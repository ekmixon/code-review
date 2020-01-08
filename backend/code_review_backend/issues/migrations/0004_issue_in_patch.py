# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Generated by Django 2.2.8 on 2020-01-06 10:19

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("issues", "0003_diff_repository")]

    operations = [
        migrations.AddField(
            model_name="issue", name="in_patch", field=models.BooleanField(null=True)
        )
    ]