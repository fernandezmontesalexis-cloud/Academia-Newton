from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('registrar_alumno/', views.registrar_alumno, name='registrar_alumno'),
    path('registrar_apoderado/',views.registrar_apoderado, name='registrar_apoderado'),
    path('regis_form_academica/',views.regis_form_academica, name='regis_form_academica'),
    path('regis_form_adicional/',views.regis_form_adicional, name='regis_form_adicional'),
    path('logout/', views.logout_view, name='logout'),
    path('matriculas/', views.matriculas, name='matricula'),
    path('pagos/<int:matricula_id>/', views.pagos, name='pagos'),
    path('cancelar-registro/', views.cancelar_registro, name='cancelar_registro'),
    path('reportes-sedes/', views.reportes_sedes, name='reportes_sedes'),
    path('alumnos/', views.lista_alumnos, name='lista_alumnos'),
    path('alumno/estado/<int:alumno_id>/', views.cambiar_estado_alumno, name='cambiar_estado_alumno'),
]