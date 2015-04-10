# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import aol.photos.models


class Migration(migrations.Migration):

    dependencies = [
        ('lakes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Photo',
            fields=[
                ('photo_id', models.AutoField(primary_key=True, serialize=False)),
                ('file', models.FileField(upload_to=aol.photos.models.upload_to, db_column='filename')),
                ('taken_on', models.DateField(blank=True, db_column='photo_date', null=True)),
                ('author', models.CharField(blank=True, max_length=255)),
                ('caption', models.CharField(blank=True, max_length=255)),
                ('lake', models.ForeignKey(to='lakes.NHDLake', db_column='reachcode')),
            ],
            options={
                'db_table': 'photo',
            },
            bases=(models.Model,),
        ),
    ]
