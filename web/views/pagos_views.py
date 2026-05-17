from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone

from datetime import date
from decimal import Decimal, InvalidOperation

from web.permisos import permiso_requerido
from ..models import Matricula, Pago

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.colors import HexColor


@login_required
@permiso_requerido(['admin', 'secretaria'])
def pagos(request, matricula_id):
    matricula = get_object_or_404(Matricula, id=matricula_id)

    if matricula.alumno.sede != request.user.perfil.sede:
        messages.error(request, "No tienes acceso a esta matrícula")
        return redirect('matriculas')

    def _contexto(error_monto=None, error_metodo=None, monto_prev="", metodo_prev=""):
        total_pagado = Pago.objects.filter(matricula=matricula).aggregate(
            Sum('monto')
        )['monto__sum'] or 0
        total_ciclo = matricula.ciclo.precio
        deuda = total_ciclo - total_pagado
        lista_pagos = Pago.objects.filter(matricula=matricula).order_by('-fecha_pago')
        return {
            'matricula': matricula,
            'total_pagado': total_pagado,
            'total_ciclo': total_ciclo,
            'deuda': deuda,
            'pagos': lista_pagos,
            'error_monto': error_monto,
            'error_metodo': error_metodo,
            'monto_prev': monto_prev,
            'metodo_prev': metodo_prev,
        }

    if request.method == 'POST':
        monto_raw = request.POST.get('monto', '').strip()
        metodo = request.POST.get('metodo_pago', '').strip()
        apoderado = request.POST.get('apoderado', '').strip()

        total_pagado = Pago.objects.filter(matricula=matricula).aggregate(
            Sum('monto')
        )['monto__sum'] or 0
        total_ciclo = matricula.ciclo.precio

        error_monto = None
        error_metodo = None

        try:
            monto = Decimal(monto_raw)
        except (InvalidOperation, TypeError, ValueError):
            error_monto = "Ingresa un monto numérico válido"
            monto = None

        if monto is not None:
            if monto <= 0:
                error_monto = "El monto debe ser mayor a 0"
            elif total_pagado + monto > total_ciclo:
                error_monto = f"El monto excede la deuda restante (S/. {total_ciclo - total_pagado:.2f})"

        if not metodo:
            error_metodo = "Debes seleccionar un método de pago"

        if error_monto or error_metodo:
            return render(
                request,
                'web/secretaria/pagos/pagos.html',
                _contexto(
                    error_monto=error_monto,
                    error_metodo=error_metodo,
                    monto_prev=monto_raw,
                    metodo_prev=metodo,
                ),
            )

        Pago.objects.create(
            matricula=matricula,
            registrado_por=request.user.perfil,
            fecha_pago=date.today(),
            monto=monto,
            metodo_pago=metodo,
            apoderado=apoderado,
        )

        total_actual = Pago.objects.filter(matricula=matricula).aggregate(
            Sum('monto')
        )['monto__sum'] or 0
        matricula.estado = 'pagado' if total_actual >= total_ciclo else 'pendiente'
        matricula.save()

        url = reverse('pagos', kwargs={'matricula_id': matricula.id})
        return redirect(f"{url}?ok=1")

    return render(request, 'web/secretaria/pagos/pagos.html', _contexto())


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
@permiso_requerido(['admin', 'secretaria'])
def boleta_pdf(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id)

    if pago.matricula.alumno.sede != request.user.perfil.sede:
        return HttpResponse("No autorizado", status=403)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="comprobante_{pago.id:06d}.pdf"'

    width = 80 * mm
    height = 260 * mm

    doc = SimpleDocTemplate(
        response,
        pagesize=(width, height),
        leftMargin=6 * mm,
        rightMargin=6 * mm,
        topMargin=6 * mm,
        bottomMargin=6 * mm,
    )

    # Totales acumulados a la fecha del comprobante
    total_pagado = Pago.objects.filter(
        matricula=pago.matricula
    ).aggregate(Sum('monto'))['monto__sum'] or 0
    deuda = pago.matricula.ciclo.precio - total_pagado

    alumno = pago.matricula.alumno
    ciclo = pago.matricula.ciclo

    # Colores
    azul = HexColor('#1a56db')
    gris_oscuro = HexColor('#374151')
    gris_claro = HexColor('#6b7280')
    rojo = HexColor('#dc2626')
    verde = HexColor('#16a34a')
    amarillo = HexColor('#d97706')
    separador = HexColor('#e5e7eb')

    # Estilos de párrafo
    titulo = ParagraphStyle(
        'titulo', fontName='Helvetica-Bold', fontSize=13,
        alignment=TA_CENTER, textColor=azul, spaceAfter=1,
    )
    subtitulo = ParagraphStyle(
        'subtitulo', fontName='Helvetica', fontSize=7,
        alignment=TA_CENTER, textColor=gris_claro, spaceAfter=0,
    )
    numero_comp = ParagraphStyle(
        'numero_comp', fontName='Helvetica-Bold', fontSize=9,
        alignment=TA_CENTER, textColor=gris_oscuro, spaceAfter=0,
    )
    label = ParagraphStyle(
        'label', fontName='Helvetica', fontSize=6.5,
        textColor=gris_claro, spaceAfter=1,
    )
    valor = ParagraphStyle(
        'valor', fontName='Helvetica-Bold', fontSize=8,
        textColor=gris_oscuro, spaceAfter=4,
    )
    monto_grande = ParagraphStyle(
        'monto_grande', fontName='Helvetica-Bold', fontSize=14,
        alignment=TA_CENTER, textColor=azul, spaceAfter=1,
    )
    footer_style = ParagraphStyle(
        'footer', fontName='Helvetica', fontSize=7,
        alignment=TA_CENTER, textColor=gris_claro, spaceAfter=2,
    )

    def sep():
        return HRFlowable(
            width='100%', thickness=0.5,
            color=separador, spaceAfter=4, spaceBefore=4,
        )

    # Estado del pago
    if deuda <= 0:
        estado_texto = "PAGADO COMPLETAMENTE"
        estado_color = verde
    elif total_pagado > pago.monto:
        estado_texto = "PAGO PARCIAL"
        estado_color = amarillo
    else:
        estado_texto = "PENDIENTE"
        estado_color = rojo

    estado_style = ParagraphStyle(
        'estado', fontName='Helvetica-Bold', fontSize=9,
        alignment=TA_CENTER, textColor=estado_color, spaceAfter=2,
    )

    fecha_str = pago.fecha_pago.strftime('%d/%m/%Y')

    elementos = []

    # ── ENCABEZADO ──────────────────────────────────
    elementos.append(Spacer(1, 2 * mm))
    elementos.append(Paragraph("ACADEMIA NEWTON", titulo))
    elementos.append(Paragraph("Newton en Red  —  Sistema Académico", subtitulo))
    elementos.append(Spacer(1, 3 * mm))
    elementos.append(sep())

    # ── SEDE / FECHA ─────────────────────────────────
    elementos.append(Paragraph(f"Sede: {alumno.sede.nombre}", label))
    elementos.append(Paragraph(f"Fecha: {fecha_str}", label))
    elementos.append(sep())

    # ── NÚMERO DE COMPROBANTE ────────────────────────
    elementos.append(Spacer(1, 1 * mm))
    elementos.append(Paragraph(f"COMPROBANTE  N°  {pago.id:06d}", numero_comp))
    elementos.append(Spacer(1, 2 * mm))
    elementos.append(sep())

    # ── DATOS DEL ALUMNO ─────────────────────────────
    elementos.append(Paragraph("Alumno", label))
    elementos.append(Paragraph(str(alumno), valor))

    elementos.append(Paragraph("DNI", label))
    elementos.append(Paragraph(alumno.dni, valor))

    elementos.append(Paragraph("Ciclo", label))
    elementos.append(Paragraph(ciclo.nombre, valor))

    elementos.append(Paragraph("Cajero", label))
    elementos.append(Paragraph(pago.registrado_por.user.username, valor))

    if pago.apoderado:
        elementos.append(Paragraph("Apoderado / Responsable", label))
        elementos.append(Paragraph(pago.apoderado, valor))

    elementos.append(sep())

    # ── MÉTODO DE PAGO ───────────────────────────────
    elementos.append(Paragraph("Método de pago", label))
    elementos.append(Paragraph(pago.get_metodo_pago_display(), valor))
    elementos.append(sep())

    # ── MONTO DE ESTE PAGO ───────────────────────────
    elementos.append(Spacer(1, 2 * mm))
    elementos.append(Paragraph(f"S/. {pago.monto:.2f}", monto_grande))
    elementos.append(Paragraph("Monto de este pago", subtitulo))
    elementos.append(Spacer(1, 3 * mm))
    elementos.append(sep())

    # ── RESUMEN FINANCIERO ───────────────────────────
    elementos.append(Paragraph(f"Total del ciclo:      S/. {ciclo.precio:.2f}", label))
    elementos.append(Paragraph(f"Total pagado:         S/. {total_pagado:.2f}", label))

    deuda_style = ParagraphStyle(
        'deuda_line', fontName='Helvetica-Bold', fontSize=7,
        textColor=rojo if deuda > 0 else verde, spaceAfter=1,
    )
    elementos.append(Paragraph(
        f"Deuda restante:       S/. {deuda:.2f}",
        deuda_style,
    ))
    elementos.append(sep())

    # ── ESTADO ───────────────────────────────────────
    elementos.append(Spacer(1, 1 * mm))
    elementos.append(Paragraph(estado_texto, estado_style))
    elementos.append(sep())

    # ── FOOTER ───────────────────────────────────────
    elementos.append(Spacer(1, 3 * mm))
    elementos.append(Paragraph("Gracias por confiar en Academia Newton", footer_style))
    elementos.append(Paragraph("Newton en Red — Sistema Académico", footer_style))
    elementos.append(Spacer(1, 2 * mm))

    doc.build(elementos)
    return response
