# Generated by Django 4.1.7 on 2023-11-28 00:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Budget', '0018_transaction_has_equalpaysplit_equalpaysplit'),
    ]

    operations = [
        migrations.RenameField(
            model_name='equalpaysplit',
            old_name='transaction',
            new_name='transactionSplit',
        ),
    ]
