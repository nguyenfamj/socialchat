# Generated by Django 4.0.5 on 2022-06-22 03:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_control', '0002_userprofile'),
    ]

    operations = [
        migrations.RenameField(
            model_name='customuser',
            old_name='emails',
            new_name='email',
        ),
    ]