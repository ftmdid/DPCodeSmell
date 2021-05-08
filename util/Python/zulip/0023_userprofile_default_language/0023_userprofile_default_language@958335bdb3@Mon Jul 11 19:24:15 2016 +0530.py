# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zerver', '0022_subscription_pin_to_top'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='default_language',
            field=models.CharField(default='en', max_length=50),
        ),
    ]