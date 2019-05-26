# Generated by Django 2.2 on 2019-05-26 23:24

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('email', models.EmailField(max_length=255, unique=True, verbose_name='Email address')),
                ('password', models.CharField(max_length=128, verbose_name='Password')),
                ('fb_id', models.CharField(blank=True, max_length=32, null=True, unique=True, verbose_name='FB id')),
                ('first_name', models.CharField(blank=True, max_length=128, null=True, verbose_name='First name')),
                ('last_name', models.CharField(blank=True, max_length=128, null=True, verbose_name='Last name')),
                ('picture', models.ImageField(blank=True, max_length=3000, null=True, upload_to='userpics')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('is_admin', models.BooleanField(default=False, verbose_name='Admin')),
                ('is_registered', models.BooleanField(default=True, verbose_name='Registered')),
                ('last_activity_date', models.DateField(blank=True, null=True)),
                ('registration_date', models.DateField(auto_now_add=True)),
                ('timezone', models.CharField(blank=True, max_length=10)),
                ('timezone_offset', models.IntegerField(blank=True, db_index=True, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
