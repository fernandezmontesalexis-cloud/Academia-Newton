from django.shortcuts import render
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Value, Count, Case, When, IntegerField
from django.db.models.functions import Coalesce
from web.permisos import permiso_requerido
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from datetime import date, timedelta, datetime
from decimal import Decimal

from ..models import Matricula, Alumno
from ..utils import estado_pago_matricula

# ── Limpieza de matrículas "huérfanas" ────────────────────────────────────────
# Una matrícula huérfana es la que se creó durante el registro de un alumno pero
# nadie hizo ningún pago — por ejemplo si el navegador se cerró antes de tiempo.
# Esta limpieza actúa como red de seguridad para esos casos.

_LIMPIEZA_INTERVALO_SEGUNDOS = 600  # 10 minutos — no quiero que esto corra en cada clic


def _limpiar_matriculas_huerfanas(sede):
    """
    Busca y elimina matrículas sin ningún pago registrado.
    También elimina el alumno si quedó sin ninguna matrícula después de la limpieza.
    Todo se hace con queries a la base de datos — sin cargar objetos en memoria.
    """
    # Primero consigo los IDs de los alumnos que tienen matrículas sin pagos
    # — los guardo antes de borrar para poder revisar si quedaron sin matrícula
    alumnos_ids = list(
        Matricula.objects.filter(
            alumno__sede=sede,
            alumno__estado='activo',
        ).annotate(num_pagos=Count('pago'))
        .filter(num_pagos=0)
        .values_list('alumno_id', flat=True)
    )

    # Si no hay nada que limpiar, salgo rápido para no hacer trabajo innecesario
    if not alumnos_ids:
        return

    # Elimino las matrículas que no tienen ningún pago
    Matricula.objects.filter(
        alumno__sede=sede,
        alumno__estado='activo',
    ).annotate(num_pagos=Count('pago')).filter(num_pagos=0).delete()

    # Elimino los alumnos que quedaron completamente sin matrículas
    # (eran alumnos recién registrados que nunca completaron el proceso)
    Alumno.objects.filter(
        id__in=alumnos_ids,
    ).annotate(num_matriculas=Count('matricula')).filter(num_matriculas=0).delete()


def _limpiar_si_necesario(request, sede):
    """
    Controla que la limpieza no se ejecute en cada vez que alguien carga la página.
    La corro máximo una vez cada 10 minutos por usuario — usando la sesión para llevar el control.
    """
    clave  = f'ultimo_limpiado_{sede.id}'
    ahora  = datetime.now().timestamp()
    ultimo = request.session.get(clave, 0)

    if ahora - ultimo >= _LIMPIEZA_INTERVALO_SEGUNDOS:
        _limpiar_matriculas_huerfanas(sede)
        request.session[clave] = ahora  # anoto la hora en que corrió


def _matriculas_base(sede):
    """
    Query base que uso para traer matrículas — la reutilizo en varias vistas.
    Le agrego anotaciones de deuda y total pagado directamente en la base de datos
    para no tener que calcularlos uno por uno en Python (evita el problema N+1).
    """
    return (
        Matricula.objects
        .filter(alumno__sede=sede, alumno__estado='activo')
        .select_related(
            'alumno', 'alumno__sede', 'alumno__apoderado',
            'ciclo', 'registrado_por__user',
        )
        .prefetch_related('pago_set')
        .annotate(
            # Sumo todos los pagos de esta matrícula directamente en la BD
            total_pagado_db=Coalesce(
                Sum('pago__monto'), Value(Decimal('0')),
                output_field=DecimalField(),
            )
        )
        .annotate(
            # La deuda es el precio del ciclo menos lo que ya se pagó
            deuda_db=ExpressionWrapper(
                F('ciclo__precio') - F('total_pagado_db'),
                output_field=DecimalField(),
            )
        )
    )


def _ultimo_pago(m):
    # Devuelvo el pago más reciente de una matrícula — lo uso para mostrar la última fecha de pago
    pagos = sorted(m.pago_set.all(), key=lambda p: p.fecha_pago, reverse=True)
    return pagos[0] if pagos else None


@login_required
@permiso_requerido(['admin', 'secretaria'])
def matriculas(request):
    sede  = request.perfil.sede
    today = date.today()

    # Aprovecho la carga de la página de matrículas para limpiar huérfanas
    # (throttled — máximo 1 vez cada 10 min para no afectar la velocidad)
    _limpiar_si_necesario(request, sede)

    base = _matriculas_base(sede)

    # Vista principal: solo muestro las que tienen deuda pendiente
    pendientes_qs = base.filter(deuda_db__gt=0)

    # Filtro por DNI si la secretaria lo escribe en el buscador
    dni = request.GET.get('dni')
    if dni:
        pendientes_qs = pendientes_qs.filter(alumno__dni__icontains=dni)

    # Cuento las pagadas para mostrar el número en el botón de "Historial"
    historial_count = base.filter(deuda_db__lte=0).count()

    # Ordeno por urgencia: vencidas primero, luego las que vencen en 7 días, luego el resto
    pendientes_qs = pendientes_qs.annotate(
        orden_pago=Case(
            When(proximo_pago__lt=today, then=0),                           # ya venció
            When(proximo_pago__lte=today + timedelta(days=7), then=1),      # vence esta semana
            default=2,                                                       # fecha futura
            output_field=IntegerField(),
        )
    )

    paginator     = Paginator(pendientes_qs.order_by('orden_pago', 'proximo_pago'), 10)
    matriculas_page = paginator.get_page(request.GET.get('page'))

    # Calculo el estado de pago de cada matrícula para mostrarlo en la tabla
    for m in matriculas_page:
        m.estado_pago = estado_pago_matricula(m, today)
        m.ultimo_pago = _ultimo_pago(m)

    return render(request, 'web/secretaria/matriculas/lista_matricula.html', {
        'matriculas':     matriculas_page,
        'historial_count': historial_count,
    })


@login_required
@permiso_requerido(['admin', 'secretaria'])
def matriculas_historial(request):
    sede = request.perfil.sede

    base = _matriculas_base(sede)
    # El historial son las matrículas que ya están completamente pagadas (deuda = 0)
    pagados_qs = base.filter(deuda_db__lte=0)

    dni = request.GET.get('dni')
    if dni:
        pagados_qs = pagados_qs.filter(alumno__dni__icontains=dni)

    # Muestro las más recientes primero
    paginator     = Paginator(pagados_qs.order_by('-fecha_matricula'), 10)
    matriculas_page = paginator.get_page(request.GET.get('page'))

    return render(request, 'web/secretaria/matriculas/matriculas_historial.html', {
        'matriculas': matriculas_page,
    })
