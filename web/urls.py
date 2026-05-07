from django.urls import path
from .views.auth_views import login_view, logout_view
from .views.dashboard_views import dashboard
from .views.alumnos_views import lista_alumnos, cambiar_estado_alumno
from .views.registro_views import (
    registrar_alumno,
    registrar_apoderado,
    regis_form_academica,
    regis_form_adicional,
    cancelar_registro,
    get_distritos,
    get_provincias,
    buscar_colegios,
    crear_colegio,
)

from .views.matriculas_views import matriculas
from .views.pagos_views import pagos
from .views.reportes_views import reportes_sedes
from .views.admin_views import lista_ciclos
from .views.admin_views import lista_sedes
from .views.admin_views import crear_sede
from .views.admin_views import editar_sede
from .views.admin_views import eliminar_sede
from .views.admin_views import crear_usuario
from .views.admin_views import lista_usuarios
from .views.admin_views import editar_usuario
from .views.admin_views import eliminar_usuario
from .views.admin_views import crear_ciclo
from .views.pagos_views import lista_pagos 
from .views.pagos_views import boleta_pdf

urlpatterns = [
    # AUTENTICACIÓN
    path("", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    # DASHBOARD
    path("dashboard/", dashboard, name="dashboard"),

    # SECRETARIA - ALUMNOS
    path("secretaria/alumnos/", lista_alumnos, name="lista_alumnos"),
    path(
        "secretaria/alumnos/estado/<int:alumno_id>/",
        cambiar_estado_alumno,
        name="cambiar_estado_alumno",
    ),

    # SECRETARIA - REGISTRO (YA CORREGIDO)
    path("secretaria/registrar-alumno/", registrar_alumno, name="registrar_alumno"),
    path(
        "secretaria/registrar-apoderado/",
        registrar_apoderado,
        name="registrar_apoderado",
    ),
    path(
        "secretaria/formacion-academica/",
        regis_form_academica,
        name="regis_form_academica",
    ),
    path(
        "secretaria/formacion-adicional/",
        regis_form_adicional,
        name="regis_form_adicional",
    ),
    path(
        "secretaria/cancelar-registro/",
        cancelar_registro,
        name="cancelar_registro",
    ),

    # MATRÍCULAS Y PAGOS
    path("secretaria/matriculas/", matriculas, name="matriculas"),
    path("secretaria/pagos/<int:matricula_id>/", pagos, name="pagos"),
    path("secretaria/pagos/", lista_pagos, name="lista_pagos"),
    path('pagos/boleta/<int:pago_id>/', boleta_pdf, name='boleta_pdf'),

    # REPORTES
    path("reportes/sedes/", reportes_sedes, name="reportes_sedes"),

    
    #LISTA SEDE
    path("panel/sedes/", lista_sedes, name="lista_sedes"),
    path("panel/sedes/nueva/", crear_sede, name="crear_sede"),

    #departamento ,provincia , distrito
    path("get-provincias/<int:departamento_id>/", get_provincias),
    path("get-distritos/<int:provincia_id>/", get_distritos),

    #colegios
    path("buscar-colegios/", buscar_colegios),
    path("crear-colegio/", crear_colegio),

    path("panel/sedes/editar/<int:id>/", editar_sede, name="editar_sede"),
    #eliminar sede
    path("panel/sedes/eliminar/<int:id>/", eliminar_sede, name="eliminar_sede"),

    #crud crear usarios
    path("panel/usuarios/crear/", crear_usuario, name="crear_usuario"),
    #lista de usaurios
    path("panel/usuarios/", lista_usuarios, name="lista_usuarios"),
    #editar usuarios
    path("panel/usuarios/editar/<int:id>/", editar_usuario, name="editar_usuario"),
    #eliminar usuario
    path("panel/usuarios/eliminar/<int:id>/", eliminar_usuario, name="eliminar_usuario"),
    #crear crud de ciclos
    path("panel/ciclos/", lista_ciclos, name="lista_ciclos"),
    path("panel/ciclos/crear/", crear_ciclo, name="crear_ciclo"),

]