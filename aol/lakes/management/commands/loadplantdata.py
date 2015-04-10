"""
Call this command like ./manage.py loadplantdata path/to/csv.csv

The CSV should be of the for

    WaterbodyName,ScientificName,CommonName,NativeSpecies,NoxiousWeedDesignation,ObsDate,SurveyOrg,ReachCode,Lat_DD,Lon_DD
    Timothy Lake,Potamogeton alpinus,red pondweed,1,,8/17/2004 0:00,PSUCLR,17090011000850,45.14,-121.76
    ...

The first row is assumed to be the column headers. Order of the columns doesn't matter.

The required columns are ScientificName, CommonName, NoxiousWeedDesignation,
NativeSpecies, ObsDate, and Reachcode. We always assume the plant data source
is "CLR" (other plant data comes from iMapInvasives
"""
from __future__ import print_function
import sys
from shapely.geometry import asShape
from psycopg2 import extras
import datetime
import itertools
import shapefile
import csv
from django.db import connection, transaction
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from aol.lakes.models import NHDLake, LakeGeom, LakePlant, Plant

class Command(BaseCommand):
    args = 'path/to/plant_data.csv'
    help = "Import plant data from the Rich Miller's CLR plant export CSV"

    @transaction.atomic
    def handle(self, *args, **options):
        if len(args) == 0:
            raise CommandError("Pass me the path to the plant data CSV")

        # delete all CLR lake_plant objects, since we just replace everything
        LakePlant.objects.filter(source="CLR").delete()

        with open(args[0], 'r') as csv_file:
            reader = csv.reader(csv_file)
            for i, row in enumerate(reader):
                if i == 0:
                    # the first row contains the header
                    header = row
                    continue
                # break the row into a dict based on the header
                row = dict((k, v) for k, v in zip(header, row))

                # create or update the plant 
                try:
                    plant = Plant.objects.get(normalized_name=row['ScientificName'].lower())
                except Plant.DoesNotExist:
                    plant = Plant()

                plant.name = row['ScientificName']
                plant.normalized_name = row['ScientificName'].lower()
                plant.common_name = row['CommonName']
                plant.noxious_weed_designation = row['NoxiousWeedDesignation']
                plant.is_native = row['NativeSpecies'] == "1"
                plant.save()


                # if we don't have a reachcode, there is nothing else to do
                if not row['ReachCode']:
                    continue

                try:
                    # for some reason, the reachcodes have a .0 at the end so
                    # we conver them to ints
                    row['ReachCode'] = int(float(row['ReachCode']))
                except ValueError as e:
                    pass

                try:
                    lake = NHDLake.objects.get(pk=row['ReachCode'])
                except NHDLake.DoesNotExist as e:
                    print("Lake with reachcode = %s not found" % str(row['ReachCode']), file=sys.stderr)
                    continue

                try:
                    observation_date = datetime.datetime.strptime(row['ObsDate'].split(" ")[0], "%m/%d/%Y")
                except ValueError:
                    observation_date = None

                LakePlant(
                    lake_id=row['ReachCode'],
                    plant=plant,
                    observation_date=observation_date,
                    source="CLR",
                    survey_org=row['SurveyOrg']
                ).save()

        # this causes the has_plants cached field to be updated
        NHDLake.update_cached_fields()
