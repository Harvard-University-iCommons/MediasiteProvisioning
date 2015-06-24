# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0002_auto_20150624_1348'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='school',
            name='canvas_mediasite_module_id',
        ),
        migrations.RemoveField(
            model_name='school',
            name='canvas_mediasite_module_item_id',
        ),
    ]
