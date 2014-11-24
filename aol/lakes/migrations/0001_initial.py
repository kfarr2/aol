# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='County',
            fields=[
                ('county_id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(db_column='altname', max_length=255)),
                ('full_name', models.CharField(db_column='instname', max_length=255)),
                ('the_geom', django.contrib.gis.db.models.fields.MultiPolygonField(srid=3644)),
            ],
            options={
                'db_table': 'county',
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FishingZone',
            fields=[
                ('fishing_zone_id', models.AutoField(serialize=False, primary_key=True)),
                ('odfw', models.CharField(max_length=255)),
                ('the_geom', django.contrib.gis.db.models.fields.MultiPolygonField(srid=3644)),
            ],
            options={
                'db_table': 'fishing_zone',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HUC6',
            fields=[
                ('huc6_id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(db_column='hu_12_name', max_length=255)),
                ('the_geom', django.contrib.gis.db.models.fields.MultiPolygonField(srid=3644)),
            ],
            options={
                'db_table': 'huc6',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LakeCounty',
            fields=[
                ('lake_county_id', models.AutoField(serialize=False, primary_key=True)),
                ('county', models.ForeignKey(to='lakes.County')),
            ],
            options={
                'db_table': 'lake_county',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LakePlant',
            fields=[
                ('lake_plant_id', models.AutoField(serialize=False, primary_key=True)),
                ('observation_date', models.DateField(null=True)),
                ('source', models.CharField(choices=[('', ''), ('CLR', 'Center for Lakes and Reservoir'), ('IMAP', 'iMapInvasives')], max_length=255, default='')),
                ('survey_org', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'lake_plant',
                'ordering': ['-observation_date'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NHDLake',
            fields=[
                ('reachcode', models.CharField(primary_key=True, serialize=False, max_length=32)),
                ('title', models.CharField(max_length=255, blank=True)),
                ('permanent_id', models.CharField(max_length=64)),
                ('fdate', models.DateField()),
                ('ftype', models.IntegerField()),
                ('fcode', models.IntegerField()),
                ('shape_length', models.FloatField()),
                ('shape_area', models.FloatField()),
                ('resolution', models.IntegerField()),
                ('gnis_id', models.CharField(max_length=32)),
                ('gnis_name', models.CharField(max_length=255)),
                ('area_sq_km', models.FloatField()),
                ('elevation', models.FloatField()),
                ('aol_page', models.IntegerField(null=True, blank=True)),
                ('body', models.TextField()),
                ('has_mussels', models.BooleanField(default=False)),
                ('has_plants', models.BooleanField(default=False)),
                ('has_docs', models.BooleanField(default=False)),
                ('has_photos', models.BooleanField(default=False)),
                ('is_in_oregon', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'nhd',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LakeGeom',
            fields=[
                ('reachcode', models.OneToOneField(db_column='reachcode', serialize=False, primary_key=True, to='lakes.NHDLake')),
                ('the_geom', django.contrib.gis.db.models.fields.MultiPolygonField(srid=3644)),
                ('the_geom_866k', django.contrib.gis.db.models.fields.MultiPolygonField(srid=3644)),
                ('the_geom_217k', django.contrib.gis.db.models.fields.MultiPolygonField(srid=3644)),
                ('the_geom_108k', django.contrib.gis.db.models.fields.MultiPolygonField(srid=3644)),
                ('the_geom_54k', django.contrib.gis.db.models.fields.MultiPolygonField(srid=3644)),
                ('the_geom_27k', django.contrib.gis.db.models.fields.MultiPolygonField(srid=3644)),
            ],
            options={
                'db_table': 'lake_geom',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Plant',
            fields=[
                ('plant_id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('normalized_name', models.CharField(unique=True, max_length=255)),
                ('common_name', models.CharField(max_length=255)),
                ('noxious_weed_designation', models.CharField(choices=[('', ''), ('A', 'ODA Class A'), ('B', 'ODA Class B'), ('Federal', 'Federal')], max_length=255, default='')),
                ('is_native', models.NullBooleanField(choices=[(True, 'Native'), (False, 'Non-native'), (None, '')], default=None)),
            ],
            options={
                'db_table': 'plant',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='nhdlake',
            name='county_set',
            field=models.ManyToManyField(through='lakes.LakeCounty', to='lakes.County'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='nhdlake',
            name='fishing_zone',
            field=models.ForeignKey(null=True, to='lakes.FishingZone'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='nhdlake',
            name='huc6',
            field=models.ForeignKey(null=True, blank=True, to='lakes.HUC6'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='nhdlake',
            name='parent',
            field=models.ForeignKey(null=True, db_column='parent', blank=True, to='lakes.NHDLake'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='nhdlake',
            name='plants',
            field=models.ManyToManyField(through='lakes.LakePlant', to='lakes.Plant'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='lakeplant',
            name='lake',
            field=models.ForeignKey(db_column='reachcode', to='lakes.NHDLake'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='lakeplant',
            name='plant',
            field=models.ForeignKey(related_name='plant_set', to='lakes.Plant'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='lakecounty',
            name='lake',
            field=models.ForeignKey(db_column='reachcode', to='lakes.NHDLake'),
            preserve_default=True,
        ),
    ]
