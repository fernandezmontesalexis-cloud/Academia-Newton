from django.shortcuts import render, redirect, get_object_or_404
from web.permisos import permiso_requerido
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from ..models import Alumno, Matricula


@login_required
@permiso_requerido(['admin', 'secretaria'])
def lista_alumnos(request):
    alumnos_lista = Alumno.objects.filter(
        sede=request.user.perfil.sede
    ).select_related('distrito')

    dni = request.GET.get('dni')
    if dni:
        alumnos_lista = alumnos_lista.filter(dni__icontains=dni)

    paginator = Paginator(alumnos_lista, 10)
    page_number = request.GET.get('page')
    alumnos = paginator.get_page(page_number)

    return render(request, 'web/secretaria/alumnos/lista_alumnos.html', {
        'alumnos': alumnos
    })


@login_required
@permiso_requerido(['admin', 'secretaria'])
def cambiar_estado_alumno(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id, sede=request.user.perfil.sede)
    alumno.estado = 'inactivo' if alumno.estado == 'activo' else 'activo'
    alumno.save()
    return redirect('lista_alumnos')


@login_required
@permiso_requerido(['admin', 'secretaria'])
def detalle_alumno(request, alumno_id):
    alumno = get_object_or_404(
        Alumno.objects.select_related('apoderado', 'distrito', 'sede'),
        id=alumno_id,
        sede=request.user.perfil.sede,
    )

    formacion_academica = getattr(alumno, 'formacionacademica', None)
    formacion_adicional = getattr(alumno, 'formacionadicional', None)

    matriculas = (
        Matricula.objects.filter(alumno=alumno)
        .select_related('ciclo')
        .prefetch_related('pago_set')
        .order_by('-fecha_matricula')
    )

    historial = []
    for m in matriculas:
        historial.append({
            'matricula': m,
            'pagos': m.pago_set.order_by('-fecha_pago'),
            'total_pagado': m.total_pagado(),
            'deuda': m.deuda(),
        })

    return render(request, 'web/secretaria/alumnos/detalle_alumno.html', {
        'alumno': alumno,
        'formacion_academica': formacion_academica,
        'formacion_adicional': formacion_adicional,
        'historial': historial,
    })
