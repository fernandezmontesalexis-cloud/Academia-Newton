import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from datetime import date, timedelta

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, Count
from django.core.paginator import Paginator

from web.permisos import permiso_requerido
from ..models import Alumno, Matricula, Pago, Sede


_METODO_MAP = {
    'efectivo':      'Efectivo',
    'yape':          'Yape',
    'transferencia': 'Transferencia',
}


def _build_page_range(page_obj, window=2):
    total = page_obj.paginator.num_pages
    if total <= 7:
        return list(range(1, total + 1))
    current = page_obj.number
    result, last_added = [], None
    for i in range(1, total + 1):
        if i == 1 or i == total or abs(i - current) <= window:
            if last_added is not None and i - last_added > 1:
                result.append(None)
            result.append(i)
            last_added = i
    return result


def _filtrar_historial(request):
    fecha_desde_str = request.GET.get('fecha_desde', '')
    fecha_hasta_str = request.GET.get('fecha_hasta', '')
    sede_id         = request.GET.get('sede_id', '')
    metodo          = request.GET.get('metodo', '')
    busqueda        = request.GET.get('q', '').strip()

    qs = Pago.objects.select_related(
        'matricula__alumno',
        'matricula__alumno__sede',
        'matricula__ciclo',
    )
    if fecha_desde_str:
        try:
            qs = qs.filter(fecha_pago__gte=date.fromisoformat(fecha_desde_str))
        except ValueError:
            pass
    if fecha_hasta_str:
        try:
            qs = qs.filter(fecha_pago__lte=date.fromisoformat(fecha_hasta_str))
        except ValueError:
            pass
    if sede_id:
        qs = qs.filter(matricula__alumno__sede_id=sede_id)
    if metodo:
        qs = qs.filter(metodo_pago=metodo)
    if busqueda:
        qs = (
            qs.filter(matricula__alumno__nombres__icontains=busqueda) |
            qs.filter(matricula__alumno__apellido_paterno__icontains=busqueda)
        )

    params = request.GET.copy()
    params.pop('page', None)
    qs_str = params.urlencode()

    filtros = {
        'fecha_desde_str': fecha_desde_str,
        'fecha_hasta_str': fecha_hasta_str,
        'sede_id':         sede_id,
        'metodo':          metodo,
        'busqueda':        busqueda,
        'filtros_activos': bool(fecha_desde_str or fecha_hasta_str or sede_id or metodo or busqueda),
        'base_url':        f'?{qs_str}&' if qs_str else '?',
    }
    return qs.order_by('-fecha_pago', '-id'), filtros


@login_required
@permiso_requerido(['admin'])
def finanzas(request):
    hoy        = date.today()
    mes_inicio = hoy.replace(day=1)
    sem_inicio = hoy - timedelta(days=6)

    # ── KPIs ──────────────────────────────────────────────────────────────
    ingresos_hoy = (
        Pago.objects.filter(fecha_pago=hoy)
        .aggregate(t=Sum('monto'))['t'] or 0
    )
    ingresos_mes = (
        Pago.objects.filter(fecha_pago__gte=mes_inicio)
        .aggregate(t=Sum('monto'))['t'] or 0
    )
    alumnos_con_deuda = (
        Alumno.objects.filter(matricula__estado='pendiente')
        .distinct().count()
    )
    deuda_total = sum(
        m.deuda()
        for m in Matricula.objects.filter(estado='pendiente')
                                  .select_related('ciclo')
                                  .prefetch_related('pago_set')
    )

    # ── Resumen Financiero ────────────────────────────────────────────────
    total_semana = (
        Pago.objects.filter(fecha_pago__gte=sem_inicio)
        .aggregate(t=Sum('monto'))['t'] or 0
    )
    promedio_raw = Pago.objects.aggregate(avg=Avg('monto'))['avg'] or 0
    promedio_pago = round(float(promedio_raw), 2)

    metodo_result = (
        Pago.objects.values('metodo_pago')
        .annotate(cnt=Count('id'))
        .order_by('-cnt')
        .first()
    )
    metodo_mas_usado = metodo_result['metodo_pago'] if metodo_result else ''
    metodo_label     = _METODO_MAP.get(metodo_mas_usado, '—')

    ultimo_pago           = Pago.objects.order_by('-fecha_pago', '-id').first()
    ultima_actualizacion  = ultimo_pago.fecha_pago if ultimo_pago else None

    # ── Historial filtrado y paginado ──────────────────────────────────────
    historial_qs, filtros = _filtrar_historial(request)
    historial = Paginator(historial_qs, 10).get_page(request.GET.get('page'))

    # ── Gráfico: ingresos últimos 7 días ──────────────────────────────────
    chart_7d_labels, chart_7d_data = [], []
    for i in range(6, -1, -1):
        dia   = hoy - timedelta(days=i)
        total = (
            Pago.objects.filter(fecha_pago=dia)
            .aggregate(t=Sum('monto'))['t'] or 0
        )
        chart_7d_labels.append(dia.strftime('%d/%m'))
        chart_7d_data.append(float(total))

    return render(request, 'web/administrador/finanzas/finanzas.html', {
        # KPIs
        'ingresos_hoy':       ingresos_hoy,
        'ingresos_mes':       ingresos_mes,
        'deuda_total':        deuda_total,
        'alumnos_con_deuda':  alumnos_con_deuda,
        # Resumen
        'total_semana':         total_semana,
        'promedio_pago':        promedio_pago,
        'metodo_mas_usado':     metodo_mas_usado,
        'metodo_label':         metodo_label,
        'ultima_actualizacion': ultima_actualizacion,
        # Historial
        'historial':  historial,
        'page_range': _build_page_range(historial),
        'sedes':      list(Sede.objects.all()),
        # Gráfico
        'chart_7d_labels': json.dumps(chart_7d_labels),
        'chart_7d_data':   json.dumps(chart_7d_data),
        **filtros,
    })


@login_required
@permiso_requerido(['admin'])
def exportar_finanzas_excel(request):
    historial_qs, _ = _filtrar_historial(request)
    pagos = historial_qs.select_related('registrado_por__user')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Movimientos Financieros"

    # ── Estilos de cabecera ────────────────────────────────────────────────
    hdr_fill = PatternFill("solid", fgColor="1B5E20")   # verde oscuro (≠ azul de Reportes)
    hdr_font = Font(bold=True, color="FFFFFF", size=10)
    center   = Alignment(horizontal='center', vertical='center')
    left_al  = Alignment(horizontal='left',   vertical='center')

    # Columna → (título, ancho fijo)
    cols = [
        ('N°',             6),
        ('Alumno',        28),
        ('DNI',           12),
        ('Sede',          16),
        ('Ciclo',         22),
        ('Monto Pagado',  14),
        ('Método',        14),
        ('Fecha',         13),
        ('Estado',        12),
        ('Deuda Restante',14),
        ('Registrado por',18),
    ]
    ws.row_dimensions[1].height = 22
    for col, (title, width) in enumerate(cols, 1):
        cell = ws.cell(row=1, column=col, value=title)
        cell.font      = hdr_font
        cell.fill      = hdr_fill
        cell.alignment = center
        ws.column_dimensions[get_column_letter(col)].width = width

    # ── Estilos de datos ──────────────────────────────────────────────────
    fill_alt   = PatternFill("solid", fgColor="F5F5F5")  # zebra par
    fill_comp  = PatternFill("solid", fgColor="E8F5E9")  # verde claro → Completo
    fill_parc  = PatternFill("solid", fgColor="FFF3E0")  # naranja claro → Parcial
    font_base  = Font(size=9)
    font_money = Font(size=9, color="1B5E20", bold=True)
    font_deuda = Font(size=9, color="B71C1C", bold=True)
    font_parc  = Font(size=9, color="E65100", bold=True)
    curr_fmt   = '"S/. "#,##0.00'

    for row_num, pago in enumerate(pagos, 2):
        alumno    = pago.matricula.alumno
        matricula = pago.matricula
        estado    = 'Completo' if matricula.estado == 'pagado' else 'Parcial'
        deuda     = float(matricula.deuda())
        usuario   = pago.registrado_por.user.username if pago.registrado_por else '—'
        is_even   = (row_num % 2 == 0)
        ws.row_dimensions[row_num].height = 15

        filas_data = [
            (row_num - 1,                          center,  font_base,  None),
            (str(alumno),                          left_al, font_base,  None),
            (alumno.dni,                           center,  font_base,  None),
            (str(alumno.sede),                     left_al, font_base,  None),
            (matricula.ciclo.nombre,               left_al, font_base,  None),
            (float(pago.monto),                    center,  font_money, curr_fmt),
            (pago.get_metodo_pago_display(),       center,  font_base,  None),
            (pago.fecha_pago.strftime('%d/%m/%Y'), center,  font_base,  None),
            (estado,                               center,  font_base,  None),
            (deuda,                                center,  font_deuda if deuda > 0 else font_base, curr_fmt),
            (usuario,                              center,  font_base,  None),
        ]

        estado_fill = fill_comp if estado == 'Completo' else fill_parc

        for col, (value, align, font, fmt) in enumerate(filas_data, 1):
            cell = ws.cell(row=row_num, column=col, value=value)
            cell.font      = font
            cell.alignment = align
            if col == 9:
                cell.fill = estado_fill
                if estado == 'Parcial':
                    cell.font = font_parc
            elif is_even:
                cell.fill = fill_alt
            if fmt:
                cell.number_format = fmt

    ws.freeze_panes = 'A2'

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="finanzas_movimientos.xlsx"'
    wb.save(response)
    return response


@login_required
@permiso_requerido(['admin'])
def historial_completo(request):
    historial_qs, filtros = _filtrar_historial(request)
    historial = Paginator(historial_qs, 10).get_page(request.GET.get('page'))

    return render(request, 'web/administrador/finanzas/historial_completo.html', {
        'historial':  historial,
        'page_range': _build_page_range(historial),
        'sedes':      list(Sede.objects.all()),
        **filtros,
    })
