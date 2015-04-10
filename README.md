# Atlas of Oregon Lakes

## Install

    make init
    copy all the data from AOL prod to your DB


### Install notes

If you have trouble installing psycopg2, you may need to add the path to
`pg_config` to your `$PATH`. You can find the proper path by using `locate pg_config`.
On my system, this does the trick:

    export PATH=/usr/pgsql-9.3/bin:$PATH

Pillow is required, [docs here](https://github.com/python-imaging/Pillow). You
will probably need to install `libjpeg-devel` and `libtiff-devel`

Copy all the AOL pdf pages and photos to the media dir if you want some dummy data

    rsync -v USERNAME@circe.rc.pdx.edu:/vol/www/aol/dev/media/pages/* media/pages
    rsync -v USERNAME@circe.rc.pdx.edu:/vol/www/aol/dev/media/photos/* media/photos

## Notes

It's very important to create an index like this:

    CREATE INDEX observation_gist
    ON observation
    USING GIST (ST_BUFFER(ST_TRANSFORM(the_geom, 3644), 10));

This allows you to do intersection queries like:

    ST_BUFFER(ST_TRANSFORM(the_geom, 3644), 10) && (SELECT the_geom FROM lake_geom WHERE reachcode = %s)

with *very* good performance. The magic '10' is arbitrary, but you should keep
this consistent with DISTANCE_FROM_ITEM in lakes.models.

We **cannot** do this in a migration unfortunately, since the observation table is part of a different application/schema

Some custom migrations exist that add fields (like an hstore), and setup stored procs and triggers. So don't go blindly deleting them.
