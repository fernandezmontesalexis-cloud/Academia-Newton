import json
from datetime import date
from decimal import Decimal

from django.shortcuts import render, get_object_or_404
from web.permisos import permiso_requerido
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, DecimalField, Value
from django.db.models.functions import Coalesce, ExtractYear, ExtractMonth

from ..models import Sede, Alumno, Matricula, Pago, Ciclo


def _salud_badge(pct):
    """Devuelve etiqueta, clase Bootstrap y color hex según % de recaudación."""
    if pct >= 75:
        return {'label': 'Saludable',    'clase': 'success', 'color': '#198754'}
    if pct >= 50:
        return {'label': 'Riesgo medio', 'clase': 'warning', 'color': '#ffc107'}
    return     {'label': 'Alta deuda',   'clase': 'danger',  'color': '#dc3545'}


def _ingresos_6_meses(sede=None):
    """
    Calcula ingresos de los últimos 6 meses en 1 sola query
    (antes hacía 6 queries separadas, una por mes).
    """
    hoy = date.today()

    # Calcular el primer día del período (hace 5 meses)
    mes_inicio = hoy.month - 5
    año_inicio = hoy.year
    while mes_inicio <= 0:
        mes_inicio += 12
        año_inicio -= 1
    inicio_periodo = date(año_inicio, mes_inicio, 1)

    # 1 sola query agrupada por año + mes
    qs = Pago.objects.filter(fecha_pago__gte=inicio_periodo)
    if sede is not None:
        qs = qs.filter(matricula__alumno__sede=sede)

    resultados = (
        qs
        .annotate(año=ExtractYear('fecha_pago'), mes=ExtractMonth('fecha_pago'))
        .values('año', 'mes')
        .annotate(total=Sum('monto'))
    )
    mapa = {(r['año'], r['mes']): float(r['total'] or 0) for r in resultados}

    # Construir labels y data en orden cronológico
    labels = []
    data = []
    for i in range(5, -1, -1):
        m = hoy.month - i
        a = hoy.year
        while m <= 0:
            m += 12
            a -= 1
        labels.append(date(a, m, 1).strftime('%b %Y'))
        data.append(mapa.get((a, m), 0.0))

    return labels, data


@login_required
@permiso_requerido(['admin'])
def reportes_sedes(request):
    from collections import defaultdict

    sedes = list(Sede.objects.all())

    # ── Ganancias anuales ─────────────────────────────────────────────────
    pagos_anuales = (
        Pago.objects
        .annotate(año=ExtractYear('fecha_pago'))
        .values('año', 'matricula__alumno__sede_id')
        .annotate(total=Sum('monto'))
        .order_by('año')
    )

    matriz = defaultdict(dict)
    for row in pagos_anuales:
        matriz[row['año']][row['matricula__alumno__sede_id']] = float(row['total'] or 0)

    años_list   = sorted(matriz.keys())[-4:]   # máximo últimos 4 años
    anual_rows  = []
    prev_total  = None
    for año in años_list:
        totales   = [round(matriz[año].get(s.id, 0), 2) for s in sedes]
        total_año = round(sum(totales), 2)
        if prev_total is not None and prev_total > 0:
            crecimiento      = round((total_año - prev_total) / prev_total * 100, 1)
            tiene_crecimiento = True
        else:
            crecimiento       = 0
            tiene_crecimiento = False
        anual_rows.append({
            'año':              año,
            'totales':          totales,
            # Lista de (nombre_sede, monto) para iterar en template sin indexado
            'sede_totales':     list(zip([s.nombre for s in sedes], totales)),
            'total':            total_año,
            'crecimiento':      crecimiento,
            'tiene_crecimiento': tiene_crecimiento,
            'positivo':         crecimiento >= 0,
        })
        prev_total = total_año

    # ── Comparativo de sedes ──────────────────────────────────────────────
    data_sedes = []

    for sede in sedes:
        alumnos_activos       = Alumno.objects.filter(sede=sede, estado='activo').count()
        matriculas_qs         = Matricula.objects.filter(alumno__sede=sede)
        matriculas_pagadas    = matriculas_qs.filter(estado='pagado').count()
        matriculas_pendientes = matriculas_qs.filter(estado='pendiente').count()

        ingresos = (
            Pago.objects.filter(matricula__alumno__sede=sede)
            .aggregate(total=Sum('monto'))['total'] or 0
        )
        deuda = sum(
            m.deuda() for m in
            matriculas_qs.filter(estado='pendiente')
            .select_related('ciclo').prefetch_related('pago_set')
        )

        # Datos gráfico 1: ingresos mensuales
        mensual_labels, mensual_data = _ingresos_6_meses(sede=sede)

        # Datos gráfico 3: esperado vs cobrado por ciclo
        ciclos = list(
            Matricula.objects.filter(alumno__sede=sede)
            .values('ciclo__id', 'ciclo__nombre', 'ciclo__precio')
            .annotate(total_mats=Count('id'))
            .order_by('ciclo__fecha_inicio')
        )
        bar_labels, bar_esperado, bar_cobrado = [], [], []
        for c in ciclos:
            bar_labels.append(c['ciclo__nombre'])
            esperado = float(c['ciclo__precio']) * c['total_mats']
            cobrado  = float(
                Pago.objects.filter(
                    matricula__ciclo_id=c['ciclo__id'],
                    matricula__alumno__sede=sede,
                ).aggregate(t=Sum('monto'))['t'] or 0
            )
            bar_esperado.append(round(esperado, 2))
            bar_cobrado.append(round(cobrado, 2))

        total_esperado = sum(bar_esperado)
        ingresos_f     = round(float(ingresos), 2)
        pct            = int(ingresos_f / total_esperado * 100) if total_esperado > 0 else 0

        data_sedes.append({
            'sede':                   sede,
            'alumnos_activos':        alumnos_activos,
            'total_matriculas':       matriculas_qs.count(),
            'ingresos':               ingresos_f,
            'deuda':                  round(float(deuda), 2),
            'pct_recaudado':          min(pct, 100),
            'salud':                  _salud_badge(pct),
            # Para gráficos modales
            'chart_mensual_labels':   json.dumps(mensual_labels),
            'chart_mensual_data':     json.dumps(mensual_data),
            'chart_estado_data':      json.dumps([matriculas_pagadas, matriculas_pendientes]),
            'chart_bar_labels':       json.dumps(bar_labels),
            'chart_bar_esperado':     json.dumps(bar_esperado),
            'chart_bar_cobrado':      json.dumps(bar_cobrado),
        })

    return render(request, 'web/administrador/reportes/reportes_sedes.html', {
        'data_sedes':  data_sedes,
        'anual_rows':  anual_rows,
        'sedes':       sedes,
    })


@login_required
@permiso_requerido(['admin'])
def reporte_sede_detalle(request, sede_id):
    sede = get_object_or_404(Sede, id=sede_id)

    alumnos_activos = Alumno.objects.filter(sede=sede, estado='activo').count()
    matriculas_qs   = Matricula.objects.filter(alumno__sede=sede)

    ingresos_total = round(float(
        Pago.objects.filter(matricula__alumno__sede=sede)
        .aggregate(total=Sum('monto'))['total'] or 0
    ), 2)
    deuda_total = round(float(sum(
        m.deuda() for m in
        matriculas_qs.filter(estado='pendiente')
        .select_related('ciclo').prefetch_related('pago_set')
    )), 2)

    # Cards de ciclos — igual que secretaria en Reportes Financieros
    ciclos_raw  = Ciclo.objects.filter(sede=sede).order_by('-fecha_inicio')
    ciclos_data = []

    for c in ciclos_raw:
        total_matriculas = Matricula.objects.filter(
            ciclo=c, alumno__estado='activo', alumno__sede=sede,
        ).count()
        if total_matriculas == 0:
            continue

        total_recaudado = (
            Pago.objects.filter(
                matricula__ciclo=c,
                matricula__alumno__estado='activo',
                matricula__alumno__sede=sede,
            ).aggregate(t=Sum('monto'))['t'] or Decimal('0')
        )
        total_esperado = c.precio * total_matriculas
        total_deuda    = max(total_esperado - total_recaudado, Decimal('0'))

        alumnos_con_deuda = (
            Matricula.objects
            .filter(ciclo=c, alumno__estado='activo', alumno__sede=sede)
            .annotate(
                pagado_m=Coalesce(
                    Sum('pago__monto'), Value(Decimal('0')),
                    output_field=DecimalField(),
                )
            )
            .filter(pagado_m__lt=c.precio)
            .count()
        )

        pct = int(total_recaudado / total_esperado * 100) if total_esperado > 0 else 0

        ciclos_data.append({
            'ciclo':             c,
            'total_matriculas':  total_matriculas,
            'total_recaudado':   total_recaudado,
            'total_esperado':    total_esperado,
            'total_deuda':       total_deuda,
            'alumnos_con_deuda': alumnos_con_deuda,
            'pct_recaudado':     min(pct, 100),
        })

    # Badge de salud global de la sede
    total_esperado_sede = sum(float(item['total_esperado']) for item in ciclos_data)
    pct_sede = int(ingresos_total / total_esperado_sede * 100) if total_esperado_sede > 0 else 0

    return render(request, 'web/administrador/reportes/reporte_sede_detalle.html', {
        'sede':             sede,
        'alumnos_activos':  alumnos_activos,
        'total_matriculas': matriculas_qs.count(),
        'ingresos_total':   ingresos_total,
        'deuda_total':      deuda_total,
        'ciclos_data':      ciclos_data,
        'salud':            _salud_badge(pct_sede),
        'pct_recaudado':    min(pct_sede, 100),
    })


