# Generated by Django 2.2.16 on 2021-12-15 05:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_comment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='image',
        ),
    ]
