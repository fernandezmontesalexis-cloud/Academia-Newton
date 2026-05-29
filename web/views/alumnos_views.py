from django.shortcuts import render, redirect, get_object_or_404

from django.contrib import messages
from django.db.models import Exists, OuterRef, Q, Case, When, IntegerField
from web.permisos import permiso_requerido
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from datetime import date

from ..models import Alumno, Matricula, Ciclo, DesactivacionLog


def _matricula_activa_exists(alumno_pk, today):
    return Matricula.objects.filter(
        alumno_id=alumno_pk,
        ciclo__fecha_fin__gte=today,
    ).exists()


def _estado_academico_full(alumno, matriculas_list, today):
    if alumno.estado == 'bloqueado':
        return 'bloqueado'

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


def _sq_activa(today):
    return Matricula.objects.filter(
        alumno=OuterRef('pk'),
        ciclo__fecha_fin__gte=today,
    )


def _base_qs(sede, today):
    return (
        Alumno.objects.filter(sede=sede)
        .annotate(tiene_matricula_activa=Exists(_sq_activa(today)))
        .select_related('distrito', 'sede', 'apoderado')
        .prefetch_related('matricula_set__ciclo')
    )


def _set_ultimo_ciclo(alumno):
    matriculas = sorted(
        alumno.matricula_set.all(),
        key=lambda m: m.fecha_matricula,
        reverse=True,
    )
    alumno.ultimo_ciclo_nombre = matriculas[0].ciclo.nombre if matriculas else ''


@login_required
@permiso_requerido(['admin', 'secretaria'])
def lista_alumnos(request):
    sede = request.perfil.sede
    today = date.today()

    base = _base_qs(sede, today)

    # Solo matriculados activos
    alumnos_qs = base.filter(estado='activo', tiene_matricula_activa=True)

    dni = request.GET.get('dni')
    if dni:
        alumnos_qs = alumnos_qs.filter(dni__icontains=dni)

    # Contador para "Otros estados" — incluye inactivos, bloqueados y sin matrícula
    otros_count = base.filter(
        Q(estado='inactivo') | Q(estado='bloqueado') |
        Q(estado='activo', tiene_matricula_activa=False)
    ).count()

    paginator = Paginator(alumnos_qs.order_by('apellido_paterno', 'nombres'), 10)
    alumnos = paginator.get_page(request.GET.get('page'))

    for a in alumnos:
        a.estado_academico = 'matriculado'
        _set_ultimo_ciclo(a)

    return render(request, 'web/secretaria/alumnos/lista_alumnos.html', {
        'alumnos': alumnos,
        'otros_count': otros_count,
    })


@login_required
@permiso_requerido(['admin', 'secretaria'])
def lista_alumnos_otros(request):
    sede = request.perfil.sede
    today = date.today()

    base = _base_qs(sede, today)

    # Orden: sin matrícula (0) → inactivo automático (1) → bloqueado (2)
    alumnos_qs = base.filter(
        Q(estado='inactivo') | Q(estado='bloqueado') |
        Q(estado='activo', tiene_matricula_activa=False)
    ).annotate(
        orden=Case(
            When(Q(estado='activo', tiene_matricula_activa=False), then=0),
            When(estado='inactivo',  then=1),
            When(estado='bloqueado', then=2),
            default=3,
            output_field=IntegerField(),
        )
    )

    dni = request.GET.get('dni')
    if dni:
        alumnos_qs = alumnos_qs.filter(dni__icontains=dni)

    paginator = Paginator(
        alumnos_qs.order_by('orden', 'apellido_paterno', 'nombres'), 10
    )
    alumnos = paginator.get_page(request.GET.get('page'))

    for a in alumnos:
        if a.estado == 'bloqueado':
            a.estado_academico = 'bloqueado'
        elif a.estado == 'inactivo':
            a.estado_academico = 'inactivo'
        else:
            a.estado_academico = 'sin_matricula'
        _set_ultimo_ciclo(a)

    ciclos_disponibles = Ciclo.objects.filter(
        sede=sede,
        fecha_fin__gte=today,
    ).order_by('fecha_inicio')

    return render(request, 'web/secretaria/alumnos/lista_alumnos_otros.html', {
        'alumnos': alumnos,
        'ciclos_disponibles': ciclos_disponibles,
    })


@login_required
@permiso_requerido(['admin', 'secretaria'])
def desactivar_alumno(request, alumno_id):
    if request.method != 'POST':
        return redirect('lista_alumnos')
    alumno = get_object_or_404(Alumno, id=alumno_id, sede=request.perfil.sede)

    motivo     = request.POST.get('motivo',     '').strip()
    comentario = request.POST.get('comentario', '').strip()

    if motivo:
        DesactivacionLog.objects.create(
            alumno=alumno,
            motivo=motivo,
            comentario=comentario,
            registrado_por=request.perfil,
        )

    alumno.estado = 'bloqueado'
    alumno.save()
    return redirect('lista_alumnos_otros')


@login_required
@permiso_requerido(['admin', 'secretaria'])
def reactivar_alumno(request, alumno_id):
    if request.method != 'POST':
        return redirect('lista_alumnos')
    alumno = get_object_or_404(Alumno, id=alumno_id, sede=request.perfil.sede)
    if alumno.estado == 'bloqueado':
        return redirect('lista_alumnos_otros')
    alumno.estado = 'activo'
    alumno.save()
    return redirect('lista_alumnos_otros')


@login_required
@permiso_requerido(['admin', 'secretaria'])
def detalle_alumno(request, alumno_id):
    alumno = get_object_or_404(
        Alumno.objects.select_related('apoderado', 'distrito', 'sede'),
        id=alumno_id,
        sede=request.perfil.sede,
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
        Alumno, id=alumno_id, sede=request.perfil.sede
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

    alumno = get_object_or_404(Alumno, id=alumno_id, sede=request.perfil.sede)

    if alumno.estado == 'bloqueado':
        messages.error(request, "El alumno se encuentra bloqueado y no puede matricularse.")
        return redirect('lista_alumnos_otros')

    ciclo_id = request.POST.get('ciclo', '').strip()
    if not ciclo_id:
        messages.error(request, "Debe seleccionar un ciclo.")
        return redirect('lista_alumnos_otros')

    ciclo = get_object_or_404(Ciclo, id=ciclo_id, sede=alumno.sede)

    celular = request.POST.get('celular', '').strip()
    if celular:
        alumno.celular = celular
    alumno.email = request.POST.get('email', '').strip() or None

    if alumno.apoderado:
        apo_nombre  = request.POST.get('apo_nombre',   '').strip()
        apo_celular = request.POST.get('apo_celular',  '').strip()
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
        registrado_por=request.perfil,
    )

    return redirect('pagos', matricula_id=nueva_matricula.id)
