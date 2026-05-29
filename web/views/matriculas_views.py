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

# ── Limpieza de matrículas huérfanas ─────────────────────────────────────────
# Cubre el caso donde el navegador se cierra inesperadamente (crash, corte de
# luz/internet, cierre forzado de pestaña) antes de que el JS pueda llamar a
# cancelar_matricula_nueva. La función en sí es eficiente (ORM puro); el
# throttle evita que corra en CADA page load con cientos de matrículas.

_LIMPIEZA_INTERVALO_SEGUNDOS = 600  # 10 minutos


def _limpiar_matriculas_huerfanas(sede):
    """
    Elimina matrículas sin ningún pago y alumnos que queden sin matrícula.
    Usa ORM puro — no carga objetos en memoria.
    """
    # Paso 1: IDs de alumnos afectados (antes de borrar para step 3)
    alumnos_ids = list(
        Matricula.objects.filter(
            alumno__sede=sede,
            alumno__estado='activo',
        ).annotate(num_pagos=Count('pago'))
        .filter(num_pagos=0)
        .values_list('alumno_id', flat=True)
    )

    if not alumnos_ids:
        return  # nada que limpiar — evita los DELETEs innecesarios

    # Paso 2: eliminar las matrículas huérfanas
    Matricula.objects.filter(
        alumno__sede=sede,
        alumno__estado='activo',
    ).annotate(num_pagos=Count('pago')).filter(num_pagos=0).delete()

    # Paso 3: eliminar alumnos que quedaron sin ninguna matrícula
    Alumno.objects.filter(
        id__in=alumnos_ids,
    ).annotate(num_matriculas=Count('matricula')).filter(num_matriculas=0).delete()


def _limpiar_si_necesario(request, sede):
    """
    Ejecuta _limpiar_matriculas_huerfanas como máximo una vez cada
    _LIMPIEZA_INTERVALO_SEGUNDOS por sesión de usuario.

    Con muchos alumnos, esto garantiza que la limpieza no se dispara en
    cada page load — solo cuando el intervalo ha expirado.
    """
    clave = f'ultimo_limpiado_{sede.id}'
    ahora = datetime.now().timestamp()
    ultimo = request.session.get(clave, 0)

    if ahora - ultimo >= _LIMPIEZA_INTERVALO_SEGUNDOS:
        _limpiar_matriculas_huerfanas(sede)
        request.session[clave] = ahora


def _matriculas_base(sede):
    return (
        Matricula.objects
        .filter(alumno__sede=sede, alumno__estado='activo')
        .select_related(
            'alumno', 'alumno__sede', 'alumno__apoderado',
            'ciclo', 'registrado_por__user',
        )
        .prefetch_related('pago_set')
        .annotate(
            total_pagado_db=Coalesce(
                Sum('pago__monto'), Value(Decimal('0')),
                output_field=DecimalField(),
            )
        )
        .annotate(
            deuda_db=ExpressionWrapper(
                F('ciclo__precio') - F('total_pagado_db'),
                output_field=DecimalField(),
            )
        )
    )


def _ultimo_pago(m):
    pagos = sorted(m.pago_set.all(), key=lambda p: p.fecha_pago, reverse=True)
    return pagos[0] if pagos else None


@login_required
@permiso_requerido(['admin', 'secretaria'])
def matriculas(request):
    sede = request.perfil.sede
    today = date.today()

    _limpiar_si_necesario(request, sede)

    base = _matriculas_base(sede)

    # Vista principal: solo con deuda pendiente
    pendientes_qs = base.filter(deuda_db__gt=0)

    dni = request.GET.get('dni')
    if dni:
        pendientes_qs = pendientes_qs.filter(alumno__dni__icontains=dni)

    historial_count = base.filter(deuda_db__lte=0).count()

    pendientes_qs = pendientes_qs.annotate(
        orden_pago=Case(
            When(proximo_pago__lt=today, then=0),
            When(proximo_pago__lte=today + timedelta(days=7), then=1),
            default=2,
            output_field=IntegerField(),
        )
    )

    paginator = Paginator(pendientes_qs.order_by('orden_pago', 'proximo_pago'), 10)
    matriculas_page = paginator.get_page(request.GET.get('page'))

    for m in matriculas_page:
        m.estado_pago = estado_pago_matricula(m, today)
        m.ultimo_pago = _ultimo_pago(m)

    return render(request, 'web/secretaria/matriculas/lista_matricula.html', {
        'matriculas': matriculas_page,
        'historial_count': historial_count,
    })


@login_required
@permiso_requerido(['admin', 'secretaria'])
def matriculas_historial(request):
    sede = request.perfil.sede

    base = _matriculas_base(sede)
    pagados_qs = base.filter(deuda_db__lte=0)

    dni = request.GET.get('dni')
    if dni:
        pagados_qs = pagados_qs.filter(alumno__dni__icontains=dni)

    paginator = Paginator(pagados_qs.order_by('-fecha_matricula'), 10)
    matriculas_page = paginator.get_page(request.GET.get('page'))

    return render(request, 'web/secretaria/matriculas/matriculas_historial.html', {
        'matriculas': matriculas_page,
    })
