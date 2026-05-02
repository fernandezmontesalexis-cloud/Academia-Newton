from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    perfil = getattr(request.user, 'perfil', None)

    if not perfil:
        return redirect('login')

    dashboards = {
        "admin": "web/administrador/dashboard_admin.html",
        "secretaria": "web/secretaria/dashboard_secre.html",
    }

    template = dashboards.get(perfil.tipo_usuario)

    if not template:
        return redirect('login')

    return render(request, template)