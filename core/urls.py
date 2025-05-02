from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomEmailLoginForm as LoginForm
from .views import register_view, CustomPasswordResetConfirmView, CustomPasswordResetView, CustomLoginView, \
    subir_apunte_view

# urls de la app
urlpatterns = [
    # Ruta para el inicio de sesión, usando la vista predeterminada de Django y un formulario personalizado.
    path('login/', CustomLoginView.as_view(), name='login'),
    path('', views.welcome_view, name='welcome'),
    path('register/', register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('mis-apuntes/', views.mis_apuntes_view, name='mis_apuntes'),
    path('resumenes/', views.resumenes_view, name='resumenes'),
    path('preguntas/', views.preguntas_view, name='preguntas'),
    path('historial-resultados/', views.historial_resultados_view, name='historial_resultados'),

    # Auth
    path('logout/', views.custom_logout_view, name='logout'),
    # Password reset flow
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),

    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='auth/password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(
        template_name='auth/password_reset_confirm.html',
        success_url='/reset/complete/'
    ), name='password_reset_confirm'),

    path('reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='auth/password_reset_complete.html'
    ), name='password_reset_complete'),

    # Activación de cuenta
    path('activate/<uidb64>/<token>/', views.activar_cuenta, name='activate'),
    path('reset/invalid/', views.reset_invalid_view, name='password_reset_invalid'),

    # Perfil y reenvío de activación
    path('perfil/', views.perfil_view, name='perfil'),
    path('reenviar-activacion/', views.reenviar_activacion_view, name='reenviar_activacion'),

    path('subir-apunte/', subir_apunte_view, name='subir_apunte'),
    path('resumenes/', views.resumenes_view, name='resumenes'),
    path('resumenes/<int:apunte_id>/', views.detalle_resumen_view, name='detalle_resumen'),
    path('mis-apuntes/', views.mis_apuntes_view, name='mis_apuntes'),
    path('mis-apuntes/<int:apunte_id>/', views.detalle_apuntes_view, name='detalle_apuntes'),
    path('mis-apuntes/<int:apunte_id>/eliminar/', views.eliminar_apunte_view, name='eliminar_apunte'),
    path('generar-preguntas/', views.seleccionar_apunte_view, name='seleccionar_apunte'),
    path('generar-preguntas/<int:apunte_id>/', views.generar_preguntas_view, name='generar_preguntas'),
    path('guardar-resultado/', views.guardar_resultado_test, name='guardar_resultado_test'),
    path('test-interactivo/<int:apunte_id>/', views.test_interactivo_view, name='test_interactivo'),

    path('guardar-resultado/', views.guardar_resultado_test, name='guardar_resultado_test'),
    path('guardar-resultado/', views.guardar_resultado_test, name='guardar_resultado_test'),
    path('descargar/test/<int:apunte_id>/', views.exportar_test_pdf, name='exportar_test_pdf'),

]
