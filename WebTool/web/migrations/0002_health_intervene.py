# Generated by Django 2.1.2 on 2018-12-23 10:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Intervene',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('StuName', models.TextField()),
                ('StuID', models.CharField(max_length=20)),
                ('School', models.TextField()),
                ('Major', models.TextField()),
                ('Grade', models.CharField(max_length=5)),
                ('Class', models.CharField(max_length=15)),
                ('Status', models.TextField()),
                ('Guidance', models.TextField()),
                ('Type', models.CharField(max_length=5)),
                ('Time', models.CharField(max_length=15)),
            ],
        ),
    ]
