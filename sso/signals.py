import json
import os

from django.conf import settings
from django_cas_ng.signals import cas_user_authenticated
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile

LANG = settings.SSO_UI_ORG_DETAIL_LANG
ORG_CODE = {}
with open(settings.SSO_UI_ORG_DETAIL_FILE_PATH, "r") as ORG_CODE_FILE:
    ORG_CODE.update(json.load(ORG_CODE_FILE))


# run ketika dia berhasil login
@receiver(cas_user_authenticated)
def save_user_attributes(user, attributes, **kwargs):
    """Save user attributes from CAS into user and profile objects."""
    if not Profile.objects.filter(user=user).exists():
        org_code = attributes["kd_org"]
        record = ORG_CODE[LANG][org_code]

        # bagian ini sering ilang karena SSO nya ampas
        profile = Profile.objects.create(
            user=user,
            org_code=attributes["kd_org"],
            role=attributes["peran_user"],
            npm=attributes["npm"],
            faculty=record["faculty"],
            study_program=record["study_program"],
            educational_program=record["educational_program"],
        )

        user.profile = profile
        user.email = f"{user.username}@ui.ac.id"

        full_name = attributes["nama"]
        i = full_name.rfind(" ")
        user.first_name, user.last_name = full_name[:i], full_name[i + 1 :]

        user.save()
