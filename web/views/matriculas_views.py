from django.shortcuts import render
from django.http import HttpResponse
from web.permisos import permiso_requerido
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.core.paginator import Paginator
from ..models import Matricula, Pago

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment


@login_required
@permiso_requerido(['admin', 'secretaria'])
def matriculas(request):
    sede = request.user.perfil.sede

    matriculas_qs = (
        Matricula.objects.filter(alumno__sede=sede, alumno__estado='activo')
        .select_related('alumno', 'ciclo')
        .prefetch_related('pago_set')
    )

    dni = request.GET.get('dni')
    if dni:
        matriculas_qs = matriculas_qs.filter(alumno__dni__icontains=dni)

    # stats antes de paginar
    total_activas = matriculas_qs.count()
    pendientes = matriculas_qs.filter(estado='pendiente').count()
    pagadas = matriculas_qs.filter(estado='pagado').count()
    ingresos = (
        Pago.objects.filter(matricula__alumno__sede=sede)
        .aggregate(total=Sum('monto'))['total'] or 0
    )

    matriculas_qs = matriculas_qs.order_by('estado', '-fecha_matricula')

    paginator = Paginator(matriculas_qs, 10)
    matriculas_page = paginator.get_page(request.GET.get('page'))

    return render(request, 'web/secretaria/matriculas/lista_matricula.html', {
        'matriculas': matriculas_page,
        'total_activas': total_activas,
        'pendientes': pendientes,
        'pagadas': pagadas,
        'ingresos': ingresos,
    })


@login_required
@permiso_requerido(['admin', 'secretaria'])
def exportar_excel(request):
    sede = request.user.perfil.sede

    matriculas_qs = (
        Matricula.objects.filter(alumno__sede=sede, alumno__estado='activo')
        .select_related('alumno', 'ciclo')
        .prefetch_related('pago_set')
        .order_by('-fecha_matricula')
    )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Matrículas"

    header_fill = PatternFill("solid", fgColor="1F4E79")
    header_font = Font(bold=True, color="FFFFFF")
    center = Alignment(horizontal="center")

    headers = ['N°', 'Alumno', 'DNI', 'Ciclo', 'Fecha Matrícula', 'Estado', 'Pagado (S/.)', 'Deuda (S/.)']
    for col, texto in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=texto)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center

    for i, m in enumerate(matriculas_qs, 1):
        total = m.total_pagado()
        deuda = m.deuda()
        ws.append([
            i,
            str(m.alumno),
            m.alumno.dni,
            m.ciclo.nombre,
            m.fecha_matricula.strftime('%d/%m/%Y'),
            m.estado.capitalize(),
            float(total),
            float(deuda),
        ])

    for col in ws.columns:
        max_len = max((len(str(cell.value or '')) for cell in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = max_len + 4

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="matriculas_{sede.nombre}.xlsx"'
    wb.save(response)
    return response
