from django.urls import path
from . import views

urlpatterns = [

    # AUTENTICACIÓN
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # DASHBOARD
    path('dashboard/', views.dashboard, name='dashboard'),

    # secretaria
    path('secretaria/alumnos/', views.lista_alumnos, name='lista_alumnos'),
    path('secretaria/alumnos/estado/<int:alumno_id>/', views.cambiar_estado_alumno, name='cambiar_estado_alumno'),

    path('secretaria/registrar-alumno/', views.registrar_alumno, name='registrar_alumno'),
    path('secretaria/registrar-apoderado/', views.registrar_apoderado, name='registrar_apoderado'),
    path('secretaria/formacion-academica/', views.regis_form_academica, name='regis_form_academica'),
    path('secretaria/formacion-adicional/', views.regis_form_adicional, name='regis_form_adicional'),

    path('secretaria/matriculas/', views.matriculas, name='matriculas'),
    path('secretaria/pagos/<int:matricula_id>/', views.pagos, name='pagos'),

    path('secretaria/cancelar-registro/', views.cancelar_registro, name='cancelar_registro'),

    # Reportes
    path('reportes/sedes/', views.reportes_sedes, name='reportes_sedes'),

    # administrador
    path('admin/ciclos/', views.lista_ciclos, name='lista_ciclos'),
    #path('admin/sedes/', views.lista_sedes, name='lista_sedes'),
    #path('admin/reportes/', views.reportes_admin, name='reportes_admin'),

]