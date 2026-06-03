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
    """
    Devuelve la etiqueta de salud financiera según el porcentaje recaudado.
    - 75% o más → Saludable (verde)
    - Entre 50% y 74% → Riesgo medio (amarillo)
    - Menos del 50% → Alta deuda (rojo)
    """
    if pct >= 75:
        return {'label': 'Saludable',    'clase': 'success', 'color': '#198754'}
    if pct >= 50:
        return {'label': 'Riesgo medio', 'clase': 'warning', 'color': '#ffc107'}
    return     {'label': 'Alta deuda',   'clase': 'danger',  'color': '#dc3545'}


def _ingresos_6_meses(sede=None):
    """
    Calcula los ingresos de los últimos 6 meses usando 1 sola consulta a la base de datos.
    Antes esto hacía 6 consultas separadas — una por mes — lo optimicé para que sea más rápido.
    """
    hoy = date.today()

    # Calculo el mes donde empieza el período de 6 meses
    mes_inicio = hoy.month - 5
    año_inicio = hoy.year
    while mes_inicio <= 0:
        mes_inicio += 12
        año_inicio -= 1
    inicio_periodo = date(año_inicio, mes_inicio, 1)

    # Traigo todos los pagos del período y los agrupo por año y mes en la BD
    qs = Pago.objects.filter(fecha_pago__gte=inicio_periodo)
    if sede is not None:
        qs = qs.filter(matricula__alumno__sede=sede)

    resultados = (
        qs
        .annotate(año=ExtractYear('fecha_pago'), mes=ExtractMonth('fecha_pago'))
        .values('año', 'mes')
        .annotate(total=Sum('monto'))
    )
    # Convierto los resultados en un diccionario para búsqueda rápida por (año, mes)
    mapa = {(r['año'], r['mes']): float(r['total'] or 0) for r in resultados}

    # Construyo las listas en orden cronológico — si un mes no tuvo pagos pongo 0
    labels = []
    data   = []
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

    # ── Sección 1: Ganancias anuales ──────────────────────────────────────
    # Traigo todos los pagos agrupados por año y sede en una sola query
    pagos_anuales = (
        Pago.objects
        .annotate(año=ExtractYear('fecha_pago'))
        .values('año', 'matricula__alumno__sede_id')
        .annotate(total=Sum('monto'))
        .order_by('año')
    )

    # Armo una matriz: matriz[año][sede_id] = total recaudado
    matriz = defaultdict(dict)
    for row in pagos_anuales:
        matriz[row['año']][row['matricula__alumno__sede_id']] = float(row['total'] or 0)

    # Solo muestro los últimos 4 años
    años_list  = sorted(matriz.keys())[-4:]
    anual_rows = []
    prev_total = None
    for año in años_list:
        totales   = [round(matriz[año].get(s.id, 0), 2) for s in sedes]
        total_año = round(sum(totales), 2)
        # Calculo el % de crecimiento o caída respecto al año anterior
        if prev_total is not None and prev_total > 0:
            crecimiento      = round((total_año - prev_total) / prev_total * 100, 1)
            tiene_crecimiento = True
        else:
            crecimiento       = 0
            tiene_crecimiento = False
        anual_rows.append({
            'año':              año,
            'totales':          totales,
            'sede_totales':     list(zip([s.nombre for s in sedes], totales)),
            'total':            total_año,
            'crecimiento':      crecimiento,
            'tiene_crecimiento': tiene_crecimiento,
            'positivo':         crecimiento >= 0,
        })
        prev_total = total_año

    # ── Sección 2: Comparativo de sedes ──────────────────────────────────
    # Armo una card por cada sede con sus métricas y datos para los gráficos modales
    data_sedes = []

    for sede in sedes:
        alumnos_activos       = Alumno.objects.filter(sede=sede, estado='activo').count()
        matriculas_qs         = Matricula.objects.filter(alumno__sede=sede)
        matriculas_pagadas    = matriculas_qs.filter(estado='pagado').count()
        matriculas_pendientes = matriculas_qs.filter(estado='pendiente').count()

        # Total recaudado histórico de la sede
        ingresos = (
            Pago.objects.filter(matricula__alumno__sede=sede)
            .aggregate(total=Sum('monto'))['total'] or 0
        )

        # Deuda total: recorro las matrículas pendientes y sumo lo que falta cobrar
        deuda = sum(
            m.deuda() for m in
            matriculas_qs.filter(estado='pendiente')
            .select_related('ciclo').prefetch_related('pago_set')
        )

        # Datos para el gráfico 1 del modal: ingresos mensuales últimos 6 meses
        mensual_labels, mensual_data = _ingresos_6_meses(sede=sede)

        # Datos para el gráfico 3 del modal: esperado vs cobrado por cada ciclo
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

        # Calculo el % recaudado para el badge de salud financiera
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
            # Datos JSON para los gráficos en los modales
            'chart_mensual_labels':   json.dumps(mensual_labels),
            'chart_mensual_data':     json.dumps(mensual_data),
            'chart_estado_data':      json.dumps([matriculas_pagadas, matriculas_pendientes]),
            'chart_bar_labels':       json.dumps(bar_labels),
            'chart_bar_esperado':     json.dumps(bar_esperado),
            'chart_bar_cobrado':      json.dumps(bar_cobrado),
        })

    return render(request, 'web/administrador/reportes/reportes_sedes.html', {
        'data_sedes': data_sedes,
        'anual_rows': anual_rows,
        'sedes':      sedes,
    })


@login_required
@permiso_requerido(['admin'])
def reporte_sede_detalle(request, sede_id):
    sede = get_object_or_404(Sede, id=sede_id)

    alumnos_activos = Alumno.objects.filter(sede=sede, estado='activo').count()
    matriculas_qs   = Matricula.objects.filter(alumno__sede=sede)

    # Ingresos y deuda total de la sede
    ingresos_total = round(float(
        Pago.objects.filter(matricula__alumno__sede=sede)
        .aggregate(total=Sum('monto'))['total'] or 0
    ), 2)
    deuda_total = round(float(sum(
        m.deuda() for m in
        matriculas_qs.filter(estado='pendiente')
        .select_related('ciclo').prefetch_related('pago_set')
    )), 2)

    # Cards de ciclos — mismo formato que los reportes financieros de la secretaria
    ciclos_raw  = Ciclo.objects.filter(sede=sede).order_by('-fecha_inicio')
    ciclos_data = []

    for c in ciclos_raw:
        total_matriculas = Matricula.objects.filter(
            ciclo=c, alumno__estado='activo', alumno__sede=sede,
        ).count()
        # Si el ciclo no tiene alumnos activos, no lo muestro
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

        # Cuento cuántos alumnos del ciclo aún tienen deuda
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

    # Badge de salud global de la sede basado en el % total recaudado vs esperado
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
