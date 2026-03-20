from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o Contraseña incorrecto')

    return render(request, 'web/login/login.html')


@login_required
def dashboard(request):
    perfil = request.user.perfil

    if perfil.tipo_usuario =='admin':
        return render(request,'web/dashboard/dashboard_admin.html')
    elif perfil.tipo_usuario == 'secretaria':
        return render(request,'web/dashboard/dashboard_secre.html')

@login_required
def registrar_alumno(request):
    return render(request,'web/alumno/registrar_alumno.html')
@login_required
def registrar_apoderado(request):
    return render(request,'web/apoderado/registrar_apoderado.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')
@login_required
def matriculas(request):
    return render(request, 'web/matricula/matricula.html')