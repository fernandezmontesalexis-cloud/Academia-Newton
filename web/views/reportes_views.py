from django.shortcuts import render
from web.permisos import permiso_requerido
from django.contrib.auth.decorators import login_required


@login_required
@permiso_requerido(['admin'])
def reportes_sedes(request):
    return render(request, 'web/administrador/reportes/reportes_sedes.html')