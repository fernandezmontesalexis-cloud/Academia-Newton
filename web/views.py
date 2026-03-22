from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Alumno, Apoderado, Sede


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
    if request.method == 'POST':

        request.session['alumno']={
            'apellido_paterno': request.POST.get('apellido_paterno'),
            'apellido_materno': request.POST.get('apellido_materno'),
            'nombres': request.POST.get('nombres'),
            'dni': request.POST.get('dni'),
            'celular': request.POST.get('celular'),
            'fecha_nacimiento': request.POST.get('fecha_nacimiento'),
            'direccion': request.POST.get('direccion'),
            'distrito': request.POST.get('distrito'),
            'email': request.POST.get('email'),
            'sede': request.POST.get('sede'),
        }
        return redirect('registrar_apoderado')
    sedes = Sede.objects.all()
    return render(request, 'web/alumno/registrar_alumno.html', {'sedes': sedes})

@login_required
def registrar_apoderado(request):
    if request.method == 'POST':
        
        data = request.session.get('alumno')

        apoderado = Apoderado.objects.create(
            nombre_completo = request.POST.get('nombre_apoderado'),
            dni = request.POST.get('dni_apoderado'),
            celular = request.POST.get('celular_apoderado'),
            direccion = request.POST.get('direccion_apoderado')
        )
        sede = Sede.objects.get(id=data['sede'])

        Alumno.objects.create(
            apellido_paterno=data['apellido_paterno'],
            apellido_materno=data['apellido_materno'],
            nombres=data['nombres'],
            dni=data['dni'],
            celular=data['celular'],
            fecha_nacimiento=data['fecha_nacimiento'],
            direccion=data['direccion'],
            distrito=data['distrito'],
            email=data['email'],
            sede=sede,
            apoderado=apoderado
        )
        del request.session['alumno']

        return redirect('dashboard')
    return render(request, 'web/apoderado/registrar_apoderado.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')
@login_required
def matriculas(request):
    return render(request, 'web/matricula/matricula.html')