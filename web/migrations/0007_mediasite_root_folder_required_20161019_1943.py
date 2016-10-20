# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0006_auto_20160604_0814'),
    ]

    operations = [
        # Note there are NO defaults set, so manual cleanup of the existing
        # records in the table must be performed to remove any records with
        # blank mediasite_root_folder fields; otherwise this migration will
        # fail with a django.db.utils.IntegrityError.
        migrations.AlterField(
            model_name='school',
            name='mediasite_root_folder',
            field=models.TextField(),
        ),
    ]
