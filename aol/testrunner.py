import os
from django.test.runner import DiscoverRunner

# for some tests, we need to ensure the mussels schema is created with a couple
# tables
sql = """
CREATE SCHEMA mussels;
CREATE TABLE mussels.observation
(
  waterbody_id integer,
  specie_id smallint,
  date_checked date,
  physical_description text,
  agency_id integer,
  approved boolean,
  clr_substrate_id smallint,
  user_id integer,
  observation_id serial NOT NULL
);
CREATE TABLE mussels.specie (
    specie_id integer PRIMARY KEY,
    name text
);
CREATE TABLE mussels.agency (
    agency_id integer PRIMARY KEY,
    name text
);
SELECT AddGeometryColumn('mussels', 'observation', 'the_geom', 4326, 'POINT', 2);
"""

class AOLRunner(DiscoverRunner):
    def setup_databases(self, *args, **kwargs):
        to_return = super(AOLRunner, self).setup_databases(*args, **kwargs)
        from django.db import connection
        from django.conf import settings
        cursor = connection.cursor()
        cursor.execute(sql)
        return to_return
