from django.test import TestCase
from .models import Facility
from django.contrib.gis.geos import GEOSGeometry
from django.conf import settings as SETTINGS
from aol.lakes.models import NHDLake

class FacilityManagerTest(TestCase):
    fixtures = ['lakes.json']

    def setUp(self):
        super(FacilityManagerTest, self).setUp()
        self.f = Facility(
            name="foo",
            waterbody="foo",
            islake=0,
            type=1,
            telephone="555",
            ramp_type="asdf",
            moorage="asdf",
            trailer_parking="asdf",
            transient="asdf",
            launch_fee="asdf",
            restroom="asdf",
            supplies="asdf",
            gas_on_water="asdf",
            diesel_on_water="asdf",
            fish_cleaning="asdf",
            pumpout="asd",
            dump_station="asdf",
            managed_by="asdf",
            latitude=10.0,
            longitude=10.0,
            boater_ser="asdf",
            icon_url="asdf",
            the_geom=GEOSGeometry("Point(30 20)")
        )
        self.f.save()

    def test_to_kml(self):
        self.assertTrue(Facility.objects.to_kml(bbox=(-50000, -50000, 50000, 50000))[0].kml)

