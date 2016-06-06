# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-06-04 12:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0005_log'),
    ]

    operations = [
        migrations.AddField(
            model_name='school',
            name='catalog_items_per_page',
            field=models.IntegerField(blank=100, null=100),
        ),
        migrations.AddField(
            model_name='school',
            name='catalog_show_date',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='school',
            name='catalog_show_time',
            field=models.BooleanField(default=False),
        ),
    ]