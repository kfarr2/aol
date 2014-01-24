from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.gis.geos import GEOSGeometry
from aol.lakes.models import Facility, NHDLake as Lake

class HomeTest(TestCase):
    fixtures = ['lakes.json']

    def test_load(self):
        response = self.client.get(reverse("map"))
        self.assertTrue(response.status_code, 200)


class LakesTest(TestCase):
    fixtures = ['lakes.json']

    def test_load(self):
        response = self.client.get(reverse("lakes-kml")+"?bbox_limited=-50000,-50000,50000,50000&scale=54000")
        self.assertTrue(response.status_code, 200)
        self.assertIn("Matt Lake", response.content)


class FacilitiesTest(TestCase):
    fixtures = ['lakes.json']

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
            trailer_park="asdf",
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
            lake=Lake.objects.get(reachcode=123)
        )
        self.f.save()

    def test_load(self):
        response = self.client.get(reverse("facilities-kml")+"?bbox_limited=-50000,-50000,50000,50000&scale=54000")
        self.assertTrue(response.status_code, 200)
        self.assertIn("foo", response.content)


class PanelTest(TestCase):
    fixtures = ['lakes.json']

    def test_load(self):
        response = self.client.get(reverse("lakes-panel", args=(123,)))
        self.assertTrue(response.status_code, 200)


class SearchTest(TestCase):
    fixtures = ['lakes.json']

    def test_load(self):
        response = self.client.get(reverse("map-search")+"?query=matt")
        self.assertTrue(response.status_code, 200)
        # Matt lake should be in the results
        self.assertIn("Matt", response.content)
