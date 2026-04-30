from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Alumno, Apoderado, Sede, FormacionAcademica, FormacionAdicional
from .models import Matricula, Pago, Ciclo
from datetime import date
from django.db.models import Sum
from decimal import Decimal
from decimal import InvalidOperation


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

    return render(request, 'web/auth/login.html')


@login_required
def dashboard(request):
    perfil = request.user.perfil

    if perfil.tipo_usuario =='admin':
        return render(request,'web/administrador/dashboard_admin.html')
    elif perfil.tipo_usuario == 'secretaria':
        return render(request,'web/secretaria/dashboard_secre.html')

@login_required
def registrar_alumno(request):

    # limpiar session si es nuevo ingreso
    if request.method == 'GET':
        request.session.pop('alumno', None)

    if request.method == 'POST':

        # capturar datos del input
        apellido_paterno = request.POST.get('apellido_paterno')
        apellido_materno = request.POST.get('apellido_materno')
        nombres = request.POST.get('nombres')
        dni = request.POST.get('dni')
        celular = request.POST.get('celular')
        
        fecha_nacimiento = request.POST.get('fecha_nacimiento')
        direccion = request.POST.get('direccion')
        distrito = request.POST.get('distrito')
        email = request.POST.get('email')

        #validar datos , antes de guardar en session

        # DNI obligatorio
        if not dni:
            messages.error(request, "El DNI es obligatorio")
            return render(request, 'web/secretaria/alumnos/registrar_alumno.html', {'alumno': request.POST})

        # DNI válido
        if len(dni) != 8 or not dni.isdigit():
            messages.error(request, "El DNI debe tener 8 números")
            return render(request, 'web/secretaria/alumnos/registrar_alumno.html', {'alumno': request.POST})

        # DNI duplicado
        if Alumno.objects.filter(dni=dni).exists():
            messages.error(request, "Este DNI ya está registrado")
            return render(request, 'web/secretaria/alumnos/registrar_alumno.html', {'alumno': request.POST})

        # Fecha obligatoria
        if not fecha_nacimiento:
            messages.error(request, "Debes ingresar la fecha de nacimiento")
            return render(request, 'web/secretaria/alumnos/registrar_alumno.html', {'alumno': request.POST})

        #guardar datos en session luego de validar
        request.session['alumno'] = {
            'apellido_paterno': apellido_paterno,
            'apellido_materno': apellido_materno,
            'nombres': nombres,
            'dni': dni,
            'celular': celular,
            'fecha_nacimiento': fecha_nacimiento,
            'direccion': direccion,
            'distrito': distrito,
            'email': email,
        }

        return redirect('registrar_apoderado')

    # GET
    alumno = request.session.get('alumno', {})

    return render(request, 'web/secretaria/alumnos/registrar_alumno.html', {
    'alumno': alumno
})
@login_required
def registrar_apoderado(request):

    if request.method == 'POST':
        
        request.session['apoderado'] = {
            'nombre_apoderado': request.POST.get('nombre_apoderado'),
            'dni_apoderado': request.POST.get('dni_apoderado'),
            'celular_apoderado': request.POST.get('celular_apoderado'),
            'direccion_apoderado': request.POST.get('direccion_apoderado'),
        }
        return redirect('regis_form_academica')
    apoderado = request.session.get('apoderado', {})

    return render(request, 'web/secretaria/alumnos/registrar_apoderado.html', {
        'apoderado': apoderado
    })


@login_required
def regis_form_academica(request):
    
    if request.method == 'POST':
        request.session['formacion_academica'] = {
            'tipo_institucion':request.POST.get('tipo_institucion'),
            'nombre_ie':request.POST.get('nombre_ie'),
            'distrito_ie':request.POST.get('distrito_ie'),
        }
        return redirect('regis_form_adicional')
        # ESTO VA FUERA DEL IF
    formacion = request.session.get('formacion_academica', {})

    return render(request, 'web/secretaria/alumnos/regis_form_academica.html', {
        'formacion': formacion
    })
@login_required
def regis_form_adicional(request):

    if request.method == 'POST':

        request.session['formacion_adicional'] = {
            'estudio_previo': request.POST.get('estudio_previo'),
            'tipo_estudio': request.POST.get('tipo_estudio'),
            'academia_anterior': request.POST.get('academia_anterior'),
            'carrera_interes': request.POST.get('carrera_interes'),
            'segunda_carrera': request.POST.get('segunda_carrera'),
            'ciclo': request.POST.get('ciclo'),
        }

        alumno_data = request.session.get('alumno')
        apoderado_data = request.session.get('apoderado')
        formacion_acad_data = request.session.get('formacion_academica')

        if not alumno_data or not formacion_acad_data:
            return redirect('registrar_alumno')

        # apoderado opcional
        apoderado = None
        if apoderado_data and apoderado_data.get('nombre_apoderado'):
            apoderado = Apoderado.objects.create(
                nombre_completo=apoderado_data['nombre_apoderado'],
                dni=apoderado_data['dni_apoderado'],
                celular=apoderado_data['celular_apoderado'],
                direccion=apoderado_data['direccion_apoderado']
            )

        sede = request.user.perfil.sede

        alumno = Alumno.objects.create(
            apellido_paterno=alumno_data['apellido_paterno'],
            apellido_materno=alumno_data['apellido_materno'],
            nombres=alumno_data['nombres'],
            dni=alumno_data['dni'],
            celular=alumno_data['celular'],
            fecha_nacimiento=alumno_data['fecha_nacimiento'],
            direccion=alumno_data['direccion'],
            distrito=alumno_data['distrito'],
            email=alumno_data['email'],
            estado = 'activo',
            sede=sede,
            apoderado=apoderado
        )

        FormacionAcademica.objects.create(
            alumno=alumno,
            tipo_institucion=formacion_acad_data['tipo_institucion'],
            nombre_ie=formacion_acad_data['nombre_ie'],
            distrito_ie=formacion_acad_data['distrito_ie']
        )

        form_adicional = request.session.get('formacion_adicional')

        FormacionAdicional.objects.create(
            alumno=alumno,
            estudio_previo=form_adicional['estudio_previo'] == 'si',
            tipo_estudio=form_adicional['tipo_estudio'],
            academia_anterior=form_adicional['academia_anterior'],
            carrera_interes=form_adicional['carrera_interes'],
            segunda_carrera=form_adicional['segunda_carrera']
        )

        ciclo_id = form_adicional.get('ciclo')

        if not ciclo_id:
            messages.error(request, "Debe seleccionar un ciclo")
            return redirect('regis_form_adicional')

        ciclo = Ciclo.objects.get(id=ciclo_id)

        matricula = Matricula.objects.create(
            alumno=alumno,
            ciclo=ciclo,
            fecha_matricula=date.today(),
            estado="pendiente",
            registrado_por=request.user.perfil
        )

        # limpiar sesión
        request.session.pop('alumno', None)
        request.session.pop('apoderado', None)
        request.session.pop('formacion_academica', None)
        request.session.pop('formacion_adicional', None)

        return redirect('pagos', matricula_id=matricula.id)

    ciclos = Ciclo.objects.all()
    formacion_adicional = request.session.get('formacion_adicional', {})

    return render(request,'web/secretaria/alumnos/regis_form_adicional.html', {
        'formacion_adicional': formacion_adicional,
        'ciclos': ciclos
    })
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')
@login_required
def matriculas(request):

    # base queryset
    matriculas = Matricula.objects.filter(
        alumno__sede=request.user.perfil.sede,
        alumno__estado = 'activo'   
    ).select_related('alumno', 'ciclo')

    # búsqueda por DNI
    dni = request.GET.get('dni')

    if dni:
        matriculas = matriculas.filter(alumno__dni__icontains=dni)

    #primero pendientes, luego pagados, y los más recientes arriba
    matriculas = matriculas.order_by('estado', '-fecha_matricula')

    #calculo de pagos y deudas

    for m in matriculas:
        total_pagado = Pago.objects.filter(matricula=m).aggregate(
            Sum('monto')
        )['monto__sum'] or 0

        m.total_pagado = total_pagado
        m.deuda = m.ciclo.precio - total_pagado

    return render(request, 'web/secretaria/matriculas/lista_matricula.html', {    
        'matriculas': matriculas
    })   

@login_required
def pagos(request, matricula_id):
    matricula = Matricula.objects.get(id=matricula_id)

    #calcular pagos actuales
    total_pagado = Pago.objects.filter(matricula=matricula).aggregate(
        Sum('monto')
    )['monto__sum'] or 0

    total_ciclo = matricula.ciclo.precio
    deuda = total_ciclo - total_pagado

    if request.method == 'POST':
        try:
            monto = Decimal(request.POST.get('monto'))
        except (InvalidOperation, TypeError):
            messages.error(request, "Monto inválido")
            return redirect('pagos', matricula_id=matricula.id)

        metodo = request.POST.get('metodo_pago')

        nuevo_total = total_pagado + monto

        #validación
        if nuevo_total > total_ciclo:
            messages.error(request, "El monto excede lo que debe pagar")
            return redirect('pagos', matricula_id=matricula.id)

        #guardar pago
        Pago.objects.create(
            matricula=matricula,
            registrado_por=request.user.perfil,
            fecha_pago=date.today(),
            monto=monto,
            metodo_pago=metodo
        )

        # actualizar estado
        if nuevo_total >= total_ciclo:
            matricula.estado = "pagado"
        else:
            matricula.estado = "pendiente"

        matricula.save()

        return redirect('matriculas')

    return render(request, 'web/secretaria/pagos/pagos.html', {
        'matricula': matricula,
        'total_pagado': total_pagado,
        'total_ciclo': total_ciclo,
        'deuda': deuda
    })
@login_required
def cancelar_registro(request):
    request.session.pop('alumno', None)
    request.session.pop('apoderado', None)
    request.session.pop('formacion_academica', None)
    request.session.pop('formacion_adicional', None)

    return redirect('dashboard')
@login_required
def reportes_sedes(request):
    return render(request, 'web/administrador/reportes/reportes_sedes.html')

@login_required
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
def cambiar_estado_alumno(request, alumno_id):
    alumno = Alumno.objects.get(id=alumno_id)

    if alumno.estado == 'activo':
        alumno.estado = 'inactivo'
    else:
        alumno.estado = 'activo'

    alumno.save()

    return redirect('lista_alumnos')
@login_required
def lista_ciclos(request):
    ciclos = Ciclo.objects.all()

    return render(request, 'web/administrador/ciclos/lista.html', {
        'ciclos': ciclos
    })