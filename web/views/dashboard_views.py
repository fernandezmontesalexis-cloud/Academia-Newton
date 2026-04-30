from django.shortcuts import render
from django.contrib.auth.decorators import login_required



@login_required
def dashboard(request):
    perfil = request.user.perfil

    if perfil.tipo_usuario == "admin":
        return render(request, "web/administrador/dashboard_admin.html")

    elif perfil.tipo_usuario == "secretaria":
        return render(request, "web/secretaria/dashboard_secre.html")