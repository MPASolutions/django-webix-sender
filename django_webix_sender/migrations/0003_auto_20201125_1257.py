# Generated by Django 3.1.3 on 2020-11-25 12:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_webix_sender', '0002_auto_20181109_1419'),
    ]

    operations = [
        migrations.AlterField(
            model_name='messagesent',
            name='extra',
            field=models.JSONField(blank=True, null=True, verbose_name='Extra'),
        ),
    ]
