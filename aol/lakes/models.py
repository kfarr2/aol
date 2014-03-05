import string
import requests
import os
import re
from django.conf import settings as SETTINGS
from django.contrib.gis.db import models
from django.db.models import Q
from django.db.models.sql.compiler import SQLCompiler
from django.db import connections, transaction, connection
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.core.cache import cache
from django.contrib.gis.geos import Point

# This monkey patch allows us to write subqueries in the `tables` argument to the
# QuerySet.extra method. For example Foo.objects.all().extra(tables=["(SELECT * FROM Bar) t"])
# See: http://djangosnippets.org/snippets/236/#c3754
_quote_name_unless_alias = SQLCompiler.quote_name_unless_alias
SQLCompiler.quote_name_unless_alias = lambda self, name: name if name.strip().startswith('(') else _quote_name_unless_alias(self, name)

def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]

class NHDLakeManager(models.Manager):
    def get_query_set(self):
        """
        We only want to return lakes that are coded as LakePond or Reservoir
        which have the types 390, 436 in the NHD. See
        http://nhd.usgs.gov/NHDv2.0_poster_6_2_2010.pdf

        We also only want to get lakes in oregon
        """
        qs = super(NHDLakeManager, self).get_query_set().filter(
            ftype__in=[390, 436],
            parent=None,
            is_in_oregon=True
        )
        qs = qs.prefetch_related("county_set")
        qs = qs.extra(
            select={"is_important": "has_mussels OR has_docs OR has_photos OR has_plants OR (aol_page IS NOT NULL)"},
            order_by=['-is_important'],
        )
        return qs

    def search(self, query):
        """
        This searches all the NHDLake objects with a gnis_name, title, gnis_id
        or reachcode containing the particular query keyword
        """
        qs = NHDLake.objects.filter(Q(gnis_name__icontains=query) | Q(title__icontains=query) | Q(gnis_id__icontains=query) | Q(reachcode__icontains=query))
        qs = qs.extra(
            tables=["(SELECT reachcode, the_geom FROM lake_geom) AS lake_geom"],
            select={"lake_area": "ST_AREA(lake_geom.the_geom)"}, 
            order_by=["-lake_area"],
            where=["lake_geom.reachcode = nhd.reachcode"]
        )
        return qs

    def by_letter(self, letter):
        """Return a queryset of all the lakes that start with the letter"""
        letter = letter.lower()
        qs = self.all().extra(
            select={"alphabetic_title": "regexp_replace(COALESCE(NULLIF(title, ''), gnis_name), '^[lL]ake\s*', '')"},
            where=["(lower(COALESCE(NULLIF(title, ''), gnis_name)) LIKE %s OR lower(regexp_replace(COALESCE(NULLIF(title, ''), gnis_name), '^[lL]ake\s*', '')) LIKE %s )"],
            params=(letter + "%",)*2,
            # we want to list important lakes first, and then sort by the alphabetic title
            order_by=['-is_important', "alphabetic_title"],
        )
        return qs

    def to_kml(self, scale, bbox):
        """
        Returns a query set of Lake objects with a "kml" attribute, which
        contains the KML string representing the lake geometry at the specific
        scale. Only lakes within the bbox (a 4-tuple of floats) are returned
        """
        if scale in [1728004, 864002, 432001]:
            geom_col = "the_geom_217k"
        elif scale in [216001]:
            geom_col = "the_geom_108k"
        elif scale in [108000]:
            geom_col = "the_geom_54k"
        elif scale in [54000, 27000, 13500, 6750]:
            geom_col = "the_geom_27k"
        else:
            raise ValueError("scale not valid")

        qs = self.all().extra(
            select={'kml': 'st_askml(lake_geom.%s)' % (geom_col)},
            tables=["(SELECT * FROM lake_geom) AS lake_geom"],
            where=[
                "lake_geom.reachcode = nhd.reachcode",
                "lake_geom.the_geom && st_setsrid(st_makebox2d(st_point(%s, %s), st_point(%s, %s)), 3644)",
                "ST_AREA(lake_geom.%s) > 0" % geom_col
            ],
            params=bbox
        )

        return qs


class NHDLake(models.Model):
    reachcode = models.CharField(max_length=32, primary_key=True)
    title = models.CharField(max_length=255, blank=True)
    permanent_id = models.CharField(max_length=64)
    fdate = models.DateField()
    ftype = models.IntegerField()
    fcode = models.IntegerField()
    shape_length = models.FloatField()
    shape_area = models.FloatField()
    resolution = models.IntegerField()
    gnis_id = models.CharField(max_length=32)
    gnis_name = models.CharField(max_length=255)
    area_sq_km = models.FloatField()
    elevation = models.FloatField()
    parent = models.ForeignKey('self', null=True, db_column="parent", blank=True)
    aol_page = models.IntegerField(null=True, blank=True)
    body = models.TextField()

    fishing_zone = models.ForeignKey('FishingZone', null=True)
    huc6 = models.ForeignKey('HUC6', null=True, blank=True)
    county_set = models.ManyToManyField('County', through="LakeCounty")
    plants = models.ManyToManyField('Plant', through="LakePlant")

    # denormalized fields
    # unfortunately, for performance reasons, we need to cache whether a lake
    # has plant data, has mussels, was in the original AOL, has docs, has
    # photos etc
    has_mussels = models.BooleanField(default=False, blank=True)
    has_plants = models.BooleanField(default=False, blank=True)
    has_docs = models.BooleanField(default=False, blank=True)
    has_photos = models.BooleanField(default=False, blank=True)
    # some lakes in the NHD are not in oregon, so we cache this value so we
    # don't have to join on the lake_county table
    is_in_oregon = models.BooleanField(default=False, blank=True)

    objects = NHDLakeManager()
    unfiltered = models.Manager()

    class Meta:
        db_table = 'nhd'

    def __unicode__(self):
        return self.title or self.gnis_name or self.pk

    @classmethod
    def update_cached_fields(cls):
        """
        Important lakes are lakes with plant data, mussel data, photos docs, etc.
        We cache these booleans (has_mussels, has_plants, etc) on the model
        itself for performance reasons, so this class method needs to be called
        to refresh thos booleans.

        It also refreshes the is_in_oregon flag
        """
        cursor = connection.cursor()
        results = cursor.execute("""
            SELECT 
                reachcode, 
                MAX(has_plants) AS has_plants, 
                MAX(has_docs) AS has_docs, 
                MAX(has_photos) AS has_photos, 
                MAX(has_aol_page) AS has_aol_page,
                MAX(has_mussels) AS has_mussels
            FROM (
                -- get all reachcodes for lakes with plants
                SELECT reachcode, 1 AS has_plants, 0 AS has_docs, 0 AS has_photos, 0 AS has_aol_page, 0 AS has_mussels FROM "lake_plant" GROUP BY reachcode HAVING COUNT(*) >= 1
                UNION
                -- get all reachcodes for lakes with documents
                SELECT reachcode, 0 AS has_plants, 1 AS has_docs, 0 AS has_photos, 0 AS has_aol_page, 0 AS has_mussels FROM "document" GROUP BY reachcode HAVING COUNT(*) >= 1
                UNION
                -- get all reachcodes for lakes with photos
                SELECT reachcode, 0 AS has_plants, 0 AS has_docs, 1 AS has_photos, 0 AS has_aol_page, 0 AS has_mussels FROM "photo" GROUP BY reachcode HAVING COUNT(*) >= 1
                UNION
                -- get all original AOL lakes
                SELECT reachcode, 0 AS has_plants, 0 AS has_docs, 0 AS has_photos, 1 AS has_aol_page, 0 AS has_mussels FROM "nhd" WHERE aol_page IS NOT NULL
                UNION
                SELECT DISTINCT reachcode, 0 AS has_plants, 0 AS has_docs, 0 AS has_photos, 0 AS has_aol_page, 1 AS has_mussels FROM "display_view" INNER JOIN "lake_geom" ON ST_DWITHIN(ST_TRANSFORM(display_view.the_geom, 3644), lake_geom.the_geom, 10)
            ) k
            GROUP BY reachcode
        """)
        for row in dictfetchall(cursor):
            NHDLake.unfiltered.filter(reachcode=row['reachcode']).update(
                has_plants=row['has_plants'],
                has_docs=row['has_docs'],
                has_photos=row['has_photos'],
                has_mussels=row['has_mussels']
            )

        # now update the is_in_oregon flag
        cursor.execute("""
            WITH foo AS (SELECT COUNT(*) AS the_count, reachcode FROM lake_county GROUP BY reachcode)
            UPDATE nhd SET is_in_oregon = foo.the_count > 0 FROM foo WHERE foo.reachcode = nhd.reachcode
        """)

    @property
    def area(self):
        """Returns the number of acres this lake is"""
        if not hasattr(self, "_area"):
            cursor = connections['default'].cursor()
            # 43560 is the number of square feet in an arre
            cursor.execute("SELECT ST_AREA(the_geom)/43560 FROM lake_geom WHERE reachcode = %s", (self.reachcode,))
            self._area = cursor.fetchone()[0]
        return self._area

    @property
    def perimeter(self):
        """Returns the number of acres this lake is"""
        if not hasattr(self, "_perimeter"):
            cursor = connections['default'].cursor()
            # 5280 is the number of feet in a mile
            cursor.execute("SELECT ST_PERIMETER(the_geom)/5280 FROM lake_geom WHERE reachcode = %s", (self.reachcode,))
            self._perimeter = cursor.fetchone()[0]
        return self._perimeter

    @property
    def bounding_box(self):
        if not hasattr(self, "_bbox"):
            lakes = LakeGeom.objects.raw("""SELECT reachcode, Box2D(ST_Envelope(st_expand(the_geom,1000))) as coords from lake_geom WHERE reachcode = %s""", (self.pk,))
            lake = list(lakes)[0]
            self._bbox = re.sub(r'[^0-9.-]', " ", lake.coords).split()
        return self._bbox

    @property
    def counties(self):
        """Return a nice comma separated list of the counties this lake belongs to"""
        if not hasattr(self, "_counties"):
            self._counties = ",".join(c.name for c in self.county_set.all())
        return self._counties

    @counties.setter
    def counties(self, value):
        """
        We need a setter since the raw query we perform in the manager class
        generates the comma separated list of counties in the query itself
        """
        self._counties = value

    @property
    def watershed_tile_url(self):
        """
        Returns the URL to the watershed tile thumbnail from the arcgis
        server for this lake
        """
        # get the bounding box of the huc6 geom for the lake. The magic 300
        # here is from the original AOL
        results = HUC6.objects.raw("""
        SELECT Box2D(st_envelope(st_expand(the_geom, 300))) AS bbox, huc6.huc6_id
        FROM huc6 WHERE huc6.huc6_id = %s
        """, (self.huc6_id,))

        try:
            bbox = list(results)[0].bbox
        except IndexError:
            # this lake does not have a watershed
            return None 

        return self._bbox_thumbnail_url(bbox)

    @property
    def basin_tile_url(self):
        """
        Return the URL to the lakebasin tile thumbnail from the arcgis server
        """
        # the magic 1000 here is from the original AOL too 
        results = LakeGeom.objects.raw("""
        SELECT Box2D(st_envelope(st_expand(the_geom,1000))) as bbox, reachcode
        FROM lake_geom where reachcode = %s
        """, (self.pk,))

        bbox = results[0].bbox
        return self._bbox_thumbnail_url(bbox)

    def _bbox_thumbnail_url(self, bbox):
        """
        Take a boundingbox string from postgis, for example:
        BOX(727773.25 1372170,829042.75 1430280.75)
        and build the URL to a tile of that bounding box in the arcgis server
        """
        # extract out the numbers from the bbox, and comma separate them
        bbox = re.sub(r'[^0-9.-]', " ", bbox).split()
        bbox = ",".join(bbox)
        path = "export?bbox=%s&bboxSR=&layers=&layerdefs=&size=&imageSR=&format=jpg&transparent=false&dpi=&time=&layerTimeOptions=&f=image"
        return SETTINGS.TILE_URL + (path % bbox)

    @property
    def mussels(self):
        """
        This queries the mussel DB for any mussels that are within a certain
        distance of this lake. It returns a comma separated string of the
        status of the mussels
        """
        if not hasattr(self, "_mussels"):
            distance = 10 # in meters since the 3644 projection is in meters
            cursor = connection.cursor()
            cursor.execute("""
                SELECT 
                    DISTINCT
                    status as species,
                    date_checked,
                    agency
                FROM 
                    display_view 
                WHERE 
                    ST_DWITHIN(ST_TRANSFORM(the_geom, 3644), (SELECT the_geom FROM lake_geom WHERE reachcode = %s), %s)
                ORDER BY date_checked
            """, (self.pk, distance))
            results = []
            for row in cursor:
                results.append({
                    "species": row[0],
                    "date_checked": row[1],
                    "source": row[2]
                })
            self._mussels = results

        return self._mussels


class LakeGeom(models.Model):
    reachcode = models.OneToOneField(NHDLake, primary_key=True, db_column="reachcode")
    the_geom = models.MultiPolygonField(srid=3644)
    the_geom_866k = models.MultiPolygonField(srid=3644)
    the_geom_217k = models.MultiPolygonField(srid=3644)
    the_geom_108k = models.MultiPolygonField(srid=3644)
    the_geom_54k = models.MultiPolygonField(srid=3644)
    the_geom_27k = models.MultiPolygonField(srid=3644)

    objects = models.GeoManager()

    class Meta:
        db_table = "lake_geom"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            instance = super(LakeGeom, self).save(*args, **kwargs)
            cursor = connection.cursor()
            # update the fishing zone
            cursor.execute("""
                UPDATE 
                    nhd 
                SET 
                    fishing_zone_id = (SELECT fishing_zone_id FROM fishing_zone WHERE ST_Intersects(fishing_zone.the_geom, nhd.the_geom) LIMIT 1)
                WHERE 
                    nhd.reachcode = %s
                """, (self.pk,))
            # update the huc6
            cursor.execute("""
                WITH foo AS (
                    SELECT 
                        huc6.huc6_id, 
                        reachcode 
                    FROM 
                        lake_geom 
                    INNER JOIN 
                        huc6 ON ST_Covers(huc6.the_geom, lake_geom.the_geom)
                    WHERE reachcode = %s
                )
                UPDATE 
                    nhd 
                SET 
                    huc6_id = foo.huc6_id 
                FROM 
                    foo 
                WHERE 
                    nhd.reachcode = foo.reachcode
            """, (self.pk,))

            # update counties
            cursor.execute("""DELETE FROM lake_county WHERE reachcode = %s""", (self.pk,))
            cursor.execute("""
                INSERT INTO lake_county (county_id, reachcode) (
                    SELECT
                        county_id, lake_geom.reachcode
                    FROM
                       county
                    INNER JOIN 
                        lake_geom ON ST_INTERSECTS(county.the_geom, lake_geom.the_geom)
                    WHERE reachcode = %s
                )
            """, (self.pk,))

        return instance


class LakeCounty(models.Model):
    lake_county_id = models.AutoField(primary_key=True)
    lake = models.ForeignKey(NHDLake, db_column="reachcode")
    county = models.ForeignKey("County")

    class Meta:
        db_table = "lake_county"


class DeferGeomManager(models.Manager):
    """
    Models that use this manager will always defer the "the_geom" column. This
    is necessary because the geom columns are huge, and rarely need to be
    accessed.
    """
    def get_query_set(self, *args, **kwargs):
        qs = super(DeferGeomManager, self).get_query_set(*args, **kwargs).defer("the_geom")
        return qs


class FishingZone(models.Model):
    fishing_zone_id = models.AutoField(primary_key=True)
    odfw = models.CharField(max_length=255)
    the_geom = models.MultiPolygonField(srid=3644)

    objects = DeferGeomManager()

    class Meta:
        db_table = "fishing_zone"

    def __unicode__(self):
        return self.odfw


class HUC6(models.Model): 
    huc6_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, db_column="hu_12_name")
    the_geom = models.MultiPolygonField(srid=3644)

    objects = DeferGeomManager()

    class Meta:
        db_table = "huc6"

    def __unicode__(self):
        return self.name


class County(models.Model):
    county_id = models.AutoField(primary_key=True)
    name = models.CharField(db_column="altname", max_length=255)
    # includes the "County" suffix
    full_name = models.CharField(db_column="instname", max_length=255)
    the_geom = models.MultiPolygonField(srid=3644)

    objects = DeferGeomManager()

    class Meta:
        db_table = "county"
        ordering = ["name"]

    def __unicode__(self):
        return self.full_name


class Plant(models.Model):
    plant_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    # the name of the plant in lower case
    normalized_name = models.CharField(max_length=255, unique=True)
    common_name = models.CharField(max_length=255) # Common name of the plant
    noxious_weed_designation = models.CharField(max_length=255, default="", choices=(
        ("", ""),
        ("A", "ODA Class A"),
        ("B", "ODA Class B"),
        ("Federal", "Federal"),
    ))
    is_native = models.NullBooleanField(default=None, choices=(
        (True, "Native"),
        (False, "Non-native"),
        (None, ""),
    ))

    class Meta:
        db_table = "plant"
    
    def __unicode__(self):
        return self.name


class LakePlant(models.Model):
    lake_plant_id = models.AutoField(primary_key=True)
    lake = models.ForeignKey(NHDLake, db_column="reachcode")
    plant = models.ForeignKey("Plant", related_name="plant_set")
    observation_date = models.DateField(null=True)
    source = models.CharField(max_length=255, default="", choices=(
        ("", ""),
        ("CLR", "Center for Lakes and Reservoir"),
        ("IMAP", "iMapInvasives"),
    ))
    survey_org = models.CharField(max_length=255)

    class Meta:
        db_table = "lake_plant"
        ordering = ['-observation_date']

    def source_link(self):
        return {
            "CLR": "http://www.clr.pdx.edu/",
            "IMAP": "http://www.imapinvasives.org",
        }.get(self.source, '#')


