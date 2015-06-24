# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='School',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('canvas_id', models.TextField()),
                ('name', models.TextField()),
                ('mediasite_root_folder', models.TextField(blank=True, null=True)),
            ],
        ),
    ]
