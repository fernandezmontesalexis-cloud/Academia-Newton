from django.shortcuts import render
from web.permisos import permiso_requerido
from django.contrib.auth.decorators import login_required

from ..models import Ciclo
from ..models import Sede
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from ..models import Sede


@login_required
@permiso_requerido(['admin'])
def lista_ciclos(request):
    ciclos = Ciclo.objects.all()

    return render(request, 'web/administrador/ciclos/lista.html', {
        'ciclos': ciclos
    })
@login_required
@permiso_requerido(['admin'])
def lista_sedes(request):
    sedes = Sede.objects.all()

    return render(request, 'web/administrador/sedes/lista_sedes.html', {
        'sedes': sedes
    })
@login_required
def crear_sede(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")

        if not nombre:
            messages.error(request, "El nombre es obligatorio")
            return redirect("crear_sede")

        Sede.objects.create(nombre=nombre)

        messages.success(request, "Sede creada correctamente")
        return redirect("lista_sedes")

    return render(request, "web/administrador/sedes/crear_sede.html")