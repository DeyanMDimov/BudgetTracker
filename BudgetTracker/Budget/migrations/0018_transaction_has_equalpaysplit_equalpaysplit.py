# Generated by Django 4.1.7 on 2023-11-28 00:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Budget', '0017_alter_traveltrip_totalspent'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='has_equalPaySplit',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='equalPaySplit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('split_length_months', models.SmallIntegerField(blank=True, null=True)),
                ('transaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Budget.transaction')),
            ],
        ),
    ]
