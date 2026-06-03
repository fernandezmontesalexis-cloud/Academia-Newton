from django.shortcuts import render, redirect, get_object_or_404

from django.contrib import messages
from django.db.models import Exists, OuterRef, Q, Case, When, IntegerField
from web.permisos import permiso_requerido
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from datetime import date

from ..models import Alumno, Matricula, Ciclo, DesactivacionLog


def _matricula_activa_exists(alumno_pk, today):
    # Reviso si el alumno tiene alguna matrícula en un ciclo que aún no ha terminado
    return Matricula.objects.filter(
        alumno_id=alumno_pk,
        ciclo__fecha_fin__gte=today,
    ).exists()


def _estado_academico_full(alumno, matriculas_list, today):
    """
    Determina el estado académico real del alumno.
    También auto-inactiva al alumno si pasaron 2 o más ciclos sin que renovara.
    """
    # Si está bloqueado o inactivo, no necesito revisar más — devuelvo ese estado
    if alumno.estado == 'bloqueado':
        return 'bloqueado'
    if alumno.estado == 'inactivo':
        return 'inactivo'

    # Si tiene una matrícula en un ciclo vigente, está matriculado
    if _matricula_activa_exists(alumno.pk, today):
        return 'matriculado'

    # Si no tiene matrícula activa, reviso cuántos ciclos pasaron desde el último
    # — si pasaron 2 o más ciclos sin renovar, lo paso a inactivo automáticamente
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

    # Tiene historial pero no está en ningún ciclo activo — simplemente sin matrícula
    return 'sin_matricula'


def _sq_activa(today):
    # Subconsulta: devuelve True si el alumno tiene matrícula en ciclo vigente
    return Matricula.objects.filter(
        alumno=OuterRef('pk'),
        ciclo__fecha_fin__gte=today,
    )


def _base_qs(sede, today):
    """
    Query base para la lista de alumnos — incluye anotación de si tiene matrícula activa
    y carga anticipada de datos relacionados para evitar consultas extra en el loop.
    """
    return (
        Alumno.objects.filter(sede=sede)
        .annotate(tiene_matricula_activa=Exists(_sq_activa(today)))
        .select_related('distrito', 'sede', 'apoderado')
        .prefetch_related('matricula_set__ciclo')
    )


def _set_ultimo_ciclo(alumno):
    # Le agrego al alumno el nombre de su último ciclo para mostrarlo en la lista
    matriculas = sorted(
        alumno.matricula_set.all(),
        key=lambda m: m.fecha_matricula,
        reverse=True,
    )
    alumno.ultimo_ciclo_nombre = matriculas[0].ciclo.nombre if matriculas else ''


@login_required
@permiso_requerido(['admin', 'secretaria'])
def lista_alumnos(request):
    sede  = request.perfil.sede
    today = date.today()

    base = _base_qs(sede, today)

    # Lista principal: solo los activos que tienen matrícula vigente
    alumnos_qs = base.filter(estado='activo', tiene_matricula_activa=True)

    # Búsqueda por DNI desde el buscador
    dni = request.GET.get('dni')
    if dni:
        alumnos_qs = alumnos_qs.filter(dni__icontains=dni)

    # Cuento los de "otros estados" para mostrar el número en el botón
    otros_count = base.filter(
        Q(estado='inactivo') | Q(estado='bloqueado') |
        Q(estado='activo', tiene_matricula_activa=False)
    ).count()

    paginator = Paginator(alumnos_qs.order_by('apellido_paterno', 'nombres'), 10)
    alumnos   = paginator.get_page(request.GET.get('page'))

    for a in alumnos:
        a.estado_academico = 'matriculado'
        _set_ultimo_ciclo(a)

    return render(request, 'web/secretaria/alumnos/lista_alumnos.html', {
        'alumnos':      alumnos,
        'otros_count':  otros_count,
    })


@login_required
@permiso_requerido(['admin', 'secretaria'])
def lista_alumnos_otros(request):
    sede  = request.perfil.sede
    today = date.today()

    base = _base_qs(sede, today)

    # Traigo inactivos, bloqueados y activos sin matrícula vigente
    alumnos_qs = base.filter(
        Q(estado='inactivo') | Q(estado='bloqueado') |
        Q(estado='activo', tiene_matricula_activa=False)
    ).annotate(
        # Ordeno: sin matrícula primero, luego inactivos, luego bloqueados
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

    # Asigno el estado académico a cada alumno para que el template sepa qué botones mostrar
    for a in alumnos:
        if a.estado == 'bloqueado':
            a.estado_academico = 'bloqueado'
        elif a.estado == 'inactivo':
            a.estado_academico = 'inactivo'
        else:
            a.estado_academico = 'sin_matricula'
        _set_ultimo_ciclo(a)

    # Ciclos disponibles para el modal de Renovar matrícula
    ciclos_disponibles = Ciclo.objects.filter(
        sede=sede,
        fecha_fin__gte=today,
    ).order_by('fecha_inicio')

    return render(request, 'web/secretaria/alumnos/lista_alumnos_otros.html', {
        'alumnos':           alumnos,
        'ciclos_disponibles': ciclos_disponibles,
    })


@login_required
@permiso_requerido(['admin', 'secretaria'])
def desactivar_alumno(request, alumno_id):
    if request.method != 'POST':
        return redirect('lista_alumnos')

    # Me aseguro de que el alumno pertenezca a la sede de quien hace la acción
    alumno = get_object_or_404(Alumno, id=alumno_id, sede=request.perfil.sede)

    motivo     = request.POST.get('motivo',     '').strip()
    comentario = request.POST.get('comentario', '').strip()

    # Registro el motivo del bloqueo en el historial de desactivaciones
    if motivo:
        DesactivacionLog.objects.create(
            alumno=alumno,
            motivo=motivo,
            comentario=comentario,
            registrado_por=request.perfil,
        )

    # Bloqueo al alumno — no podrá matricularse en ninguna sede
    alumno.estado = 'bloqueado'
    alumno.save()
    return redirect('lista_alumnos_otros')


@login_required
@permiso_requerido(['admin', 'secretaria'])
def reactivar_alumno(request, alumno_id):
    if request.method != 'POST':
        return redirect('lista_alumnos')

    alumno = get_object_or_404(Alumno, id=alumno_id, sede=request.perfil.sede)

    # Los alumnos bloqueados no se pueden reactivar desde aquí
    # — esa decisión la toma el gerente directamente en la base de datos
    if alumno.estado == 'bloqueado':
        return redirect('lista_alumnos_otros')

    # Solo reactivo si estaba inactivo (no bloqueado)
    alumno.estado = 'activo'
    alumno.save()
    return redirect('lista_alumnos_otros')


@login_required
@permiso_requerido(['admin', 'secretaria'])
def detalle_alumno(request, alumno_id):
    # Filtro por sede para que una secretaria no pueda ver alumnos de otra sede
    alumno = get_object_or_404(
        Alumno.objects.select_related('apoderado', 'distrito', 'sede'),
        id=alumno_id,
        sede=request.perfil.sede,
    )

    # Traigo los datos opcionales de formación — pueden no existir
    formacion_academica = getattr(alumno, 'formacionacademica', None)
    formacion_adicional = getattr(alumno, 'formacionadicional', None)

    # Historial completo de matrículas y pagos del alumno
    matriculas_qs = (
        Matricula.objects.filter(alumno=alumno)
        .select_related('ciclo')
        .prefetch_related('pago_set')
        .order_by('-fecha_matricula')
    )
    matriculas_list = list(matriculas_qs)

    # Armo la lista del historial con totales calculados por matrícula
    historial = []
    for m in matriculas_list:
        historial.append({
            'matricula':    m,
            'pagos':        m.pago_set.order_by('-fecha_pago'),
            'total_pagado': m.total_pagado(),
            'deuda':        m.deuda(),
        })

    today = date.today()
    # Calculo el estado académico actual — puede auto-inactivar al alumno si lleva 2+ ciclos sin renovar
    estado_academico = _estado_academico_full(alumno, matriculas_list, today)

    return render(request, 'web/secretaria/alumnos/detalle_alumno.html', {
        'alumno':              alumno,
        'formacion_academica': formacion_academica,
        'formacion_adicional': formacion_adicional,
        'historial':           historial,
        'estado_academico':    estado_academico,
    })


@login_required
@permiso_requerido(['admin', 'secretaria'])
def editar_alumno(request, alumno_id):
    from ..models import FormacionAdicional
    alumno = get_object_or_404(
        Alumno.objects.select_related('apoderado'),
        id=alumno_id, sede=request.perfil.sede,
    )
    if request.method == 'POST':
        # Actualizo los datos personales del alumno
        alumno.apellido_paterno = request.POST.get('apellido_paterno', '').strip()
        alumno.apellido_materno = request.POST.get('apellido_materno', '').strip()
        alumno.nombres          = request.POST.get('nombres',          '').strip()
        alumno.celular          = request.POST.get('celular',          '').strip()
        alumno.email            = request.POST.get('email',            '').strip() or None
        alumno.direccion        = request.POST.get('direccion',        '').strip()
        alumno.save()

        # Si tiene apoderado, actualizo sus datos también
        if alumno.apoderado:
            apo    = alumno.apoderado
            nombre  = request.POST.get('apo_nombre',  '').strip()
            celular = request.POST.get('apo_celular', '').strip()
            dni     = request.POST.get('apo_dni',     '').strip()
            if nombre:  apo.nombre_completo = nombre
            if celular: apo.celular         = celular
            if dni:     apo.dni             = dni
            apo.save()

        # Si tiene formación adicional, actualizo las carreras de interés
        formacion = FormacionAdicional.objects.filter(alumno=alumno).first()
        if formacion:
            formacion.carrera_interes = request.POST.get('carrera_interes', '').strip()
            formacion.segunda_carrera = request.POST.get('segunda_carrera', '').strip()
            formacion.save()

        return redirect('detalle_alumno', alumno_id=alumno.id)

    # GET: el formulario de edición está en un modal dentro del detalle del alumno
    return redirect('detalle_alumno', alumno_id=alumno.id)


@login_required
@permiso_requerido(['admin', 'secretaria'])
def renovar_matricula(request, alumno_id):
    if request.method != 'POST':
        return redirect('lista_alumnos')

    # No filtro por sede aquí — esto permite que lleguen alumnos de otra sede (transferencia)
    alumno = get_object_or_404(Alumno, id=alumno_id)

    # Detecto si el alumno viene de una sede diferente a la mía
    es_transferencia = alumno.sede != request.perfil.sede

    # Un alumno bloqueado no puede renovar ni transferirse — muestro error
    if alumno.estado == 'bloqueado':
        messages.error(request, "El alumno se encuentra bloqueado y no puede matricularse.")
        return redirect('lista_alumnos_otros' if not es_transferencia else 'registrar_alumno')

    ciclo_id = request.POST.get('ciclo', '').strip()
    if not ciclo_id:
        messages.error(request, "Debe seleccionar un ciclo.")
        return redirect('lista_alumnos_otros' if not es_transferencia else 'registrar_alumno')

    # El ciclo siempre es de mi sede (la sede destino) — no del origen del alumno
    ciclo = get_object_or_404(Ciclo, id=ciclo_id, sede=request.perfil.sede)

    # Actualizo el celular y email si vinieron en el formulario (modal de renovar)
    celular = request.POST.get('celular', '').strip()
    if celular:
        alumno.celular = celular
    alumno.email = request.POST.get('email', '').strip() or None

    # Actualizo datos del apoderado si existen
    if alumno.apoderado:
        apo_nombre  = request.POST.get('apo_nombre',  '').strip()
        apo_celular = request.POST.get('apo_celular', '').strip()
        if apo_nombre:
            alumno.apoderado.nombre_completo = apo_nombre
        if apo_celular:
            alumno.apoderado.celular = apo_celular
        alumno.apoderado.save()

    # Si estaba inactivo, lo reactivo automáticamente al renovar
    if alumno.estado == 'inactivo':
        alumno.estado = 'activo'

    # Si es transferencia, cambio la sede del alumno a la sede donde está renovando
    if es_transferencia:
        alumno.sede = request.perfil.sede

    alumno.save()

    # Creo la nueva matrícula y mando directo a registrar el pago
    nueva_matricula = Matricula.objects.create(
        alumno=alumno,
        ciclo=ciclo,
        fecha_matricula=date.today(),
        estado='pendiente',
        registrado_por=request.perfil,
    )

    return redirect('pagos', matricula_id=nueva_matricula.id)
