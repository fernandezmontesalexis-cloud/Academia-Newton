from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from ..models import Ciclo
from ..models import Sede


@login_required
def lista_ciclos(request):
    ciclos = Ciclo.objects.all()

    return render(request, 'web/administrador/ciclos/lista.html', {
        'ciclos': ciclos
    })
@login_required
def lista_sedes(request):
    sedes = Sede.objects.all()

    return render(request, 'web/administrador/sedes/lista_sedes.html', {
        'sedes': sedes
    })