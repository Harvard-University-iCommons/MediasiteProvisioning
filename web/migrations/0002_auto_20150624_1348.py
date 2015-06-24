# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('web', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='APIUser',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('canvas_api_key', models.TextField()),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='school',
            name='canvas_mediasite_module_id',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='school',
            name='canvas_mediasite_module_item_id',
            field=models.TextField(null=True, blank=True),
        ),
    ]
