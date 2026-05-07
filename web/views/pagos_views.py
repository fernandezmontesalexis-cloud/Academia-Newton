from django.shortcuts import render, redirect
from web.permisos import permiso_requerido
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from datetime import date
from decimal import Decimal, InvalidOperation

from ..models import Matricula, Pago


from django.shortcuts import get_object_or_404

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from django.http import HttpResponse
from reportlab.lib.units import mm


@login_required
@permiso_requerido(['admin','secretaria'])
def pagos(request, matricula_id):

    matricula = get_object_or_404(Matricula, id=matricula_id)

    # 🔐 seguridad por sede
    if matricula.alumno.sede != request.user.perfil.sede:
        messages.error(request, "No tienes acceso a esta matrícula")
        return redirect('matriculas')

    total_pagado = Pago.objects.filter(matricula=matricula).aggregate(
        Sum('monto')
    )['monto__sum'] or 0

    total_ciclo = matricula.ciclo.precio
    deuda = total_ciclo - total_pagado

    if request.method == 'POST':
        try:
            monto = Decimal(request.POST.get('monto'))
        except (InvalidOperation, TypeError):
            messages.error(request, "Monto inválido")
            return redirect('pagos', matricula_id=matricula.id)

        if monto <= 0:
            messages.error(request, "El monto debe ser mayor a 0")
            return redirect('pagos', matricula_id=matricula.id)

        metodo = request.POST.get('metodo_pago')

        if not metodo:
            messages.error(request, "Debe seleccionar un método de pago")
            return redirect('pagos', matricula_id=matricula.id)

        nuevo_total = total_pagado + monto

        if nuevo_total > total_ciclo:
            messages.error(request, "El monto excede lo que debe pagar")
            return redirect('pagos', matricula_id=matricula.id)

        Pago.objects.create(
            matricula=matricula,
            registrado_por=request.user.perfil,
            fecha_pago=date.today(),
            monto=monto,
            metodo_pago=metodo
        )

        total_pagado_actual = Pago.objects.filter(matricula=matricula).aggregate(
            Sum('monto')
        )['monto__sum'] or 0

        if total_pagado_actual >= total_ciclo:
            matricula.estado = "pagado"
        else:
            matricula.estado = "pendiente"

        matricula.save()

        return redirect('pagos', matricula_id=matricula.id)

    pagos = Pago.objects.filter(matricula=matricula).order_by('-fecha_pago')

    return render(request, 'web/secretaria/pagos/pagos.html', {
        'matricula': matricula,
        'total_pagado': total_pagado,
        'total_ciclo': total_ciclo,
        'deuda': deuda,
        'pagos': pagos
    })
@login_required
@permiso_requerido(['admin', 'secretaria'])
def lista_pagos(request):
    sede = request.user.perfil.sede

    matriculas = Matricula.objects.filter(
        alumno__sede=sede
    ).select_related('alumno', 'ciclo')

    data = []
    for m in matriculas:
        total_pagado = m.pago_set.aggregate(total=Sum('monto'))['total'] or 0
        deuda = m.ciclo.precio - total_pagado
        data.append({
            'matricula': m,
            'total_pagado': total_pagado,
            'deuda': deuda,
        })

    data.sort(key=lambda x: x['deuda'], reverse=True)

    pagos_hoy = (
        Pago.objects.filter(fecha_pago=date.today(), matricula__alumno__sede=sede)
        .aggregate(total=Sum('monto'))['total'] or 0
    )
    deuda_total = sum(x['deuda'] for x in data)
    alumnos_con_deuda = sum(1 for x in data if x['deuda'] > 0)

    return render(request, 'web/secretaria/pagos/lista_pagos.html', {
        'data': data,
        'pagos_hoy': pagos_hoy,
        'deuda_total': deuda_total,
        'alumnos_con_deuda': alumnos_con_deuda,
    })


@login_required
@permiso_requerido(['admin','secretaria'])
def boleta_pdf(request, pago_id):

    pago = get_object_or_404(Pago, id=pago_id)

    if pago.matricula.alumno.sede != request.user.perfil.sede:
        return HttpResponse("No autorizado", status=403)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="boleta_{pago.id}.pdf"'

    # 🔥 TAMAÑO TIPO TICKET
    width = 80 * mm
    height = 200 * mm

    doc = SimpleDocTemplate(
        response,
        pagesize=(width, height),
        leftMargin=5,
        rightMargin=5,
        topMargin=5,
        bottomMargin=5
    )

    styles = getSampleStyleSheet()

    alumno = pago.matricula.alumno
    ciclo = pago.matricula.ciclo

    elementos = []

    # 🏫 ENCABEZADO
    elementos.append(Paragraph("<b>ACADEMIA NEWTON</b>", styles['Normal']))
    elementos.append(Paragraph("Lima - Perú", styles['Normal']))
    elementos.append(Spacer(1, 8))

    elementos.append(Paragraph("<b>BOLETA DE PAGO</b>", styles['Normal']))
    elementos.append(Paragraph(f"N°: {pago.id}", styles['Normal']))
    elementos.append(Spacer(1, 8))

    elementos.append(Paragraph("--------------------------------", styles['Normal']))

    # 👤 DATOS
    elementos.append(Paragraph(f"Alumno: {alumno}", styles['Normal']))
    elementos.append(Paragraph(f"DNI: {alumno.dni}", styles['Normal']))
    elementos.append(Paragraph(f"Ciclo: {ciclo.nombre}", styles['Normal']))
    elementos.append(Spacer(1, 6))

    elementos.append(Paragraph("--------------------------------", styles['Normal']))

    # 💰 PAGO
    elementos.append(Paragraph(f"Fecha: {pago.fecha_pago}", styles['Normal']))
    elementos.append(Paragraph(f"Metodo: {pago.metodo_pago}", styles['Normal']))
    elementos.append(Spacer(1, 6))

    elementos.append(Paragraph("--------------------------------", styles['Normal']))

    elementos.append(Paragraph(f"<b>TOTAL: S/. {pago.monto}</b>", styles['Normal']))

    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph(f"Estado: {pago.matricula.estado.upper()}", styles['Normal']))

    elementos.append(Spacer(1, 10))

    # 💬 FINAL
    elementos.append(Paragraph("Gracias por su pago", styles['Normal']))

    doc.build(elementos)

    return response