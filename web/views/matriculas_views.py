from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

from ..models import Matricula, Pago


@login_required
def matriculas(request):

    # base queryset
    matriculas = Matricula.objects.filter(
        alumno__sede=request.user.perfil.sede,
        alumno__estado='activo'
    ).select_related('alumno', 'ciclo')

    # búsqueda por DNI
    dni = request.GET.get('dni')

    if dni:
        matriculas = matriculas.filter(alumno__dni__icontains=dni)

    # primero pendientes, luego pagados, y los más recientes arriba
    matriculas = matriculas.order_by('estado', '-fecha_matricula')

    # cálculo de pagos y deudas
    for m in matriculas:
        total_pagado = Pago.objects.filter(matricula=m).aggregate(
            Sum('monto')
        )['monto__sum'] or 0

        m.total_pagado = total_pagado
        m.deuda = m.ciclo.precio - total_pagado

    return render(request, 'web/secretaria/matriculas/lista_matricula.html', {
        'matriculas': matriculas
    })