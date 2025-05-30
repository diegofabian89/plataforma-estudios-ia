# Generated by Django 5.2 on 2025-04-29 18:26

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_categoria_apunte'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='apunte',
            name='titulo',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.CreateModel(
            name='Pregunta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pregunta', models.TextField()),
                ('opcion_1', models.CharField(max_length=255)),
                ('opcion_2', models.CharField(max_length=255)),
                ('opcion_3', models.CharField(max_length=255)),
                ('opcion_4', models.CharField(max_length=255)),
                ('respuesta_correcta', models.CharField(max_length=255)),
                ('creada', models.DateTimeField(auto_now_add=True)),
                ('apunte', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='preguntas', to='core.apunte')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ResultadoTest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('puntuacion', models.IntegerField()),
                ('total_preguntas', models.IntegerField(default=15)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('apunte', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.apunte')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('usuario', 'apunte')},
            },
        ),
    ]
