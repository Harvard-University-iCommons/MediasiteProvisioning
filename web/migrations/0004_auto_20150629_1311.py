# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0003_auto_20150624_1410'),
    ]

    operations = [
        migrations.AddField(
            model_name='school',
            name='consumer_key',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='school',
            name='shared_secret',
            field=models.TextField(null=True, blank=True),
        ),
    ]
