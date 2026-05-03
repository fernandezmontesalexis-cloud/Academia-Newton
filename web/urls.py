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
)

import web.old_views as views  # para lo que aún no movemos
from .views.matriculas_views import matriculas
from .views.pagos_views import pagos
from .views.reportes_views import reportes_sedes
from .views.admin_views import lista_ciclos
from .views.admin_views import lista_sedes
from .views.admin_views import crear_sede

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

    # MATRÍCULAS Y PAGOS (aún en old_views)
    path("secretaria/matriculas/", matriculas, name="matriculas"),
    path("secretaria/pagos/<int:matricula_id>/", pagos, name="pagos"),

    # REPORTES
    path("reportes/sedes/", reportes_sedes, name="reportes_sedes"),

    # ADMIN
    path("panel/ciclos/", lista_ciclos, name="lista_ciclos"),
    #LISTA SEDE
    path("panel/sedes/", lista_sedes, name="lista_sedes"),
    path("panel/sedes/nueva/", crear_sede, name="crear_sede"),
    

]