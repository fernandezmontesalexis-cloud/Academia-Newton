from django.shortcuts import render, redirect
from web.permisos import permiso_requerido
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import json

from ..models import (
    Alumno,
    Apoderado,
    FormacionAcademica,
    FormacionAdicional,
    Matricula,
    Ciclo,
    Provincia,
    Distrito,
    Departamento,
    InstitucionEducativa,
)
from datetime import datetime, date


@login_required
@permiso_requerido(["admin", "secretaria"])
def registrar_alumno(request):

    departamentos = Departamento.objects.all()

    if request.method == "POST":

        apellido_paterno = request.POST.get("apellido_paterno")
        apellido_materno = request.POST.get("apellido_materno")
        nombres = request.POST.get("nombres")
        dni = request.POST.get("dni")
        celular = request.POST.get("celular")

        fecha_nacimiento = request.POST.get("fecha_nacimiento")
        direccion = request.POST.get("direccion")
        distrito_id = request.POST.get("distrito")
        email = request.POST.get("email")

        if not dni:
            messages.error(request, "El DNI es obligatorio")
            return render(
                request,
                "web/secretaria/alumnos/registrar_alumno.html",
                {"alumno": request.POST, "departamentos": departamentos},
            )

        if len(dni) != 8 or not dni.isdigit():
            messages.error(request, "El DNI debe tener 8 números")
            return render(
                request,
                "web/secretaria/alumnos/registrar_alumno.html",
                {"alumno": request.POST, "departamentos": departamentos},
            )

        if Alumno.objects.filter(dni=dni).exists():
            messages.error(request, "Este DNI ya está registrado")
            return render(
                request,
                "web/secretaria/alumnos/registrar_alumno.html",
                {"alumno": request.POST, "departamentos": departamentos},
            )

        if not fecha_nacimiento:
            messages.error(request, "Debes ingresar la fecha de nacimiento")
            return render(
                request,
                "web/secretaria/alumnos/registrar_alumno.html",
                {"alumno": request.POST, "departamentos": departamentos},
            )

        #  VALIDACIÓN DE FECHA Y EDAD
        try:
            fecha_nac = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Fecha inválida")
            return render(
                request,
                "web/secretaria/alumnos/registrar_alumno.html",
                {"alumno": request.POST, "departamentos": departamentos},
            )

        hoy = date.today()

        # no permitir fechas futuras
        if fecha_nac > hoy:
            messages.error(request, "La fecha no puede ser futura")
            return render(
                request,
                "web/secretaria/alumnos/registrar_alumno.html",
                {"alumno": request.POST, "departamentos": departamentos},
            )

        # calcular edad
        edad = (
            hoy.year
            - fecha_nac.year
            - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
        )

        # muy joven (ej: 2020)
        if edad < 12:
            messages.error(request, "El alumno debe tener al menos 12 años")
            return render(
                request,
                "web/secretaria/alumnos/registrar_alumno.html",
                {"alumno": request.POST, "departamentos": departamentos},
            )

        # edad poco
        if edad > 60:
            messages.error(request, "Edad no válida para este registro")
            return render(
                request,
                "web/secretaria/alumnos/registrar_alumno.html",
                {"alumno": request.POST, "departamentos": departamentos},
            )

        # guardar en session
        request.session["alumno"] = {
            "apellido_paterno": apellido_paterno,
            "apellido_materno": apellido_materno,
            "nombres": nombres,
            "dni": dni,
            "celular": celular,
            "fecha_nacimiento": fecha_nacimiento,
            "direccion": direccion,
            "distrito": distrito_id,
            "email": email,
        }

        return redirect("registrar_apoderado")

    # GET
    alumno = request.session.get("alumno", {})

    return render(
        request,
        "web/secretaria/alumnos/registrar_alumno.html",
        {"alumno": alumno, "departamentos": departamentos},
    )


@login_required
@permiso_requerido(["admin", "secretaria"])
def registrar_apoderado(request):

    if request.method == "POST":

        request.session["apoderado"] = {
            "nombre_apoderado": request.POST.get("nombre_apoderado"),
            "dni_apoderado": request.POST.get("dni_apoderado"),
            "celular_apoderado": request.POST.get("celular_apoderado"),
            "direccion_apoderado": request.POST.get("direccion_apoderado"),
        }
        return redirect("regis_form_academica")
    apoderado = request.session.get("apoderado", {})

    return render(
        request,
        "web/secretaria/alumnos/registrar_apoderado.html",
        {"apoderado": apoderado},
    )


@login_required
@permiso_requerido(["admin", "secretaria"])
def regis_form_academica(request):

    departamentos = Departamento.objects.all()

    if request.method == "POST":
        request.session["formacion_academica"] = {
            "tipo_institucion": request.POST.get("tipo_institucion"),
            "colegio_id": request.POST.get("colegio_id"),
        }
        return redirect("regis_form_adicional")
        # ESTO VA FUERA DEL IF
    formacion = request.session.get("formacion_academica", {})

    return render(
        request,
        "web/secretaria/alumnos/regis_form_academica.html",
        {"formacion": formacion, "departamentos": departamentos},
    )


@login_required
@permiso_requerido(["admin", "secretaria"])
def regis_form_adicional(request):

    if request.method == "POST":

        request.session["formacion_adicional"] = {
            "estudio_previo": request.POST.get("estudio_previo"),
            "tipo_estudio": request.POST.get("tipo_estudio"),
            "academia_anterior": request.POST.get("academia_anterior"),
            "carrera_interes": request.POST.get("carrera_interes"),
            "segunda_carrera": request.POST.get("segunda_carrera"),
            "ciclo": request.POST.get("ciclo"),
        }

        alumno_data = request.session.get("alumno")
        apoderado_data = request.session.get("apoderado")
        formacion_acad_data = request.session.get("formacion_academica")

        if not alumno_data or not formacion_acad_data:
            return redirect("registrar_alumno")

        # apoderado opcional
        # apoderado opcional

        apoderado = None

        if apoderado_data and apoderado_data.get("nombre_apoderado"):

            apoderado, created = Apoderado.objects.get_or_create(
                dni=apoderado_data["dni_apoderado"],
                defaults={
                    "nombre_completo": apoderado_data["nombre_apoderado"],
                    "celular": apoderado_data["celular_apoderado"],
                    "direccion": apoderado_data["direccion_apoderado"],
                },
            )

            # 🔥 actualizar si ya existía
            if not created:
                apoderado.nombre_completo = apoderado_data["nombre_apoderado"]
                apoderado.celular = apoderado_data["celular_apoderado"]
                apoderado.direccion = apoderado_data["direccion_apoderado"]
                apoderado.save()

        sede = request.user.perfil.sede

        distrito = None

        distrito_id = alumno_data.get("distrito")

        if distrito_id:
            distrito = Distrito.objects.filter(id=distrito_id).first()

        alumno = Alumno.objects.create(
            apellido_paterno=alumno_data["apellido_paterno"],
            apellido_materno=alumno_data["apellido_materno"],
            nombres=alumno_data["nombres"],
            dni=alumno_data["dni"],
            celular=alumno_data["celular"],
            fecha_nacimiento=alumno_data["fecha_nacimiento"],
            direccion=alumno_data["direccion"],
            distrito=distrito,
            email=alumno_data["email"],
            estado="activo",
            sede=sede,
            apoderado=apoderado,
        )
        colegio = InstitucionEducativa.objects.filter(
            id=formacion_acad_data.get("colegio_id")
        ).first()
        FormacionAcademica.objects.create(
            alumno=alumno,
            tipo_institucion=formacion_acad_data["tipo_institucion"],
            institucion=colegio,
        )

        form_adicional = request.session.get("formacion_adicional")

        FormacionAdicional.objects.create(
            alumno=alumno,
            estudio_previo=form_adicional["estudio_previo"] == "si",
            tipo_estudio=form_adicional["tipo_estudio"],
            academia_anterior=form_adicional["academia_anterior"],
            carrera_interes=form_adicional["carrera_interes"],
            segunda_carrera=form_adicional["segunda_carrera"],
        )

        ciclo_id = form_adicional.get("ciclo")

        if not ciclo_id or ciclo_id == "":
            messages.error(request, "Debe seleccionar un ciclo")
            return redirect("regis_form_adicional")

        try:
            ciclo = Ciclo.objects.get(id=int(ciclo_id))
        except (Ciclo.DoesNotExist, ValueError):
            messages.error(request, "Ciclo inválido")
            return redirect("regis_form_adicional")

        matricula = Matricula.objects.create(
            alumno=alumno,
            ciclo=ciclo,
            fecha_matricula=date.today(),
            estado="pendiente",
            registrado_por=request.user.perfil,
        )

        # limpiar sesión
        request.session.pop("alumno", None)
        request.session.pop("apoderado", None)
        request.session.pop("formacion_academica", None)
        request.session.pop("formacion_adicional", None)

        return redirect("pagos", matricula_id=matricula.id)

    ciclos = Ciclo.objects.filter(sede=request.user.perfil.sede)
    formacion_adicional = request.session.get("formacion_adicional", {})

    return render(
        request,
        "web/secretaria/alumnos/regis_form_adicional.html",
        {"formacion_adicional": formacion_adicional, "ciclos": ciclos},
    )


@login_required
@permiso_requerido(["admin", "secretaria"])
def cancelar_registro(request):
    request.session.pop("alumno", None)
    request.session.pop("apoderado", None)
    request.session.pop("formacion_academica", None)
    request.session.pop("formacion_adicional", None)

    return redirect("dashboard")


@login_required
def get_provincias(request, departamento_id):
    provincias = Provincia.objects.filter(departamento_id=departamento_id)
    data = list(provincias.values("id", "nombre"))
    return JsonResponse(data, safe=False)


@login_required
def get_distritos(request, provincia_id):
    distritos = Distrito.objects.filter(provincia_id=provincia_id)
    data = list(distritos.values("id", "nombre"))
    return JsonResponse(data, safe=False)


@login_required
def buscar_colegios(request):
    q = request.GET.get("q", "")

    colegios = InstitucionEducativa.objects.filter(nombre__icontains=q)[:10]

    data = list(colegios.values("id", "nombre"))

    return JsonResponse(data, safe=False)


@login_required
@permiso_requerido(["admin", "secretaria"])
def crear_colegio(request):
    if request.method == "POST":
        data = json.loads(request.body)

        nombre = data.get("nombre")
        distrito_id = data.get("distrito")

        if not nombre or not distrito_id:
            return JsonResponse({"error": "Faltan datos"}, status=400)

        colegio = InstitucionEducativa.objects.create(
            nombre=nombre, distrito_id=distrito_id
        )

        return JsonResponse({"id": colegio.id, "nombre": colegio.nombre})
