from django.shortcuts import render
from web.permisos import permiso_requerido
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.core.paginator import Paginator
from ..models import Matricula, Pago


@login_required
@permiso_requerido(['admin','secretaria'])
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

    #PAGINACIÓN
    paginator = Paginator(matriculas, 10)
    page_number = request.GET.get('page')

    matriculas = paginator.get_page(page_number)

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