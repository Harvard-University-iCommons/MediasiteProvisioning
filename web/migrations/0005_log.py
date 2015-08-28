# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0004_auto_20150629_1311'),
    ]

    operations = [
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('username', models.TextField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now=True)),
                ('error', models.TextField()),
            ],
        ),
    ]
