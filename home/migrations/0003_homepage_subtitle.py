# Generated by Django 4.2.5 on 2023-09-21 20:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0002_create_homepage"),
    ]

    operations = [
        migrations.AddField(
            model_name="homepage",
            name="subtitle",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
