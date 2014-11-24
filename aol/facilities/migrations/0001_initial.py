# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Facility',
            fields=[
                ('facility_id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=254, db_column='facilityna')),
                ('waterbody', models.CharField(max_length=254)),
                ('islake', models.IntegerField()),
                ('type', models.CharField(max_length=254)),
                ('telephone', models.CharField(max_length=254)),
                ('ramp_type', models.CharField(max_length=254, db_column='ramp_type_')),
                ('moorage', models.CharField(max_length=254)),
                ('trailer_parking', models.CharField(max_length=254, db_column='trailer_pa')),
                ('transient', models.CharField(max_length=254)),
                ('launch_fee', models.CharField(max_length=254)),
                ('restroom', models.CharField(max_length=254)),
                ('supplies', models.CharField(max_length=254)),
                ('gas_on_water', models.CharField(max_length=254, db_column='gas_on_the')),
                ('diesel_on_water', models.CharField(max_length=254, db_column='diesel_on')),
                ('fish_cleaning', models.CharField(max_length=254, db_column='fish_clean')),
                ('pumpout', models.CharField(max_length=254)),
                ('dump_station', models.CharField(max_length=254, db_column='dump_stati')),
                ('managed_by', models.CharField(max_length=254)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('boater_ser', models.CharField(max_length=254)),
                ('icon_url', models.CharField(max_length=254)),
                ('the_geom', django.contrib.gis.db.models.fields.PointField(srid=3644)),
            ],
            options={
                'db_table': 'facility',
            },
            bases=(models.Model,),
        ),
    ]
