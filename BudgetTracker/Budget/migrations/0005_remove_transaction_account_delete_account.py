# Generated by Django 4.1.7 on 2023-03-08 05:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Budget', '0004_alter_account_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='account',
        ),
        migrations.DeleteModel(
            name='account',
        ),
    ]
