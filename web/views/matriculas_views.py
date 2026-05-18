from django.shortcuts import render
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Value, Count
from django.db.models.functions import Coalesce
from web.permisos import permiso_requerido
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from datetime import date
from decimal import Decimal

from ..models import Matricula


def _limpiar_matriculas_huerfanas(sede):
    """Elimina matrículas sin ningún pago registrado (registros inconsistentes)."""
    Matricula.objects.filter(
        alumno__sede=sede,
        alumno__estado='activo',
    ).annotate(num_pagos=Count('pago')).filter(num_pagos=0).delete()


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


def _estado_pago(m, today):
    if m.deuda_db <= 0:
        return 'pagado'
    if m.ciclo.fecha_fin < today:
        return 'vencido'
    if m.total_pagado_db > 0:
        return 'parcial'
    return 'sin_pago'


def _ultimo_pago(m):
    pagos = sorted(m.pago_set.all(), key=lambda p: p.fecha_pago, reverse=True)
    return pagos[0] if pagos else None


@login_required
@permiso_requerido(['admin', 'secretaria'])
def matriculas(request):
    sede = request.user.perfil.sede
    today = date.today()

    _limpiar_matriculas_huerfanas(sede)

    base = _matriculas_base(sede)

    # Vista principal: solo con deuda pendiente
    pendientes_qs = base.filter(deuda_db__gt=0)

    dni = request.GET.get('dni')
    if dni:
        pendientes_qs = pendientes_qs.filter(alumno__dni__icontains=dni)

    historial_count = base.filter(deuda_db__lte=0).count()

    paginator = Paginator(pendientes_qs.order_by('-fecha_matricula'), 10)
    matriculas_page = paginator.get_page(request.GET.get('page'))

    for m in matriculas_page:
        m.estado_pago = _estado_pago(m, today)
        m.ultimo_pago = _ultimo_pago(m)

    return render(request, 'web/secretaria/matriculas/lista_matricula.html', {
        'matriculas': matriculas_page,
        'historial_count': historial_count,
    })


@login_required
@permiso_requerido(['admin', 'secretaria'])
def matriculas_historial(request):
    sede = request.user.perfil.sede

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
