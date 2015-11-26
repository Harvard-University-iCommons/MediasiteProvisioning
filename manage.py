#!/usr/bin/env python
import os
import sys


if __name__ == "__main__":
    if 'test' in sys.argv:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'mediasite_provisioning.settings.test'
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediasite_provisioning.settings.local')
    # os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MediasiteProvisioning.settings.local")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
