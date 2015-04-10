# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import aol.documents.models


class Migration(migrations.Migration):

    dependencies = [
        ('lakes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('document_id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('file', models.FileField(upload_to=aol.documents.models.upload_to)),
                ('rank', models.IntegerField(help_text='Defines the order in which items are listed.', verbose_name='Weight')),
                ('uploaded_on', models.DateTimeField(auto_now_add=True)),
                ('type', models.IntegerField(help_text="Map documents will appear on the 'Maps' tab on the lake page", choices=[(0, 'Other'), (1, 'Map')])),
                ('friendly_filename', models.CharField(max_length=255, help_text="When this document is downloaded, this will be the filename (if blank, it will default to the document's original filename)", blank=True)),
                ('lake', models.ForeignKey(to='lakes.NHDLake', db_column='reachcode')),
            ],
            options={
                'db_table': 'document',
                'ordering': ['rank'],
            },
            bases=(models.Model,),
        ),
    ]
