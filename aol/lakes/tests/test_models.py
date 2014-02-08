import os
from django.test import TestCase
from django.contrib.gis.geos import GEOSGeometry
from django.conf import settings as SETTINGS
from ..models import NHDLake as Lake, FishingZone, County, HUC6, LakeCounty

class LakeManagerTest(TestCase):
    fixtures = ['lakes.json']

    def test_get_query_set(self):
        lake = Lake.objects.get(title="Matt Lake")
        # the lake should have a comma separated list of counties
        with self.assertNumQueries(0):
            # the ordering matters here. It's alphabetical
            self.assertTrue(lake.counties, "Clark, Washington")

    def test_search(self):
        lakes = Lake.objects.search("")[:2]
        self.assertTrue(len(lakes), 2)

    def test_important_lakes(self):
        with self.assertNumQueries(1):
            # only two important lakes are in the fixtures
            lakes = Lake.objects.important_lakes()
            self.assertTrue(len(list(lakes)), 2)

        # test things got cached
        with self.assertNumQueries(0):
            lakes = Lake.objects.important_lakes()
            self.assertTrue(len(list(lakes)), 2)


    def test_to_kml(self):
        # make sure invalid scales raise errors
        invalid_scale = 12
        self.assertRaises(ValueError, Lake.objects.to_kml, scale=invalid_scale, bbox=())

        lakes = Lake.objects.to_kml(scale=108000, bbox=(-50000, -50000, 50000, 50000))
        for lake in lakes:
            # make sure the lake has a kml attribute set
            self.assertTrue(lake.kml)


class LakeTest(TestCase):
    fixtures = ['lakes.json']

    def test_area(self):
        lake = Lake.objects.get(title="Matt Lake")
        self.assertTrue(lake.area)
        # check to make sure we cache the result
        with self.assertNumQueries(0):
            self.assertTrue(lake.area)

    def test_perimeter(self):
        lake = Lake.objects.get(title="Matt Lake")
        self.assertTrue(lake.perimeter)
        # check to make sure we cache the result
        with self.assertNumQueries(0):
            self.assertTrue(lake.perimeter)

    def test_bounding_box(self):
        lake = Lake.objects.get(title="Matt Lake")
        self.assertTrue(lake.bounding_box)
        # check to make sure we cache the result
        with self.assertNumQueries(0):
            self.assertTrue(lake.bounding_box)

    def test_counties(self):
        lake = Lake.objects.get(title="Matt Lake")
        self.assertEqual(lake.counties, "Clark, Washington")
        # check to make sure we cache the result
        with self.assertNumQueries(0):
            self.assertEqual(lake.counties, "Clark, Washington")

        # test the setter
        lake.counties = "foo"
        self.assertEqual(lake.counties, "foo")

    def test_watershed_tile_url(self):
        # just make sure the URL has a bbox set in it
        lake = Lake.objects.get(title="Matt Lake")
        url = lake.watershed_tile_url
        self.assertTrue("?bbox=-295,-295,345,340" in url)

    def test_basin_tile_url(self):
        # just make sure the URL has a bbox set in it
        lake = Lake.objects.get(title="Matt Lake")
        url = lake.basin_tile_url
        self.assertTrue("?bbox=-995,-995,1045,1040" in url)

