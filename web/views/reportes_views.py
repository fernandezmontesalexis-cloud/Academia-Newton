import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import date

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from web.permisos import permiso_requerido
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count

from ..models import Sede, Alumno, Matricula, Pago


def _ingresos_6_meses(sede=None):
    """Calcula ingresos de los últimos 6 meses. Si sede es None, calcula globales."""
    hoy = date.today()
    labels = []
    data = []
    for i in range(5, -1, -1):
        mes = hoy.month - i
        año = hoy.year
        while mes <= 0:
            mes += 12
            año -= 1
        inicio = date(año, mes, 1)
        fin = date(año + 1, 1, 1) if mes == 12 else date(año, mes + 1, 1)
        qs = Pago.objects.filter(fecha_pago__gte=inicio, fecha_pago__lt=fin)
        if sede is not None:
            qs = qs.filter(matricula__alumno__sede=sede)
        total = qs.aggregate(total=Sum('monto'))['total'] or 0
        labels.append(inicio.strftime('%b %Y'))
        data.append(float(total))
    return labels, data


@login_required
@permiso_requerido(['admin'])
def reportes_sedes(request):
    fecha_inicio_str = request.GET.get('fecha_inicio', '')
    fecha_fin_str = request.GET.get('fecha_fin', '')

    fecha_inicio = None
    fecha_fin = None
    try:
        if fecha_inicio_str:
            fecha_inicio = date.fromisoformat(fecha_inicio_str)
        if fecha_fin_str:
            fecha_fin = date.fromisoformat(fecha_fin_str)
    except ValueError:
        pass

    sedes = Sede.objects.all()
    data_sedes = []

    for sede in sedes:
        alumnos_activos = Alumno.objects.filter(sede=sede, estado='activo').count()
        matriculas_qs = Matricula.objects.filter(alumno__sede=sede)

        pagos_qs = Pago.objects.filter(matricula__alumno__sede=sede)
        if fecha_inicio:
            pagos_qs = pagos_qs.filter(fecha_pago__gte=fecha_inicio)
        if fecha_fin:
            pagos_qs = pagos_qs.filter(fecha_pago__lte=fecha_fin)

        ingresos = pagos_qs.aggregate(total=Sum('monto'))['total'] or 0
        deuda = sum(
            m.deuda() for m in matriculas_qs.filter(estado='pendiente')
        )

        data_sedes.append({
            'sede': sede,
            'alumnos_activos': alumnos_activos,
            'total_matriculas': matriculas_qs.count(),
            'ingresos': ingresos,
            'deuda': deuda,
        })

    return render(request, 'web/administrador/reportes/reportes_sedes.html', {
        'data_sedes': data_sedes,
        'fecha_inicio_str': fecha_inicio_str,
        'fecha_fin_str': fecha_fin_str,
    })


@login_required
@permiso_requerido(['admin'])
def reporte_sede_detalle(request, sede_id):
    sede = get_object_or_404(Sede, id=sede_id)

    alumnos_activos = Alumno.objects.filter(sede=sede, estado='activo').count()
    alumnos_inactivos = Alumno.objects.filter(sede=sede, estado='inactivo').count()

    matriculas_qs = Matricula.objects.filter(alumno__sede=sede)
    matriculas_pagadas = matriculas_qs.filter(estado='pagado').count()
    matriculas_pendientes_count = matriculas_qs.filter(estado='pendiente').count()

    ingresos_total = (
        Pago.objects.filter(matricula__alumno__sede=sede)
        .aggregate(total=Sum('monto'))['total'] or 0
    )
    deuda_total = sum(
        m.deuda() for m in matriculas_qs.filter(estado='pendiente')
    )

    mensual_labels, mensual_data = _ingresos_6_meses(sede=sede)

    pagos_recientes = list(
        Pago.objects.filter(matricula__alumno__sede=sede)
        .select_related('matricula__alumno', 'matricula__ciclo')
        .order_by('-fecha_pago', '-id')[:10]
    )

    ciclos_usados = list(
        Matricula.objects.filter(alumno__sede=sede)
        .values('ciclo__nombre')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )

    return render(request, 'web/administrador/reportes/reporte_sede_detalle.html', {
        'sede': sede,
        'alumnos_activos': alumnos_activos,
        'alumnos_inactivos': alumnos_inactivos,
        'total_matriculas': matriculas_qs.count(),
        'matriculas_pagadas': matriculas_pagadas,
        'matriculas_pendientes': matriculas_pendientes_count,
        'ingresos_total': ingresos_total,
        'deuda_total': deuda_total,
        'pagos_recientes': pagos_recientes,
        'ciclos_usados': ciclos_usados,
        'chart_mensual_labels': json.dumps(mensual_labels),
        'chart_mensual_data': json.dumps(mensual_data),
        'chart_estado_labels': json.dumps(['Pagado', 'Pendiente']),
        'chart_estado_data': json.dumps([matriculas_pagadas, matriculas_pendientes_count]),
    })


@login_required
@permiso_requerido(['admin'])
def exportar_reporte_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reporte Financiero"

    header_fill = PatternFill("solid", fgColor="1F4E79")
    header_font = Font(bold=True, color="FFFFFF")
    center = Alignment(horizontal='center')

    headers = ['Alumno', 'DNI', 'Sede', 'Ciclo', 'Monto Pagado', 'Deuda', 'Fecha', 'Método']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center

    pagos = Pago.objects.select_related(
        'matricula__alumno',
        'matricula__alumno__sede',
        'matricula__ciclo',
    ).order_by('-fecha_pago')

    for row, pago in enumerate(pagos, 2):
        alumno = pago.matricula.alumno
        ws.cell(row=row, column=1, value=str(alumno))
        ws.cell(row=row, column=2, value=alumno.dni)
        ws.cell(row=row, column=3, value=str(alumno.sede))
        ws.cell(row=row, column=4, value=str(pago.matricula.ciclo))
        ws.cell(row=row, column=5, value=float(pago.monto))
        ws.cell(row=row, column=6, value=float(pago.matricula.deuda()))
        ws.cell(row=row, column=7, value=str(pago.fecha_pago))
        ws.cell(row=row, column=8, value=pago.get_metodo_pago_display())

    for col in ws.columns:
        max_len = max((len(str(cell.value or '')) for cell in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = max_len + 4

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="reporte_financiero.xlsx"'
    wb.save(response)
    return response
