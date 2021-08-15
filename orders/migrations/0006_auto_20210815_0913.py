# Generated by Django 3.1 on 2021-08-15 08:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_variation'),
        ('orders', '0005_auto_20210815_0909'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderproduct',
            name='variation',
        ),
        migrations.AddField(
            model_name='orderproduct',
            name='variation',
            field=models.ManyToManyField(blank=True, to='store.Variation'),
        ),
    ]
