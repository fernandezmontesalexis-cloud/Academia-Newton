from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Alumno, Apoderado, Sede, FormacionAcademica, FormacionAdicional
from .models import Matricula, Pago, Ciclo
from datetime import date


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

        fecha_nacimiento = request.POST.get('fecha_nacimiento')

        # 🔥 VALIDACIÓN
        if not fecha_nacimiento:
            messages.error(request, "Debes ingresar la fecha de nacimiento")
            return redirect('registrar_alumno')

        request.session['alumno'] = {
            'apellido_paterno': request.POST.get('apellido_paterno'),
            'apellido_materno': request.POST.get('apellido_materno'),
            'nombres': request.POST.get('nombres'),
            'dni': request.POST.get('dni'),
            'celular': request.POST.get('celular'),
            'fecha_nacimiento': fecha_nacimiento,  # ← ya validado
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
        
        request.session['apoderado'] = {
            'nombre_apoderado': request.POST.get('nombre_apoderado'),
            'dni_apoderado': request.POST.get('dni_apoderado'),
            'celular_apoderado': request.POST.get('celular_apoderado'),
            'direccion_apoderado': request.POST.get('direccion_apoderado'),
        }
        return redirect('regis_form_academica')
    return render(request,'web/apoderado/registrar_apoderado.html')

@login_required
def regis_form_academica(request):
    
    if request.method == 'POST':
        request.session['formacion_academica'] = {
            'tipo_institucion':request.POST.get('tipo_institucion'),
            'nombre_ie':request.POST.get('nombre_ie'),
            'distrito_ie':request.POST.get('distrito_ie'),
        }
        return redirect('regis_form_adicional')
    return render(request,'web/formacion/regis_form_academica.html')
@login_required
def regis_form_adicional(request):

    if request.method == 'POST':

        #obteniendo informacion de session
        alumno_data = request.session.get('alumno')
        apoderado_data = request.session.get('apoderado')
        formacion_acad_data = request.session.get('formacion_academica')

        if not alumno_data or not apoderado_data or not formacion_acad_data:
            return redirect('registrar_alumno')

        #apoderado
        apoderado = Apoderado.objects.create(
            nombre_completo = apoderado_data['nombre_apoderado'],
            dni = apoderado_data['dni_apoderado'],
            celular = apoderado_data['celular_apoderado'],
            direccion = apoderado_data['direccion_apoderado']
        )
        #sede
        sede = Sede.objects.get(id=alumno_data['sede'])

        #que no se repita el dni
        dni = alumno_data['dni']
        if Alumno.objects.filter(dni=dni).exists():
                messages.error(request, "este alumno ya esta registrado")
                return redirect('registrar_alumno')

        #alumno
        alumno = Alumno.objects.create(
            apellido_paterno = alumno_data['apellido_paterno'],
            apellido_materno = alumno_data['apellido_materno'],
            nombres = alumno_data['nombres'],
            dni = alumno_data['dni'],
            celular = alumno_data['celular'],
            fecha_nacimiento = alumno_data['fecha_nacimiento'],
            direccion = alumno_data['direccion'],
            distrito = alumno_data['distrito'],
            email = alumno_data['email'],

            sede = sede,
            apoderado = apoderado
        )
        #forma academica
        FormacionAcademica.objects.create(
            alumno = alumno,
            tipo_institucion=formacion_acad_data['tipo_institucion'],
            nombre_ie = formacion_acad_data['nombre_ie'],
            distrito_ie = formacion_acad_data['distrito_ie']
        )
        #forma adicional
        FormacionAdicional.objects.create(
            alumno = alumno,
            estudio_previo = request.POST.get('estudio_previo') == 'si',
            tipo_estudio = request.POST.get('tipo_estudio'),
            academia_anterior = request.POST.get('academia_anterior'),
            carrera_interes = request.POST.get('carrera_interes'),
            segunda_carrera = request.POST.get('segunda_carrera')
        )

                # 🔥 NUEVO CODIGO CORRECTO
        ciclo_id = request.POST.get('ciclo')

        if not ciclo_id:
            messages.error(request, "Debe seleccionar un ciclo")
            return redirect('regis_form_adicional')

        ciclo = Ciclo.objects.get(id=ciclo_id)

        matricula = Matricula.objects.create(
            alumno=alumno,
            ciclo=ciclo,
            fecha_matricula=date.today(),
            estado="pendiente"
        )
        
        #para que se quede limpia la session
        del request.session['alumno']
        del request.session['apoderado']
        del request.session['formacion_academica']

        return redirect('pagos', matricula_id=matricula.id)
    ciclos = Ciclo.objects.all()
    return render(request,'web/formacion/regis_form_adicional.html', {
    'ciclos': ciclos
    })
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')
@login_required
def matriculas(request):
    matriculas = Matricula.objects.select_related('alumno', 'ciclo').all()

    return render(request, 'web/matricula/matricula.html', {
        'matriculas': matriculas
    })
@login_required
def pagos(request, matricula_id):
    matricula = Matricula.objects.get(id=matricula_id)

    if request.method == 'POST':
        fecha = request.POST.get('fecha')
        monto = request.POST.get('monto')
        metodo = request.POST.get('metodo_pago')

        Pago.objects.create(
            matricula=matricula,
            perfil=request.user.perfil,
            fecha_pago=fecha,
            monto=monto,
            metodo_pago=metodo,
            estado="completado"
        )

        return redirect('dashboard')

    return render(request, 'web/pagos/pagos.html', {
        'matricula': matricula
    })