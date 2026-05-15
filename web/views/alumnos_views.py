from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Exists, OuterRef
from web.permisos import permiso_requerido
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from datetime import date

from ..models import Alumno, Matricula, Ciclo


def _matricula_activa_exists(alumno_pk, today):
    """
    Consulta directa a DB: ¿tiene el alumno una matrícula con ciclo vigente hoy?
    Misma lógica de fecha que usa matriculas_views (ciclo__fecha_inicio__lte / fecha_fin__gte).
    """
    return Matricula.objects.filter(
        alumno_id=alumno_pk,
        ciclo__fecha_inicio__lte=today,
        ciclo__fecha_fin__gte=today,
    ).exists()


def _estado_academico_full(alumno, matriculas_list, today):
    """
    Para el detalle: usa DB para verificar ciclo activo + auto-inactivación.
    """
    if alumno.estado == 'inactivo':
        return 'inactivo'

    if _matricula_activa_exists(alumno.pk, today):
        return 'matriculado'

    # Auto-inactivar si pasaron 2+ ciclos en la sede sin renovar
    if matriculas_list:
        last_ciclo_end = max(m.ciclo.fecha_fin for m in matriculas_list)
        ciclos_posteriores = Ciclo.objects.filter(
            sede=alumno.sede,
            fecha_inicio__gt=last_ciclo_end,
        ).count()
        if ciclos_posteriores >= 2:
            alumno.estado = 'inactivo'
            alumno.save(update_fields=['estado'])
            return 'inactivo'

    return 'sin_matricula'


@login_required
@permiso_requerido(['admin', 'secretaria'])
def lista_alumnos(request):
    sede = request.user.perfil.sede
    today = date.today()

    # Subquery DB: ciclo vigente hoy — misma condición que en matriculas_views
    sq_activa = Matricula.objects.filter(
        alumno=OuterRef('pk'),
        ciclo__fecha_inicio__lte=today,
        ciclo__fecha_fin__gte=today,
    )

    alumnos_qs = (
        Alumno.objects.filter(sede=sede)
        .annotate(tiene_matricula_activa=Exists(sq_activa))
        .select_related('distrito', 'sede', 'apoderado')
        .prefetch_related('matricula_set__ciclo')
    )

    dni = request.GET.get('dni')
    if dni:
        alumnos_qs = alumnos_qs.filter(dni__icontains=dni)

    paginator = Paginator(alumnos_qs, 10)
    alumnos = paginator.get_page(request.GET.get('page'))

    for a in alumnos:
        # Estado académico derivado de la anotación DB (fuente única de verdad)
        if a.estado == 'inactivo':
            a.estado_academico = 'inactivo'
        elif a.tiene_matricula_activa:
            a.estado_academico = 'matriculado'
        else:
            a.estado_academico = 'sin_matricula'

        # Último ciclo para el modal de renovación
        matriculas = sorted(
            a.matricula_set.all(),
            key=lambda m: m.fecha_matricula,
            reverse=True,
        )
        a.ultimo_ciclo_nombre = matriculas[0].ciclo.nombre if matriculas else ''

    ciclos_disponibles = Ciclo.objects.filter(
        sede=sede,
        fecha_fin__gte=today,
    ).order_by('fecha_inicio')

    return render(request, 'web/secretaria/alumnos/lista_alumnos.html', {
        'alumnos': alumnos,
        'ciclos_disponibles': ciclos_disponibles,
    })


@login_required
@permiso_requerido(['admin', 'secretaria'])
def desactivar_alumno(request, alumno_id):
    if request.method != 'POST':
        return redirect('lista_alumnos')
    alumno = get_object_or_404(Alumno, id=alumno_id, sede=request.user.perfil.sede)
    alumno.estado = 'inactivo'
    alumno.save()
    return redirect('lista_alumnos')


@login_required
@permiso_requerido(['admin', 'secretaria'])
def reactivar_alumno(request, alumno_id):
    if request.method != 'POST':
        return redirect('lista_alumnos')
    alumno = get_object_or_404(Alumno, id=alumno_id, sede=request.user.perfil.sede)
    alumno.estado = 'activo'
    alumno.save()
    return redirect('lista_alumnos')


@login_required
@permiso_requerido(['admin', 'secretaria'])
def detalle_alumno(request, alumno_id):
    alumno = get_object_or_404(
        Alumno.objects.select_related('apoderado', 'distrito', 'sede'),
        id=alumno_id,
        sede=request.user.perfil.sede,
    )

    formacion_academica = getattr(alumno, 'formacionacademica', None)
    formacion_adicional = getattr(alumno, 'formacionadicional', None)

    matriculas_qs = (
        Matricula.objects.filter(alumno=alumno)
        .select_related('ciclo')
        .prefetch_related('pago_set')
        .order_by('-fecha_matricula')
    )
    matriculas_list = list(matriculas_qs)

    historial = []
    for m in matriculas_list:
        historial.append({
            'matricula': m,
            'pagos': m.pago_set.order_by('-fecha_pago'),
            'total_pagado': m.total_pagado(),
            'deuda': m.deuda(),
        })

    today = date.today()
    estado_academico = _estado_academico_full(alumno, matriculas_list, today)

    return render(request, 'web/secretaria/alumnos/detalle_alumno.html', {
        'alumno': alumno,
        'formacion_academica': formacion_academica,
        'formacion_adicional': formacion_adicional,
        'historial': historial,
        'estado_academico': estado_academico,
    })


@login_required
@permiso_requerido(['admin', 'secretaria'])
def editar_alumno(request, alumno_id):
    alumno = get_object_or_404(
        Alumno, id=alumno_id, sede=request.user.perfil.sede
    )
    if request.method == 'POST':
        alumno.apellido_paterno = request.POST.get('apellido_paterno', '').strip()
        alumno.apellido_materno = request.POST.get('apellido_materno', '').strip()
        alumno.nombres = request.POST.get('nombres', '').strip()
        alumno.celular = request.POST.get('celular', '').strip()
        alumno.email = request.POST.get('email', '').strip() or None
        alumno.direccion = request.POST.get('direccion', '').strip()
        alumno.save()
        return redirect('detalle_alumno', alumno_id=alumno.id)
    return render(request, 'web/secretaria/alumnos/editar_alumno.html', {'alumno': alumno})


@login_required
@permiso_requerido(['admin', 'secretaria'])
def renovar_matricula(request, alumno_id):
    if request.method != 'POST':
        return redirect('lista_alumnos')

    alumno = get_object_or_404(Alumno, id=alumno_id, sede=request.user.perfil.sede)

    ciclo_id = request.POST.get('ciclo', '').strip()
    if not ciclo_id:
        messages.error(request, "Debe seleccionar un ciclo.")
        return redirect('lista_alumnos')

    ciclo = get_object_or_404(Ciclo, id=ciclo_id, sede=alumno.sede)

    celular = request.POST.get('celular', '').strip()
    if celular:
        alumno.celular = celular
    alumno.email = request.POST.get('email', '').strip() or None

    if alumno.apoderado:
        apo_nombre = request.POST.get('apo_nombre', '').strip()
        apo_celular = request.POST.get('apo_celular', '').strip()
        if apo_nombre:
            alumno.apoderado.nombre_completo = apo_nombre
        if apo_celular:
            alumno.apoderado.celular = apo_celular
        alumno.apoderado.save()

    if alumno.estado == 'inactivo':
        alumno.estado = 'activo'

    alumno.save()

    nueva_matricula = Matricula.objects.create(
        alumno=alumno,
        ciclo=ciclo,
        fecha_matricula=date.today(),
        estado='pendiente',
        registrado_por=request.user.perfil,
    )

    return redirect('pagos', matricula_id=nueva_matricula.id)
