from django.contrib.auth.models import User
from django.db import models


class PerfilUsuario(models.Model):
    ESTUDIOS = [
        ('primaria', 'Educación Primaria'),
        ('eso', 'Educación Secundaria Obligatoria (ESO)'),
        ('bachillerato', 'Bachillerato'),
        ('fp', 'Formación Profesional (FP)'),
        ('universidad', 'Universidad'),
        ('master', 'Máster o Postgrado'),
        ('oposiciones', 'Preparando oposiciones'),
        ('idiomas', 'Estudios de idiomas'),
        ('autoformacion', 'Autoformación / Cursos online'),
        ('no_estudia', 'No soy estudiante'),
        ('otro', 'Otro'),
    ]

    AVATAR_CHOICES = [
        ('avatar_male.png', 'Avatar masculino'),
        ('avatar_female.png', 'Avatar femenino'),
        ('avatar_old.png', 'Avatar anciano'),
        ('avatar_child.png', 'Avatar infantil'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    estudio_actual = models.CharField(max_length=50, choices=ESTUDIOS)
    imagen = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    avatar_default = models.CharField(
        max_length=100,
        choices=AVATAR_CHOICES,
        blank=True,
        null=True,
        help_text="Puedes elegir un avatar predeterminado si no deseas subir una imagen propia."
    )

    def __str__(self):
        return f"{self.user.username} - {self.estudio_actual}"

    def get_avatar_url(self):
        if self.imagen:
            return self.imagen.url
        elif self.avatar_default:
            return f"/static/img/avatars/{self.avatar_default}"
        else:
            return "/static/img/avatar_default.png"  # avatar por defecto si no hay nada


class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Apunte(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200, null=True)
    archivo = models.FileField(upload_to='apuntes/', blank=True, null=True)
    texto = models.TextField(blank=True)
    resumen = models.TextField(blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo


class Pregunta(models.Model):
    apunte = models.ForeignKey('Apunte', on_delete=models.CASCADE, related_name='preguntas')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    pregunta = models.TextField()
    opcion_1 = models.CharField(max_length=255)
    opcion_2 = models.CharField(max_length=255)
    opcion_3 = models.CharField(max_length=255)
    opcion_4 = models.CharField(max_length=255)
    respuesta_correcta = models.CharField(max_length=255)  # Guarda el texto de la respuesta correcta
    creada = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Pregunta de {self.apunte.titulo[:40]}..."


class ResultadoTest(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    apunte = models.ForeignKey(Apunte, on_delete=models.CASCADE)
    puntuacion = models.IntegerField()
    total_preguntas = models.IntegerField(default=15)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'apunte')  # solo 1 resultado por apunte por usuario

    def __str__(self):
        return f"{self.usuario.username} - {self.apunte.titulo} ({self.puntuacion}/{self.total_preguntas})"


