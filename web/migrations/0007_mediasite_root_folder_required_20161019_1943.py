# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

DEFAULT = 'None'


def give_existing_records_sane_defaults(apps, schema_editor):
    # Clean up any records with blank strings. Nulls are handled by AlterField.
    school_class = apps.get_model('web', 'School')
    school_class.objects.select_for_update()\
        .filter(mediasite_root_folder='')\
        .update(mediasite_root_folder=DEFAULT)


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0006_auto_20160604_0814'),
    ]

    operations = [
        # The AlterField migration below doesn't automatically convert blank
        # strings saved in the DB to 'None' (it only handles null fields), so
        # we need to clean these fields up manually.
        migrations.RunPython(
            code=give_existing_records_sane_defaults,
            reverse_code=migrations.RunPython.noop,
        ),
        # Note there are NO defaults set in the actual model, because we don't
        # want users or code to add web_school records without specifying a
        # root folder, so this migration performs cleanup of the existing
        # records in the table to ensure there are no blank
        # mediasite_root_folder fields, without persisting a default in the
        # model itself. The user is responsible for fixing the
        # data so it makes sense (i.e. so that integrations which shouldn't be
        # using 'None' as the root folder are updated manually or removed from
        # the database entirely); the timing of this manual cleanup can be
        # independent of the actual migration.
        migrations.AlterField(
            model_name='school',
            name='mediasite_root_folder',
            field=models.TextField(
                null=False,  # do not allow empty field (DB-level constraint)
                blank=False,  # do not allow empty strings in field
                              # (Django only; not a DB-level constraint)
                default=DEFAULT),  # temporary default for migration only
            preserve_default=False  # default is not permanent in model
        ),
    ]
