from django.shortcuts import render, redirect
from web.permisos import permiso_requerido
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from datetime import date
from decimal import Decimal, InvalidOperation

from ..models import Matricula, Pago


@login_required
@permiso_requerido(['admin','secretaria'])
def pagos(request, matricula_id):
    matricula = Matricula.objects.get(id=matricula_id)

    # calcular pagos actuales
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

        metodo = request.POST.get('metodo_pago')

        nuevo_total = total_pagado + monto

        # validación
        if nuevo_total > total_ciclo:
            messages.error(request, "El monto excede lo que debe pagar")
            return redirect('pagos', matricula_id=matricula.id)

        # guardar pago
        Pago.objects.create(
            matricula=matricula,
            registrado_por=request.user.perfil,
            fecha_pago=date.today(),
            monto=monto,
            metodo_pago=metodo
        )

        # actualizar estado
        if nuevo_total >= total_ciclo:
            matricula.estado = "pagado"
        else:
            matricula.estado = "pendiente"

        matricula.save()

        return redirect('matriculas')

    return render(request, 'web/secretaria/pagos/pagos.html', {
        'matricula': matricula,
        'total_pagado': total_pagado,
        'total_ciclo': total_ciclo,
        'deuda': deuda
    })