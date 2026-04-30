from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def reportes_sedes(request):
    return render(request, 'web/administrador/reportes/reportes_sedes.html')