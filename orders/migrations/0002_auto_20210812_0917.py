# Generated by Django 3.1 on 2021-08-12 08:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='emqil',
            new_name='email',
        ),
    ]
