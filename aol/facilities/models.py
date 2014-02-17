import requests
from django.contrib.gis.db import models
from django.db import connections, transaction, connection
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib.gis.geos import Point

class FacilityManager(models.Manager):
    def to_kml(self, bbox):
        return Facility.objects.all().extra(
            select={'kml': 'st_askml(the_geom)'},
            where=[
                "the_geom && st_setsrid(st_makebox2d(st_point(%s, %s), st_point(%s, %s)), 3644)",
            ],
            params=bbox
        )

    def reimport(self):
        """
        Connects to the Oregon facility JSON endpoint and reimports all the
        facilities
        """
        response = requests.get("https://data.oregon.gov/resource/spxe-q5vj.json")
        js = response.json()
        # the data source uses WGS84 coords, so we have to transform them
        gcoord = SpatialReference(4326)
        mycoord = SpatialReference(3644)
        trans = CoordTransform(gcoord, mycoord)
        with transaction.atomic():
            # wipe out the existing facilties
            Facility.objects.all().delete()
            for row in js:
                try:
                    p = Point(float(row['location']['longitude']), float(row['location']['latitude']), srid=4326)
                except KeyError:
                    continue
                p.transform(trans)

                f = Facility(
                    name=row['boating_facility_name'],
                    managed_by=row.get('managed_by', ''),
                    telephone=row.get('telephone', {}).get('phone_number', ''),
                    ramp_type=row.get('ramp_type_lanes', ''),
                    trailer_parking=row.get('trailer_parking', ''),
                    moorage=row.get('moorage', ''),
                    launch_fee=row.get('launch_fee', ''),
                    restroom=row.get('restroom', ''),
                    supplies=row.get('supplies', ''),
                    gas_on_water=row.get('gas_on_the_water', ''),
                    diesel_on_water=row.get('diesel_on_the_water', ''),
                    waterbody=row.get('waterbody', ''),
                    fish_cleaning=row.get('fish_cleaning_station', ''),
                    pumpout=row.get('pumpout', ''),
                    dump_station=row.get('dump_station', ''),
                    the_geom=p,
                    icon_url=row.get('boater_services', ''),
                )
                f.save()


class Facility(models.Model):
    facility_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=254, db_column="facilityna")
    waterbody = models.CharField(max_length=254)
    islake = models.IntegerField()
    type = models.CharField(max_length=254)
    telephone = models.CharField(max_length=254) 
    ramp_type = models.CharField(max_length=254, db_column="ramp_type_")
    moorage = models.CharField(max_length=254) 
    trailer_parking = models.CharField(max_length=254, db_column="trailer_pa")
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

    objects = FacilityManager()

    class Meta:
        db_table = "facility"

