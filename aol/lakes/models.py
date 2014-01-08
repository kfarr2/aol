import os
import re
from django.conf import settings as SETTINGS
from django.contrib.gis.db import models
from django.db.models.sql.compiler import SQLCompiler
from PIL import Image

# This monkey patch allows us to write subqueries in the `tables` argument to the
# QuerySet.extra method. For example Foo.objects.all().extra(tables=["(SELECT * FROM Bar) t"])
# See: http://djangosnippets.org/snippets/236/#c3754
_quote_name_unless_alias = SQLCompiler.quote_name_unless_alias
SQLCompiler.quote_name_unless_alias = lambda self, name: name if name.strip().startswith('(') else _quote_name_unless_alias(self, name)

class NHDLakeManager(models.Manager):
    def get_query_set(self, *args, **kwargs):
        """
        Override the default query_set for lakes so that the fishing_zone
        and a commas separated list of counties are always attached to the Lake
        object.
        """
        qs = super(NHDLakeManager, self).get_query_set(*args, **kwargs).defer("fishing_zone__the_geom").filter(parent=None)
        # always tack on the fishing zone
        #qs = qs.select_related("fishing_zone")
        # we want to get a list of the counties each lake belongs to without
        # multiple round-trips to the DB, or Django's stupid prefetch_related
        # method. We build a little subquery, and cleverly tack it onto the
        # queryset. 
        sql = """
        (SELECT 
            lake_county.reachcode, 
            array_to_string(array_agg(county.altname ORDER BY county.altname), ', ') AS counties
        FROM lake_county INNER JOIN county USING(county_id)
        GROUP BY lake_county.reachcode
        ) counties
        """
        qs = qs.extra(
            select={"counties": "counties.counties"},
            tables=[sql],
            where=["counties.reachcode = nhd.reachcode"]
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

        return Lake.objects.all().extra(
            tables=[sql],
            select={'kml': 'st_askml(lake_geom.%s)' % (geom_col)},
            where=[
                "nhd.the_geom && st_setsrid(st_makebox2d(st_point(%s, %s), st_point(%s, %s)), 3644)",
            ],
            params=bbox
        )

class NHDLake(models.Model):
    reachcode = models.CharField(max_length=32, primary_key=True)
    title = models.CharField(max_length=255)
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
    parent = models.ForeignKey('self', null=True, db_column="parent")
    aol_page = models.IntegerField(null=True)
    body = models.TextField()

    fishing_zone = models.ForeignKey('FishingZone', null=True)
    huc6 = models.ForeignKey('HUC6', null=True)
    county_set = models.ManyToManyField('County', through="LakeCounty")
    plants = models.ManyToManyField('Plant', through="LakePlant")

    objects = NHDLakeManager()
    unfiltered = models.Manager()

    class Meta:
        db_table = 'nhd'

    def __unicode__(self):
        return self.title or self.gnis_name or self.pk

    @property
    def page_urls(self):
        """
        Returns a dict with possible keys "page", "map", "stats" and "basin",
        where the values are the URLs to the appropriate PDF page
        """
        files = ("map", "page", "survey", "stats")
        urls = {}
        for file in files:
            # construct the path to the file, and see if it exists
            path = os.path.join(SETTINGS.MEDIA_ROOT, "pages", "%d_%s.pdf" % (self.pk, file))
            if os.path.exists(path):
                urls[file] = SETTINGS.MEDIA_URL + os.path.relpath(path, SETTINGS.MEDIA_ROOT)

        return urls

    @property
    def basin_page_url(self):
        """
        Returns the URL to the AOL PDF page for the lake, or None is there is none
        """
        path = os.path.join(SETTINGS.MEDIA_ROOT, "pages", "SUP%04d" % self.page_number)
        if os.path.exists(path):
            return SETTINGS.MEDIA_URL + os.path.relpath(path, SETTINGS.MEDIA_ROOT)
        return None

    @property
    def watershed_tile_url(self):
        """
        Returns the URL to the watershed tile thumbnail from the arcgis
        server for this lake
        """
        # get the bounding box of the huc6 geom for the lake. The magic 300
        # here is from the original AOL
        results = HUC6.objects.raw("""
        SELECT st_box2d(st_envelope(st_expand(the_geom, 300))) AS bbox, huc6.huc6_id
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
        results = NHDLake.objects.raw("""
        SELECT st_box2d(st_envelope(st_expand(the_geom,1000))) as bbox, reachcode
        FROM nhd where reachcode = %s
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


class LakeGeom(models.Model):
    reachcode = models.CharField(max_length=32, primary_key=True)
    the_geom = models.MultiPolygonField(srid=3644)
    the_geom_866k = models.MultiPolygonField(srid=3644)
    the_geom_217k = models.MultiPolygonField(srid=3644)
    the_geom_108k = models.MultiPolygonField(srid=3644)
    the_geom_54k = models.MultiPolygonField(srid=3644)
    the_geom_27k = models.MultiPolygonField(srid=3644)

    objects = models.GeoManager()

    class Meta:
        db_table = "nhd"


class LakeCounty(models.Model):
    lake_county_id = models.AutoField(primary_key=True)
    lake = models.ForeignKey(NHDLake, db_column="reachcode")
    county = models.ForeignKey("County")

    class Meta:
        db_table = "lake_county"


class Document(models.Model):
    """
    Stores all the documents attached to a lake like PDFs, and whatever else an
    admin wants to upload (except Photos which are handled in their own model)
    """
    DOCUMENT_DIR = "pages/"

    document_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to=lambda instance, filename: instance.DOCUMENT_DIR + filename)
    rank = models.IntegerField(help_text="The order this field is displayed on the lakes detail page")
    uploaded_on = models.DateTimeField(auto_now_add=True)

    lake = models.ForeignKey(NHDLake, db_column="reachcode")

    class Meta:
        db_table = 'document'
        ordering = ['rank']


class Photo(models.Model):
    """Stores all the photos attached to a lake"""
    PHOTO_DIR = "photos/"
    THUMBNAIL_PREFIX = "thumbnail-"

    photo_id = models.AutoField(primary_key=True)
    file = models.FileField(upload_to=lambda instance, filename: instance.PHOTO_DIR + filename, db_column="filename")
    taken_on = models.DateField(null=True, db_column="photo_date")
    author = models.CharField(max_length=255)
    caption = models.CharField(max_length=255)

    lake = models.ForeignKey(NHDLake, db_column="reachcode")

    class Meta:
        db_table = "photo"

    @property
    def url(self):
        """Returns the complete path to the photo from MEDIA_URL"""
        return self.file.url

    @property
    def thumbnail_url(self):
        """Returns the complete path to the photo's thumbnail from MEDIA_URL"""
        return SETTINGS.MEDIA_URL + os.path.relpath(self._thumbnail_path, SETTINGS.MEDIA_ROOT)

    @property
    def _thumbnail_path(self):
        """Returns the abspath to the thumbnail file, and generates it if needed"""
        filename = self.THUMBNAIL_PREFIX + os.path.basename(self.file.name)
        path = os.path.join(os.path.dirname(self.file.path), filename)
        try:
            open(path).close()
        except IOError:
            self._generate_thumbnail(path)

        return path

    def _generate_thumbnail(self, save_to_location):
        """Generates a thumbnail and saves to to the save_to_location"""
        SIZE = (400, 300)
        im = Image.open(self.file.path)
        im.thumbnail(SIZE, Image.ANTIALIAS)
        im.save(save_to_location)


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
    plant_id = models.AutoField(primary_key=True) # Primary key for a plant row
    name = models.CharField(max_length=255) # Scientific name of a plant
    common_name = models.CharField(max_length=255) # Common name of the plant
    former_name = models.CharField(max_length=255) # Former name of the plant
    plant_family = models.CharField(max_length=255) # The family name that the plant belongs to

    class Meta:
        db_table = "plant"
    
    def __unicode__(self):
        return self.name


class LakePlant(models.Model):
    lake_plant_id = models.AutoField(primary_key=True)
    lake = models.ForeignKey(NHDLake, db_column="reachcode")
    plant = models.ForeignKey("Plant")

    class Meta:
        db_table = "lake_plant"


class FacilityManager(models.Manager):
    def to_kml(self, bbox):
        return Facility.objects.all().extra(
            select={'kml': 'st_askml(the_geom)'},
            where=[
                "the_geom && st_setsrid(st_makebox2d(st_point(%s, %s), st_point(%s, %s)), 3644)",
            ],
            params=bbox
        )


class Facility(models.Model):
    facility_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=254, db_column="facilityna")
    waterbody = models.CharField(max_length=254)
    islake = models.IntegerField()
    type = models.CharField(max_length=254)
    telephone = models.CharField(max_length=254) 
    ramp_type = models.CharField(max_length=254, db_column="ramp_type_")
    moorage = models.CharField(max_length=254) 
    trailer_park = models.CharField(max_length=254, db_column="trailer_pa")
    transient = models.CharField(max_length=254)
    launch_fee = models.CharField(max_length=254)
    restroom = models.CharField(max_length=254)
    supplies = models.CharField(max_length=254)
    gas_on_water = models.CharField(max_length=254, db_column="gas_on_the")
    diesel_on_water = models.CharField(max_length=254, db_column="diesel_on") 
    fish_cleaning = models.CharField(max_length=254, db_column="fish_clean")
    pumpout = models.CharField(max_length=254)
    dump_station = models.CharField(max_length=254, db_column="dump_stati")
    managed_by = models.CharField(max_length=254)
    latitude = models.FloatField() 
    longitude = models.FloatField()
    boater_ser = models.CharField(max_length=254)
    icon_url = models.CharField(max_length=254)
    the_geom = models.PointField(srid=3644)

    lake = models.ForeignKey(NHDLake, db_column="reachcode")
    objects = FacilityManager()

    class Meta:
        db_table = "facility"
