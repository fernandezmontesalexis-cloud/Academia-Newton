from django.shortcuts import render, redirect
from web.permisos import permiso_requerido
from django.contrib.auth.decorators import login_required
from ..models import Alumno

@login_required 
@permiso_requerido(['admin','secretaria'])
def lista_alumnos(request):
    alumnos = Alumno.objects.filter(
        sede=request.user.perfil.sede
    )

    dni = request.GET.get('dni')

    if dni:
        alumnos = alumnos.filter(dni__icontains=dni)

    return render(request, 'web/secretaria/alumnos/lista_alumnos.html', {
        'alumnos': alumnos
    })


@login_required
@permiso_requerido(['admin','secretaria'])
def cambiar_estado_alumno(request, alumno_id):
    alumno = Alumno.objects.get(id=alumno_id)

    if alumno.estado == 'activo':
        alumno.estado = 'inactivo'
    else:
        alumno.estado = 'activo'

    alumno.save()

    return redirect('lista_alumnos')