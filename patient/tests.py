import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "checkup_backend.settings")
import django

django.setup()

from patient.models import *

