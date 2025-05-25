from pathlib import Path
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView
from django.db.models import Max
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
import json

from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

from .forms import CustomUserCreationForm, PerfilForm, CustomEmailLoginForm
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth import logout
from django.views.decorators.cache import never_cache
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage, EmailMultiAlternatives, send_mail
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from .models import PerfilUsuario, Apunte, Categoria, Pregunta, ResultadoTest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from .forms import ApunteForm
from .utils import resumir_texto_con_ia, extraer_texto_de_pdf, predecir_categoria_con_ia, generar_titulo_con_ia, \
    generar_preguntas_con_ia, generar_consejo_diario_con_cache
from django.contrib.auth.decorators import login_required

User = get_user_model()


def enviar_email_cambio_contrasena(user):
    subject = "Contraseña actualizada en EdukAI"
    message = render_to_string('auth/password_changed_email.html', {
        'user': user,
    })

    email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    email.content_subtype = 'html'  # Para enviar como HTML
    email.send()


def reenviar_activacion_view(request):
    if request.method == 'POST':
        email = request.POST.get('email').strip()
        user = User.objects.filter(email=email, is_active=False).first()
        if user:
            enviar_activacion(request, user)
            messages.success(request, "Te hemos enviado un nuevo enlace de activación a tu email.")
            request.session.pop('inactive_email', None)
            request.session.pop('token_expired_email', None)
            request.session.pop('token_expired', None)
            return redirect('login')
        else:
            messages.error(request, "No se encontró una cuenta inactiva con ese correo.")
    return render(request, 'auth/password_reset_done.html')


def activar_cuenta(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, '¡Tu cuenta ha sido activada con éxito! Ya puedes iniciar sesión.')
        return redirect('login')
    else:
        email = user.email if user else ''
        return render(request, 'auth/account_activation_invalid.html', {'email': email})


def enviar_activacion(request, user):
    if not user.is_active:
        current_site = get_current_site(request)
        subject = 'Activa tu cuenta en EdukAI'
        message = render_to_string('auth/account_activation_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
            'protocol': 'https' if request.is_secure() else 'http',
        })
        email = EmailMessage(subject, message, to=[user.email])
        email.content_subtype = 'html'
        email.send()


def reset_invalid_view(request):
    request.session.pop('token_expired_email', None)
    request.session.pop('token_expired', None)
    return render(request, 'auth/password_reset_invalid.html')


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'auth/password_reset_confirm.html'
    success_url = '/reset/complete/'

    def dispatch(self, request, *args, **kwargs):
        # Deja que Django maneje el flujo y prepare valid_link
        response = super().dispatch(request, *args, **kwargs)

        # Si el token es inválido, redirige a template personalizado
        if not getattr(self, 'valid_link', True):
            request.session['token_expired'] = True
            return redirect('password_reset_invalid')

        return response

    def form_valid(self, form):
        # Limpia cualquier rastro de error anterior
        self.request.session.pop('token_expired', None)
        self.request.session.pop('token_expired_email', None)
        return super().form_valid(form)


class CustomLoginView(LoginView):
    template_name = 'login.html'
    authentication_form = CustomEmailLoginForm

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_active:
            self.request.session['inactive_email'] = user.email
            return self.form_invalid(form)
        login(self.request, user)
        return super().form_valid(form)

    def form_invalid(self, form):
        # self.request.session.pop('inactive_email', None)
        return super().form_invalid(form)


class CustomPasswordResetView(PasswordResetView):
    template_name = 'auth/password_reset.html'
    email_template_name = 'auth/password_reset_email.html'
    subject_template_name = 'auth/password_reset_subject.txt'
    success_url = '/password-reset/done/'

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        user = User.objects.filter(email=email, is_active=True).first()
        if user:
            context = {
                'email': email,
                'domain': self.request.get_host(),
                'site_name': 'EdukAI',
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': default_token_generator.make_token(user),
                'protocol': 'https' if self.request.is_secure() else 'http',
            }
            subject = render_to_string(self.subject_template_name, context).strip()
            html_email = render_to_string(self.email_template_name, context)
            email_message = EmailMultiAlternatives(subject, '', settings.DEFAULT_FROM_EMAIL, [email])
            email_message.attach_alternative(html_email, "text/html")
            email_message.send()
            return redirect(self.success_url)
        else:
            messages.error(self.request, "No se encontró ninguna cuenta activa con ese correo.")
            return self.form_invalid(form)


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            estudio_actual = form.cleaned_data.get('estudio_actual')
            PerfilUsuario.objects.create(user=user, estudio_actual=estudio_actual)
            enviar_activacion(request, user)
            messages.info(request, "Te hemos enviado un correo para activar tu cuenta.")
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


def terminos_view(request):
    return render(request, 'secciones/terminos.html')


def custom_logout_view(request):
    logout(request)
    messages.success(request, "Has cerrado sesión correctamente.")
    return redirect('welcome')


def welcome_view(request):
    return render(request, 'welcome.html')


def dashboard_view(request):
    if request.user.is_authenticated:
        apuntes = Apunte.objects.filter(usuario=request.user).order_by('-creado')
        userId = request.user.id
        user_name = User.objects.get(id=userId).get_username()
        estudio_actual = PerfilUsuario.objects.get(user_id=userId).estudio_actual

        consejo = generar_consejo_diario_con_cache(userId, estudio_actual,user_name)

        return render(request, 'dashboard.html', {'apuntes': apuntes, 'consejo': consejo, 'active': 'dashboard'})
    else:
        return render(request, 'dashboard.html', {'active': 'dashboard'})


@never_cache
@login_required
def perfil_view(request):
    perfil, created = PerfilUsuario.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=perfil, user=request.user)
        user = request.user
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        new_password = request.POST.get('new_password')

        if form.is_valid():
            user.save()
            perfil = form.save(commit=False)

            if form.cleaned_data.get('eliminar_imagen') and perfil.imagen:
                imagen_path = Path(perfil.imagen.path)
                perfil.imagen.delete(save=False)
                if imagen_path.exists():
                    imagen_path.unlink()
                perfil.imagen = None

            if request.FILES.get('imagen'):
                if perfil.imagen and perfil.imagen.name != request.FILES['imagen'].name:
                    imagen_path = Path(perfil.imagen.path)
                    perfil.imagen.delete(save=False)
                    if imagen_path.exists():
                        imagen_path.unlink()
                perfil.avatar_default = None

            if form.cleaned_data.get('avatar_default') and not request.FILES.get('imagen'):
                if perfil.imagen:
                    imagen_path = Path(perfil.imagen.path)
                    perfil.imagen.delete(save=False)
                    if imagen_path.exists():
                        imagen_path.unlink()
                    perfil.imagen = None
            if new_password:
                try:
                    validate_password(new_password, user=user)
                    user.set_password(new_password)
                    user.save()
                    update_session_auth_hash(request, user)
                    enviar_email_cambio_contrasena(user)
                    messages.success(request, "Se ha enviado un email de confirmacion.")
                except ValidationError as e:
                    for error in e:
                        messages.error(request, error)
                    return render(request, 'secciones/perfil.html',
                                  {'form': form, 'user': request.user, 'active': 'perfil'})

            if not request.FILES.get('imagen') and not form.cleaned_data.get('eliminar_imagen'):
                if not form.cleaned_data.get('avatar_default'):
                    perfil.avatar_default = perfil.avatar_default
            perfil.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect('dashboard')
    else:
        form = PerfilForm(instance=perfil, user=request.user)

    return render(request, 'secciones/perfil.html', {
        'form': form,
        'user': request.user,
        'active': 'perfil'
    })


@never_cache
@login_required
def subir_apunte_view(request):
    if request.method == 'POST':
        form = ApunteForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = form.cleaned_data.get('archivo')
            texto_manual = form.cleaned_data.get('texto')
            texto_extraido = None
            if archivo:
                texto_extraido = extraer_texto_de_pdf(archivo)

            texto_para_resumir = texto_manual or texto_extraido

            if not texto_para_resumir:
                form.add_error(None, "No se pudo extraer texto del archivo o el texto manual está vacío.")
                return render(request, 'secciones/subir_apunte.html', {'form': form, 'active': 'subir_apunte'})

            # Generar resumen, categoría, guardar apunte... (el resto de tu lógica)
            resumen_generado = resumir_texto_con_ia(texto_para_resumir)
            categoria_nombre = predecir_categoria_con_ia(texto_para_resumir)
            categoria, _ = Categoria.objects.get_or_create(nombre=categoria_nombre)
            apunte = form.save(commit=False)
            if not form.cleaned_data.get('titulo'):
                apunte.titulo = generar_titulo_con_ia(texto_para_resumir)
            else:
                apunte.titulo = form.cleaned_data.get('titulo')
            apunte.usuario = request.user
            apunte.resumen = resumen_generado
            apunte.categoria = categoria
            apunte.save()
            messages.success(request,
                             f"Apunte subido y categorizado automáticamente como: {categoria.nombre} puedes ir a la seccion Mis Apuntes para verlos")
            return redirect('dashboard')
        else:

            return render(request, 'secciones/subir_apunte.html', {'form': form, 'active': 'subir_apunte'})
    else:
        form = ApunteForm()
    return render(request, 'secciones/subir_apunte.html', {'form': form, 'active': 'subir_apunte'})


@never_cache
@login_required
def resumenes_view(request):
    resumenes = Apunte.objects.filter(usuario=request.user).exclude(resumen="").order_by('-creado')
    return render(request, 'secciones/resumenes.html', {'resumenes': resumenes, 'active': 'resumenes'})


@never_cache
@login_required
def detalle_resumen_view(request, apunte_id):
    apunte = get_object_or_404(Apunte, id=apunte_id, usuario=request.user)
    return render(request, 'secciones/detalle_resumen.html', {'apunte': apunte, 'active': 'resumenes'})


@never_cache
@login_required
def mis_apuntes_view(request):
    apuntes = Apunte.objects.filter(usuario=request.user).order_by('-creado')
    return render(request, 'secciones/mis_apuntes.html', {'apuntes': apuntes, 'active': 'mis_apuntes'})


@never_cache
@login_required
def detalle_apuntes_view(request, apunte_id):
    apunte = get_object_or_404(Apunte, id=apunte_id, usuario=request.user)

    return render(request, 'secciones/detalle_apuntes.html', {'apunte': apunte, 'active': 'mis_apuntes'})


@never_cache
@login_required
def eliminar_apunte_view(request, apunte_id):
    apunte = get_object_or_404(Apunte, id=apunte_id, usuario=request.user)
    pregunta = get_object_or_404(Pregunta, id=apunte_id)

    if request.method == 'POST':
        apunte.delete()
        messages.success(request, "Apunte, resumen preguntas y resultado eliminados correctamente.")
        return redirect('mis_apuntes')

    return redirect('detalle_apunte', apunte_id=apunte_id)


@never_cache
@login_required
def lastest_apunte_view(request):
    apuntes = Apunte.objects.filter(usuario=request.user).order_by('-creado')
    return render(request, 'dashboard.html', {'apuntes': apuntes, 'active': 'dashboard'})


@never_cache
@login_required
def seleccionar_apunte_view(request):
    apuntes = Apunte.objects.filter(usuario=request.user).order_by('-creado')
    return render(request, 'secciones/generar_pregunta.html', {'apuntes': apuntes, 'active': 'preguntas'})


@never_cache
@login_required
def generar_preguntas_view(request, apunte_id):
    apunte = get_object_or_404(Apunte, id=apunte_id, usuario=request.user)

    # Llamar a la IA para generar las preguntas
    preguntas_texto = generar_preguntas_con_ia(apunte.texto)

    # Aquí parseamos las preguntas generadas
    preguntas = parsear_preguntas_desde_texto(preguntas_texto)

    # Guardar las preguntas en la base de datos
    for p in preguntas:
        Pregunta.objects.create(
            apunte=apunte,
            usuario=request.user,
            pregunta=p['pregunta'],
            opcion_1=p['opciones'][0],
            opcion_2=p['opciones'][1],
            opcion_3=p['opciones'][2],
            opcion_4=p['opciones'][3],
            respuesta_correcta=p['respuesta_correcta']
        )

    messages.success(request,
                     f"Se han generado {len(preguntas)} preguntas para el apunte \"{apunte.titulo}\". Ve a la seccion Mis Preguntas para verlas")

    return redirect('dashboard')


def parsear_preguntas_desde_texto(texto):
    try:
        texto_decodificado = texto.encode('utf-8').decode('utf-8-sig')

        # Buscar el primer corchete [ y el último ]
        inicio = texto_decodificado.find('[')
        fin = texto_decodificado.rfind(']') + 1  # incluimos el corchete final

        if inicio == -1 or fin == -1:
            return []

        json_texto = texto_decodificado[inicio:fin]

        preguntas = json.loads(json_texto)
        return preguntas
    except Exception as e:
        print(f"Error al parsear JSON: {e}")
        return []


@never_cache
@login_required
def preguntas_view(request):
    apuntes_con_preguntas = Apunte.objects.filter(
        usuario=request.user,
        preguntas__isnull=False
    ).annotate(
        ultima_pregunta=Max('preguntas__creada')
    ).distinct().order_by('-ultima_pregunta')

    return render(request, 'secciones/preguntas.html', {
        'apuntes': apuntes_con_preguntas,
        'active': 'preguntas'
    })


@never_cache
@login_required
def test_interactivo_view(request, apunte_id):
    # Obtener el apunte específico o devolver un 404 si no existe o no pertenece al usuario
    apunte = get_object_or_404(Apunte, id=apunte_id, usuario=request.user)

    # Filtrar las preguntas por el apunte_id y el usuario, luego obtener 15 aleatorias
    preguntas = list(
        Pregunta.objects.filter(apunte=apunte, usuario=request.user).order_by('?').values('pregunta', 'opcion_1',
                                                                                          'opcion_2', 'opcion_3',
                                                                                          'opcion_4',
                                                                                          'respuesta_correcta')[:15])
    return render(request, 'secciones/test_interactivo.html',
                  {'preguntas': preguntas, 'apunte': apunte, 'active': 'preguntas'})


@never_cache
@login_required
def historial_resultados_view(request):
    resultados = ResultadoTest.objects.filter(usuario=request.user).select_related('apunte').order_by('-fecha')
    return render(request, 'secciones/historial_tests.html',
                  {'resultados': resultados, 'active': 'historial_resultados'})


@never_cache
@login_required
@require_POST
def guardar_resultado_test(request):
    apunte_id = request.POST.get('apunte_id')
    puntuacion = int(request.POST.get('puntuacion'))
    total_preguntas = int(request.POST.get('total_preguntas', 15))

    apunte = get_object_or_404(Apunte, id=apunte_id, usuario=request.user)

    resultado, creado = ResultadoTest.objects.get_or_create(
        usuario=request.user,
        apunte=apunte,
        defaults={'puntuacion': puntuacion, 'total_preguntas': total_preguntas}
    )

    if not creado:
        if puntuacion > resultado.puntuacion:
            resultado.puntuacion = puntuacion
            resultado.save()
            return JsonResponse({'status': 'mejorado'})
        else:
            return JsonResponse({'status': 'sin_mejora'})
    return JsonResponse({'status': 'nuevo'})


@never_cache
@login_required
def exportar_test_pdf(request, apunte_id):
    apunte = Apunte.objects.get(id=apunte_id, usuario=request.user)
    preguntas = Pregunta.objects.filter(apunte=apunte, usuario=request.user)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="test_{apunte.titulo}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y = height - 50

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Test generado por EdukAI")
    y -= 30

    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"{apunte.titulo}")
    y -= 30
    respuestas_finales = []
    for idx, pregunta in enumerate(preguntas, start=1):
        if y < 150:
            p.showPage()
            y = height - 50

        # Mostrar pregunta con salto de línea
        texto_pregunta = f"{idx}. {pregunta.pregunta}"
        lineas = simpleSplit(texto_pregunta, "Helvetica", 12, width - 100)
        for linea in lineas:
            p.drawString(50, y, linea)
            y -= 20

        # Mostrar opciones
        opciones = [
            f"A) {pregunta.opcion_1}",
            f"B) {pregunta.opcion_2}",
            f"C) {pregunta.opcion_3}",
            f"D) {pregunta.opcion_4}",
        ]
        for opcion in opciones:
            lineas_opcion = simpleSplit(opcion, "Helvetica", 12, width - 100)
            for linea in lineas_opcion:
                if y < 50:
                    p.showPage()
                    y = height - 50
                p.drawString(70, y, linea)
                y -= 20

        # Respuesta correcta
        y -= 20
        respuestas_finales.append(f"{idx}. {pregunta.pregunta}: \n {pregunta.respuesta_correcta}")

    p.showPage()
    y = height - 50
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, " Respuestas Correctas")
    y -= 30
    p.setFont("Helvetica", 12)

    for respuesta in respuestas_finales:

        lineas_opcion = simpleSplit(respuesta, "Helvetica", 12, width - 100)
        for linea in lineas_opcion:
            if y < 50:
                p.showPage()
                y = height - 50
            p.drawString(70, y, linea)
            y -= 20
        y -= 20
    p.save()
    return response


@never_cache
@login_required
def ver_test_view(request, apunte_id):
    apunte = get_object_or_404(Apunte, id=apunte_id, usuario=request.user)
    preguntas = Pregunta.objects.filter(apunte=apunte, usuario=request.user)
    return render(request, 'secciones/detalle_test.html', {'apunte': apunte, 'preguntas': preguntas})
