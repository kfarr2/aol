from shapely.geometry import asShape
from psycopg2 import extras
import datetime
import itertools
import shapefile
from django.db import connection, transaction
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from aol.lakes.models import NHDLake, LakeGeom

class Command(BaseCommand):
    args = 'shapefile.shp'
    help = 'Load a shapefile'

    def handle(self, *args, **options):
        if len(args) == 0:
            raise CommandError("Pass me the shapefile path")

        print "Assuming shapefile uses srid/epsg 4269!" 

        # read the shapefile
        sf = shapefile.Reader(args[0])

        # make the cursor work with postgres hstore fields
        cursor = connection.cursor()
        extras.register_hstore(cursor.cursor)

        with transaction.atomic():
            # we want to disable the trigger that updated the changed_on hstore
            # field, since we don't care when the NHD changes its own data
            cursor.execute("ALTER TABLE nhd DISABLE TRIGGER USER")

            # the first field is the DeleteFlg, which isn't stored in the actual
            # records, so we cut it off
            fields = sf.fields[1:] 
            # the fields *should* be labeled as such, so we use these keys to index
            # the record dictionary
            #['Permanent_', 'FDate', 'Resolution', 'GNIS_ID', 'GNIS_Name',
            # 'AreaSqKm', 'Elevation', 'ReachCode', 'FType', 'FCode', 'Shape_Leng',
            # 'Shape_Area', 'AOLReachCo', 'AOLGNIS_Na']

            # get the fields out of our model since we may not want to update
            # every one of them. We need to remove the PK though, since it
            # causes problems for Django
            relevant_fields = set(f.name for f in NHDLake._meta.fields) - set(['reachcode'])

            for shape, record in itertools.izip(sf.iterShapes(), sf.iterRecords()):
                # make it so we can index by column name instead of column position
                record = dict((field_description[0].upper(), field_value) for field_description, field_value in zip(fields, record))
                if record['REACHCODE'].strip() == "":
                    print "Skipping lake with no reachcode and permanent_id=%s" % record['PERMANENT_'].strip()

                # fetch the existing hstore for the lake, which tells us when
                # each column was modified
                cursor.execute("""SELECT changed_on FROM nhd WHERE reachcode = %s""", (record['REACHCODE'],))
                row = cursor.fetchone()
                if row is not None:
                    # remove any fields that have been modified outside of the
                    # NHD (i.e. someone edited the lake in the database
                    # manually), since we don't want overwrite those
                    modified_fields = set(row[0].keys())
                    update_fields = relevant_fields - modified_fields
                else:
                    modified_fields = set()
                    # this will cause an insert query to be performed
                    update_fields = None

                NHDLake(
                    reachcode=record['REACHCODE'].strip(),
                    permanent_id=record['PERMANENT_'].strip(),
                    fdate=datetime.date(*record['FDATE']),
                    ftype=record['FTYPE'],
                    fcode=record['FCODE'],
                    shape_length=float(record['SHAPE_LENG']),
                    shape_area=float(record['SHAPE_AREA']),
                    resolution=record['RESOLUTION'],
                    gnis_id=record['GNIS_ID'].strip(),
                    gnis_name=record['GNIS_NAME'].strip(),
                    area_sq_km=float(record['AREASQKM']),
                    elevation=float(record['ELEVATION'])
                ).save(update_fields=update_fields)

                # only change the geom if it has been changed already
                if "THE_GEOM" not in modified_fields:
                    # this stupid pyshp library has no way to spit out the wkt
                    # which is what GEOSGeometry needs, so we have to rely on
                    # another library to do the conversion
                    geom = GEOSGeometry(asShape(shape).wkt, srid=4269)
                    # cast Polygons to Multipolygons
                    if geom.geom_type == "Polygon":
                        geom = MultiPolygon(geom, srid=4269)
                    geom.transform(3644) # transform to the proper epsg code
                    # update the Geometry
                    LakeGeom(
                        reachcode_id=record['REACHCODE'].strip(),
                        the_geom=geom
                    ).save()

            cursor.execute("ALTER TABLE nhd ENABLE TRIGGER USER")
            # we only care about preserving the topology on the geom for the most zoomed in level
            cursor.execute("UPDATE lake_geom SET the_geom_27k = ST_MULTI(st_simplifypreservetopology(the_geom, 121.5))")
            cursor.execute("UPDATE  lake_geom SET the_geom_54k = ST_MULTI(st_simplify(the_geom, 242))")
            cursor.execute("UPDATE lake_geom SET the_geom_108k = ST_MULTI(st_simplify(the_geom, 610))")
            cursor.execute("UPDATE lake_geom SET the_geom_217k = ST_MULTI(st_simplify(the_geom, 1220))")
