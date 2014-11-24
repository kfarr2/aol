from unittest.mock import Mock, patch
from model_mommy.mommy import make
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.gis.geos import GEOSGeometry
from aol.lakes.models import NHDLake, LakeGeom
from aol.facilities.models import Facility

class HomeTest(TestCase):
    def test_load(self):
        response = self.client.get(reverse("map"))
        self.assertTrue(response.status_code, 200)


class LakesTest(TestCase):
    def test_load(self):
        with patch("aol.lakes.models.NHDLake.objects.to_kml", lambda *args, **kwargs: [Mock(title="Matt Lake")]):
            response = self.client.get(reverse("lakes-kml")+"?bbox_limited=-50000,-50000,50000,50000&scale=54000")
            self.assertTrue(response.status_code, 200)
            self.assertIn("Matt Lake", response.content.decode("utf8"))


class FacilitiesTest(TestCase):
    def setUp(self):
        super(FacilitiesTest, self).setUp()
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
            the_geom=GEOSGeometry("Point(30 20)"),
        )
        self.f.save()

    def test_load(self):
        response = self.client.get(reverse("facilities-kml")+"?bbox_limited=-50000,-50000,50000,50000&scale=54000")
        self.assertTrue(response.status_code, 200)
        self.assertIn("foo", response.content.decode("utf8"))


class PanelTest(TestCase):
    def test_load(self):
        lake = make(NHDLake, title="Matt Lake", ftype=390, is_in_oregon=True)
        make(LakeGeom, reachcode=lake)
        response = self.client.get(reverse("lakes-panel", args=(lake.pk,)))
        self.assertTrue(response.status_code, 200)


class SearchTest(TestCase):
    def test_load(self):
        lake = make(NHDLake, title="Matt Lake", ftype=390, is_in_oregon=True)
        make(LakeGeom, reachcode=lake)
        response = self.client.get(reverse("map-search")+"?query=matt")
        self.assertTrue(response.status_code, 200)
        # Matt lake should be in the results
        self.assertIn("Matt", response.content.decode())
