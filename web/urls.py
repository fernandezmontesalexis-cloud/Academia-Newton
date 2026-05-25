from django.urls import path
from .views.auth_views import login_view, logout_view
from .views.dashboard_views import dashboard
from .views.alumnos_views import (
    lista_alumnos, lista_alumnos_otros, detalle_alumno, editar_alumno,
    desactivar_alumno, reactivar_alumno, renovar_matricula,
)
from .views.registro_views import (
    registrar_alumno,
    registrar_apoderado,
    regis_form_academica,
    regis_form_adicional,
    cancelar_registro,
    nuevo_registro,
    get_distritos,
    get_provincias,
    buscar_colegios,
    crear_colegio,
)

from .views.matriculas_views import matriculas, matriculas_historial
from .views.pagos_views import pagos
from .views.reportes_views import reportes_sedes, reporte_sede_detalle
from .views.finanzas_views import finanzas, historial_completo, exportar_finanzas_excel
from .views.admin_views import (
    lista_ciclos,
    ciclos_sede_detalle,
    lista_sedes,
    crear_sede,
    editar_sede,
    eliminar_sede,
    reactivar_sede,
    crear_usuario,
    lista_usuarios,
    editar_usuario,
    eliminar_usuario,
    reactivar_usuario,
    crear_ciclo,
    editar_ciclo,
    eliminar_ciclo,
    configuracion,
)
from .views.pagos_views import (
    lista_pagos, reporte_ciclo, exportar_reportes, boleta_pdf,
    cancelar_matricula_nueva,
)

urlpatterns = [
    # AUTENTICACIÓN
    path("", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    # DASHBOARD
    path("dashboard/", dashboard, name="dashboard"),
    # SECRETARIA - ALUMNOS
    path("secretaria/alumnos/", lista_alumnos, name="lista_alumnos"),
    path("secretaria/alumnos/otros/", lista_alumnos_otros, name="lista_alumnos_otros"),
    path("secretaria/alumnos/<int:alumno_id>/", detalle_alumno, name="detalle_alumno"),
    path("secretaria/alumnos/<int:alumno_id>/editar/", editar_alumno, name="editar_alumno"),
    path("secretaria/alumnos/<int:alumno_id>/renovar/", renovar_matricula, name="renovar_matricula"),
    path("secretaria/alumnos/<int:alumno_id>/desactivar/", desactivar_alumno, name="desactivar_alumno"),
    path("secretaria/alumnos/<int:alumno_id>/reactivar/", reactivar_alumno, name="reactivar_alumno"),
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
    # para limpiar los campos de formulario
    path(
        "secretaria/nuevo-registro/",
        nuevo_registro,
        name="nuevo_registro",
    ),
    # MATRÍCULAS Y PAGOS
    path("secretaria/matriculas/", matriculas, name="matriculas"),
    path("secretaria/matriculas/historial/", matriculas_historial, name="matriculas_historial"),
    path("secretaria/pagos/<int:matricula_id>/", pagos, name="pagos"),
    path("secretaria/pagos/<int:matricula_id>/cancelar/", cancelar_matricula_nueva, name="cancelar_matricula_nueva"),
    path("secretaria/pagos/", lista_pagos, name="lista_pagos"),
    path("secretaria/pagos/ciclo/<int:ciclo_id>/", reporte_ciclo, name="reporte_ciclo"),
    path("secretaria/pagos/exportar/", exportar_reportes, name="exportar_reportes"),
    path("pagos/boleta/<int:pago_id>/", boleta_pdf, name="boleta_pdf"),
    # REPORTES
    path("reportes/sedes/", reportes_sedes, name="reportes_sedes"),
    path("reportes/sede/<int:sede_id>/", reporte_sede_detalle, name="reporte_sede_detalle"),
    # FINANZAS
    path("panel/finanzas/", finanzas, name="finanzas"),
    path("panel/finanzas/historial/", historial_completo, name="historial_completo"),
    path("panel/finanzas/exportar/", exportar_finanzas_excel, name="exportar_finanzas_excel"),
    # LISTA SEDE
    path("panel/sedes/", lista_sedes, name="lista_sedes"),
    path("panel/sedes/nueva/", crear_sede, name="crear_sede"),
    # departamento ,provincia , distrito
    path("get-provincias/<int:departamento_id>/", get_provincias),
    path("get-distritos/<int:provincia_id>/", get_distritos),
    # colegios
    path("buscar-colegios/", buscar_colegios),
    path("crear-colegio/", crear_colegio),
    path("panel/sedes/editar/<int:id>/", editar_sede, name="editar_sede"),
    # desactivar/reactivar sede (soft-delete)
    path("panel/sedes/eliminar/<int:id>/", eliminar_sede, name="eliminar_sede"),
    path("panel/sedes/reactivar/<int:id>/", reactivar_sede, name="reactivar_sede"),
    # crud crear usarios
    path("panel/usuarios/crear/", crear_usuario, name="crear_usuario"),
    # lista de usuarios
    path("panel/usuarios/", lista_usuarios, name="lista_usuarios"),
    # editar usuarios
    path("panel/usuarios/editar/<int:id>/", editar_usuario, name="editar_usuario"),
    # desactivar usuario (soft-delete)
    path("panel/usuarios/eliminar/<int:id>/", eliminar_usuario, name="eliminar_usuario"),
    # reactivar usuario
    path("panel/usuarios/reactivar/<int:id>/", reactivar_usuario, name="reactivar_usuario"),
    # ciclos
    path("panel/ciclos/", lista_ciclos, name="lista_ciclos"),
    path("panel/ciclos/sede/<int:sede_id>/", ciclos_sede_detalle, name="ciclos_sede_detalle"),
    path("panel/ciclos/crear/", crear_ciclo, name="crear_ciclo"),
    path("panel/ciclos/editar/<int:id>/", editar_ciclo, name="editar_ciclo"),
    path("panel/ciclos/eliminar/<int:id>/", eliminar_ciclo, name="eliminar_ciclo"),
    path("panel/configuracion/", configuracion, name="configuracion"),
]
