# Generated by Django 5.2 on 2025-04-15 11:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PerfilUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estudio_actual', models.CharField(choices=[('primaria', 'Educación Primaria'), ('eso', 'Educación Secundaria Obligatoria (ESO)'), ('bachillerato', 'Bachillerato'), ('fp', 'Formación Profesional (FP)'), ('universidad', 'Universidad'), ('master', 'Máster o Postgrado'), ('oposiciones', 'Preparando oposiciones'), ('idiomas', 'Estudios de idiomas'), ('autoformacion', 'Autoformación / Cursos online'), ('no_estudia', 'No soy estudiante'), ('otro', 'Otro')], max_length=50)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
