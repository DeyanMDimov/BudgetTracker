# Generated by Django 4.1.7 on 2023-03-11 06:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Budget', '0009_transaction_confirmed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='notes',
            field=models.CharField(blank=True, max_length=350, null=True),
        ),
    ]
