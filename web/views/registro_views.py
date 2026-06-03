from django.shortcuts import render, redirect
from web.permisos import permiso_requerido
from django.contrib.auth.decorators import login_required
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
from ..utils import (
    estado_ciclo_hoy,
    normalizar_nombre,
    normalizar_texto,
    validar_dni,
    validar_celular,
    validar_email,
)


# ══════════════════════════════════════════════════════════════════
#  PASO 1 — Datos del alumno
# ══════════════════════════════════════════════════════════════════

@login_required
@permiso_requerido(["admin", "secretaria"])
def registrar_alumno(request):
    """
    Primer paso del registro: datos personales del alumno.
    Acá también detecto si el alumno ya existe en otra sede — si es así, muestro
    el modal de transferencia en lugar de dejarlo registrar uno nuevo.
    """
    departamentos = Departamento.objects.all()
    hoy = date.today()

    # Calculo el rango de fechas de nacimiento válido (12 a 60 años)
    try:
        fecha_max_iso = date(hoy.year - 12, hoy.month, hoy.day).isoformat()
        fecha_min_iso = date(hoy.year - 61, hoy.month, hoy.day).isoformat()
    except ValueError:
        # Manejo especial para el 29 de febrero en años no bisiestos
        fecha_max_iso = date(hoy.year - 12, hoy.month, 28).isoformat()
        fecha_min_iso = date(hoy.year - 61, hoy.month, 28).isoformat()

    if request.method == "POST":

        # Normalizo los nombres con title-case y sin espacios dobles
        apellido_paterno = normalizar_nombre(request.POST.get("apellido_paterno", ""))
        apellido_materno = normalizar_nombre(request.POST.get("apellido_materno", ""))
        nombres          = normalizar_nombre(request.POST.get("nombres", ""))
        dni              = request.POST.get("dni", "").strip()
        celular          = request.POST.get("celular", "").strip()
        fecha_nacimiento = request.POST.get("fecha_nacimiento", "").strip()
        direccion        = normalizar_texto(request.POST.get("direccion", ""))
        departamento_id  = request.POST.get("departamento")
        provincia_id     = request.POST.get("provincia")
        distrito_id      = request.POST.get("distrito")
        email            = request.POST.get("email", "").strip().lower()

        field_errors = {}

        # ── Validación del DNI ────────────────────────────────────────────
        if not dni:
            field_errors['dni'] = "Debe ingresar un DNI."
        elif len(dni) != 8 or not dni.isdigit():
            field_errors['dni'] = "El DNI debe tener exactamente 8 dígitos."
        else:
            # Busco si ya existe un alumno con ese DNI en cualquier sede
            alumno_existente = Alumno.objects.select_related(
                'sede', 'distrito__provincia__departamento'
            ).filter(dni=dni).first()

            if alumno_existente:
                nombre_completo = f"{alumno_existente.nombres} {alumno_existente.apellido_paterno}"

                if alumno_existente.estado == 'bloqueado':
                    # Alumno bloqueado — no puede matricularse en ninguna sede
                    field_errors['dni'] = (
                        f"El alumno {nombre_completo} está bloqueado y no puede matricularse. "
                        f"Comunícate con el administrador para resolver su situación."
                    )
                else:
                    # Verifico si tiene una matrícula vigente (ciclo que aún no terminó)
                    tiene_matricula_vigente = Matricula.objects.filter(
                        alumno=alumno_existente,
                        ciclo__fecha_fin__gte=hoy,
                    ).exists()

                    if tiene_matricula_vigente:
                        # Ya tiene ciclo activo — no se puede matricular dos veces al mismo tiempo
                        field_errors['dni'] = (
                            f"El alumno {nombre_completo} ya tiene una matrícula activa "
                            f"en la sede {alumno_existente.sede}."
                        )
                    elif alumno_existente.sede == request.perfil.sede:
                        # Está en esta misma sede sin matrícula vigente — usar flujo de Renovar
                        field_errors['dni'] = (
                            f"El alumno {nombre_completo} ya está registrado en esta sede. "
                            f"Búscalo en la lista de Alumnos y usa la opción 'Renovar'."
                        )
                    else:
                        # Está en otra sede sin matrícula vigente → ofrezco transferirlo a esta sede
                        # Preparo los ciclos disponibles en mi sede para mostrar en el modal
                        ciclos_transfer = []
                        for c in Ciclo.objects.filter(sede=request.perfil.sede).order_by('fecha_inicio'):
                            estado = estado_ciclo_hoy(c, hoy)
                            if estado in ('activa', 'pendiente'):
                                c.estado_ciclo = estado
                                ciclos_transfer.append(c)

                        apo = alumno_existente.apoderado
                        return render(
                            request,
                            "web/secretaria/alumnos/registrar_alumno.html",
                            {
                                "alumno":       {},
                                "departamentos": departamentos,
                                "fecha_max_iso": fecha_max_iso,
                                "fecha_min_iso": fecha_min_iso,
                                # Paso los datos del alumno existente para mostrarlos en el modal
                                "transferencia_alumno": {
                                    "id":          alumno_existente.id,
                                    "nombre":      f"{alumno_existente.nombres} {alumno_existente.apellido_paterno} {alumno_existente.apellido_materno}",
                                    "dni":         alumno_existente.dni,
                                    "sede_origen": alumno_existente.sede.nombre,
                                    "celular":     alumno_existente.celular or '',
                                    "email":       alumno_existente.email or '',
                                    "ultimo_ciclo": Matricula.objects.filter(
                                        alumno=alumno_existente
                                    ).order_by('-fecha_matricula').values_list(
                                        'ciclo__nombre', flat=True
                                    ).first() or '—',
                                    "apo":         apo.nombre_completo if apo else '',
                                    "apo_celular": apo.celular if apo else '',
                                },
                                "ciclos_transfer": ciclos_transfer,
                            },
                        )

        # ── Validación del email ──────────────────────────────────────────
        email_error = validar_email(email)
        if email_error:
            field_errors['email'] = email_error

        # ── Validación del celular ────────────────────────────────────────
        if celular and not validar_celular(celular):
            field_errors['celular'] = "El celular debe tener 9 dígitos y comenzar con 9 (ej: 987654321)"

        # ── Validación de la dirección ────────────────────────────────────
        if not direccion:
            field_errors['direccion'] = "La dirección es obligatoria."

        # ── Validación de la fecha de nacimiento ──────────────────────────
        if fecha_nacimiento:
            try:
                fecha_nac = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date()
                if fecha_nac > hoy:
                    field_errors['fecha_nacimiento'] = "La fecha no puede ser futura"
                else:
                    edad = (
                        hoy.year - fecha_nac.year
                        - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
                    )
                    if edad < 12:
                        field_errors['fecha_nacimiento'] = "El alumno debe tener al menos 12 años"
                    elif edad > 60:
                        field_errors['fecha_nacimiento'] = "Edad no válida para este registro (máximo 60 años)"
            except ValueError:
                field_errors['fecha_nacimiento'] = "Formato de fecha inválido"

        # Si hay errores, devuelvo el formulario con los campos ya llenados
        if field_errors:
            def _int_or_none(val):
                try:
                    return int(val) if val else None
                except (ValueError, TypeError):
                    return None

            return render(
                request,
                "web/secretaria/alumnos/registrar_alumno.html",
                {
                    "alumno":        request.POST,
                    "departamentos": departamentos,
                    "field_errors":  field_errors,
                    "fecha_max_iso": fecha_max_iso,
                    "fecha_min_iso": fecha_min_iso,
                    "departamento_seleccionado": _int_or_none(request.POST.get("departamento")),
                    "provincia_seleccionada":    _int_or_none(request.POST.get("provincia")),
                    "distrito_seleccionado":     _int_or_none(request.POST.get("distrito")),
                },
            )

        # Guardo los datos en sesión para llevarlos al siguiente paso
        request.session["alumno"] = {
            "apellido_paterno": apellido_paterno,
            "apellido_materno": apellido_materno,
            "nombres":          nombres,
            "dni":              dni,
            "celular":          celular,
            "fecha_nacimiento": fecha_nacimiento,
            "direccion":        direccion,
            "departamento":     departamento_id,
            "provincia":        provincia_id,
            "distrito":         distrito_id,
            "email":            email,
        }

        return redirect("registrar_apoderado")

    # GET: muestro el formulario, precargando datos si el usuario volvió atrás
    alumno = request.session.get("alumno", {})

    return render(
        request,
        "web/secretaria/alumnos/registrar_alumno.html",
        {
            "alumno":        alumno,
            "departamentos": departamentos,
            "fecha_max_iso": fecha_max_iso,
            "fecha_min_iso": fecha_min_iso,
            "departamento_seleccionado": (
                int(alumno.get("departamento")) if alumno.get("departamento") else None
            ),
            "provincia_seleccionada": (
                int(alumno.get("provincia")) if alumno.get("provincia") else None
            ),
            "distrito_seleccionado": (
                int(alumno.get("distrito")) if alumno.get("distrito") else None
            ),
        },
    )


# ══════════════════════════════════════════════════════════════════
#  PASO 2 — Datos del apoderado
# ══════════════════════════════════════════════════════════════════

@login_required
@permiso_requerido(["admin", "secretaria"])
def registrar_apoderado(request):
    """
    Segundo paso: datos del apoderado (padre/madre/tutor).
    Este paso es completamente opcional — si no se llena nada, simplemente se salta.
    Si se llena algo, exijo al menos nombre y DNI.
    """
    if request.method == "POST":

        nombre    = normalizar_nombre(request.POST.get("nombre_apoderado", ""))
        dni       = request.POST.get("dni_apoderado", "").strip()
        celular   = request.POST.get("celular_apoderado", "").strip()
        direccion = normalizar_texto(request.POST.get("direccion_apoderado", ""))

        field_errors = {}

        # Solo valido si el usuario llenó algún campo — si todos están vacíos, está bien así
        any_filled = any([nombre, dni, celular, direccion])

        if any_filled:
            if not nombre:
                field_errors['nombre_apoderado'] = "Si ingresa datos del apoderado, el nombre es obligatorio"
            if not dni:
                field_errors['dni_apoderado'] = "Si ingresa datos del apoderado, el DNI es obligatorio"
            elif not validar_dni(dni):
                field_errors['dni_apoderado'] = "El DNI debe tener exactamente 8 dígitos numéricos"
            if celular and not validar_celular(celular):
                field_errors['celular_apoderado'] = "El celular debe tener 9 dígitos y comenzar con 9"

        if field_errors:
            return render(
                request,
                "web/secretaria/alumnos/registrar_apoderado.html",
                {"apoderado": request.POST, "field_errors": field_errors},
            )

        # Guardo en sesión para el siguiente paso
        request.session["apoderado"] = {
            "nombre_apoderado":    nombre,
            "dni_apoderado":       dni,
            "celular_apoderado":   celular,
            "direccion_apoderado": direccion,
        }

        return redirect("regis_form_academica")

    apoderado = request.session.get("apoderado", {})

    return render(
        request,
        "web/secretaria/alumnos/registrar_apoderado.html",
        {"apoderado": apoderado},
    )


# ══════════════════════════════════════════════════════════════════
#  PASO 3 — Formación académica (colegio de procedencia)
# ══════════════════════════════════════════════════════════════════

@login_required
@permiso_requerido(["admin", "secretaria"])
def regis_form_academica(request):
    departamentos = Departamento.objects.all()

    if request.method == "POST":
        colegio_id = request.POST.get("colegio_id", "").strip()

        field_errors = {}
        colegio      = None

        # El colegio es obligatorio — el usuario debe buscarlo o crear uno nuevo
        if not colegio_id:
            field_errors['colegio'] = (
                "Debes seleccionar un colegio de la lista o crear uno nuevo con '+ Agregar colegio'"
            )
        else:
            colegio = InstitucionEducativa.objects.filter(id=colegio_id).first()
            if not colegio:
                field_errors['colegio'] = "El colegio seleccionado no existe. Selecciona uno válido o créalo."

        if field_errors:
            colegio_nombre = colegio.nombre if colegio else ""
            return render(
                request,
                "web/secretaria/alumnos/regis_form_academica.html",
                {
                    "formacion": {
                        "colegio_id":     colegio_id,
                        "colegio_nombre": colegio_nombre,
                    },
                    "departamentos": departamentos,
                    "field_errors":  field_errors,
                },
            )

        # El tipo de institución (Nacional/Particular) viene del colegio, no del formulario
        tipo_institucion = colegio.tipo_ie if colegio else ""

        request.session["formacion_academica"] = {
            "tipo_institucion": tipo_institucion,
            "colegio_id":       colegio_id,
        }
        return redirect("regis_form_adicional")

    # GET: recupero el nombre del colegio si ya fue seleccionado antes
    formacion      = request.session.get("formacion_academica", {})
    colegio_nombre = ""
    if formacion.get("colegio_id"):
        ie = InstitucionEducativa.objects.filter(id=formacion["colegio_id"]).first()
        if ie:
            colegio_nombre = ie.nombre
    formacion = dict(formacion)
    formacion["colegio_nombre"] = colegio_nombre

    return render(
        request,
        "web/secretaria/alumnos/regis_form_academica.html",
        {"formacion": formacion, "departamentos": departamentos},
    )


# ══════════════════════════════════════════════════════════════════
#  PASO 4 — Información adicional + selección de ciclo
#           Este es el paso final que crea todo en la base de datos
# ══════════════════════════════════════════════════════════════════

@login_required
@permiso_requerido(["admin", "secretaria"])
def regis_form_adicional(request):
    today = date.today()

    # Solo muestro ciclos activos o próximos de esta sede para que elija la secretaria
    ciclos_disponibles = []
    for c in Ciclo.objects.filter(sede=request.perfil.sede).order_by('fecha_inicio'):
        estado = estado_ciclo_hoy(c, today)
        if estado in ('activa', 'pendiente'):
            c.estado_ciclo = estado
            ciclos_disponibles.append(c)

    if request.method == "POST":

        estudio_previo = request.POST.get("estudio_previo", "no")
        tipo_estudio   = request.POST.get("tipo_estudio", "")
        academia_anterior = (
            normalizar_nombre(request.POST.get("academia_anterior", ""))
            if estudio_previo == "si" else ""
        )
        carrera_interes = normalizar_nombre(request.POST.get("carrera_interes", ""))
        segunda_carrera = normalizar_nombre(request.POST.get("segunda_carrera", ""))
        ciclo_id        = request.POST.get("ciclo", "").strip()

        field_errors = {}

        if estudio_previo == "si" and not academia_anterior:
            field_errors['academia_anterior'] = "Debes ingresar el nombre de la academia anterior"

        # Valido que el ciclo seleccionado exista y esté disponible
        ciclo = None
        if not ciclo_id:
            field_errors['ciclo'] = "Debes seleccionar un ciclo"
        else:
            try:
                ciclo = Ciclo.objects.get(id=int(ciclo_id))
                if estado_ciclo_hoy(ciclo, today) not in ('activa', 'pendiente'):
                    field_errors['ciclo'] = "El ciclo seleccionado no está disponible"
            except (Ciclo.DoesNotExist, ValueError):
                field_errors['ciclo'] = "Ciclo inválido"

        if field_errors:
            return render(
                request,
                "web/secretaria/alumnos/regis_form_adicional.html",
                {
                    "formacion_adicional": request.POST,
                    "ciclos":              ciclos_disponibles,
                    "ciclo_seleccionado":  (
                        int(ciclo_id) if ciclo_id and ciclo_id.isdigit() else None
                    ),
                    "field_errors": field_errors,
                },
            )

        # Verifico que los datos de los pasos anteriores sigan en sesión
        # — si el usuario entró directo a esta URL sin pasar por los pasos anteriores, lo mando al inicio
        alumno_data       = request.session.get("alumno")
        apoderado_data    = request.session.get("apoderado")
        formacion_acad_data = request.session.get("formacion_academica")

        if not alumno_data or not formacion_acad_data:
            return redirect("registrar_alumno")

        # ── Crear apoderado ───────────────────────────────────────────────
        # Solo creo el apoderado si tiene nombre y DNI (campos mínimos requeridos)
        # Uso get_or_create por DNI — si ya existe lo actualizo con los nuevos datos
        apoderado = None
        if (
            apoderado_data
            and apoderado_data.get("nombre_apoderado")
            and apoderado_data.get("dni_apoderado")
        ):
            apoderado, created = Apoderado.objects.get_or_create(
                dni=apoderado_data["dni_apoderado"],
                defaults={
                    "nombre_completo": apoderado_data["nombre_apoderado"],
                    "celular":         apoderado_data["celular_apoderado"],
                    "direccion":       apoderado_data["direccion_apoderado"],
                },
            )
            if not created:
                # El apoderado ya existía — actualizo sus datos con los del formulario
                apoderado.nombre_completo = apoderado_data["nombre_apoderado"]
                apoderado.celular         = apoderado_data["celular_apoderado"]
                apoderado.direccion       = apoderado_data["direccion_apoderado"]
                apoderado.save()

        sede = request.perfil.sede

        # Busco el distrito seleccionado en el paso 1
        distrito = None
        distrito_id = alumno_data.get("distrito")
        if distrito_id:
            distrito = Distrito.objects.filter(id=distrito_id).first()

        # ── Crear el alumno ───────────────────────────────────────────────
        alumno = Alumno.objects.create(
            apellido_paterno=alumno_data["apellido_paterno"],
            apellido_materno=alumno_data["apellido_materno"],
            nombres=          alumno_data["nombres"],
            dni=              alumno_data["dni"],
            celular=          alumno_data["celular"],
            fecha_nacimiento= alumno_data["fecha_nacimiento"],
            direccion=        alumno_data["direccion"],
            distrito=         distrito,
            email=            alumno_data["email"],
            estado=           "activo",
            sede=             sede,
            apoderado=        apoderado,
        )

        # ── Guardar formación académica ───────────────────────────────────
        colegio = InstitucionEducativa.objects.filter(
            id=formacion_acad_data.get("colegio_id")
        ).first()
        FormacionAcademica.objects.update_or_create(
            alumno=alumno,
            defaults={
                'tipo_institucion': formacion_acad_data["tipo_institucion"],
                'institucion':      colegio,
            },
        )

        # ── Guardar formación adicional ───────────────────────────────────
        FormacionAdicional.objects.update_or_create(
            alumno=alumno,
            defaults={
                'estudio_previo':    estudio_previo == "si",
                'tipo_estudio':      tipo_estudio,
                'academia_anterior': academia_anterior,
                'carrera_interes':   carrera_interes,
                'segunda_carrera':   segunda_carrera,
            },
        )

        # ── Crear la matrícula ────────────────────────────────────────────
        matricula = Matricula.objects.create(
            alumno=          alumno,
            ciclo=           ciclo,
            fecha_matricula= today,
            estado=          "pendiente",
            registrado_por=  request.perfil,
        )

        # Limpio la sesión — ya no necesito los datos del flujo de registro
        request.session.pop("alumno",              None)
        request.session.pop("apoderado",           None)
        request.session.pop("formacion_academica", None)
        request.session.pop("formacion_adicional", None)

        # Mando a registrar el pago — la matrícula queda "pendiente" hasta que se pague
        return redirect("pagos", matricula_id=matricula.id)

    # GET: muestro el formulario con datos previos si el usuario volvió atrás
    formacion_adicional = request.session.get("formacion_adicional", {})

    return render(
        request,
        "web/secretaria/alumnos/regis_form_adicional.html",
        {
            "formacion_adicional": formacion_adicional,
            "ciclos":              ciclos_disponibles,
            "ciclo_seleccionado":  (
                int(formacion_adicional.get("ciclo"))
                if formacion_adicional.get("ciclo")
                else None
            ),
        },
    )


# ══════════════════════════════════════════════════════════════════
#  Acciones auxiliares del flujo de registro
# ══════════════════════════════════════════════════════════════════

@login_required
@permiso_requerido(["admin", "secretaria"])
def cancelar_registro(request):
    # Limpio toda la sesión del registro y mando al dashboard
    request.session.pop("alumno",              None)
    request.session.pop("apoderado",           None)
    request.session.pop("formacion_academica", None)
    request.session.pop("formacion_adicional", None)
    return redirect("dashboard")


@login_required
def get_provincias(request, departamento_id):
    # Devuelvo las provincias del departamento seleccionado — lo usa el selector en cascada
    provincias = Provincia.objects.filter(departamento_id=departamento_id)
    data = list(provincias.values("id", "nombre"))
    return JsonResponse(data, safe=False)


@login_required
def get_distritos(request, provincia_id):
    # Devuelvo los distritos de la provincia seleccionada — lo usa el selector en cascada
    distritos = Distrito.objects.filter(provincia_id=provincia_id)
    data = list(distritos.values("id", "nombre"))
    return JsonResponse(data, safe=False)


@login_required
def buscar_colegios(request):
    # Búsqueda de colegios por nombre — devuelvo máximo 10 resultados para el autocomplete
    q       = request.GET.get("q", "")
    colegios = InstitucionEducativa.objects.filter(nombre__icontains=q)[:10]
    data    = list(colegios.values("id", "nombre", "tipo_ie"))
    return JsonResponse(data, safe=False)


@login_required
@permiso_requerido(["admin", "secretaria"])
def crear_colegio(request):
    """Crea un nuevo colegio desde el modal del paso 3 — responde en JSON para el frontend."""
    if request.method == "POST":
        data = json.loads(request.body)

        nombre     = normalizar_nombre(data.get("nombre", ""))
        distrito_id = data.get("distrito")
        tipo_ie    = (data.get("tipo_ie") or "").strip()

        if not nombre:
            return JsonResponse({"error": "El nombre del colegio es obligatorio"}, status=400)
        if not distrito_id:
            return JsonResponse(
                {"error": "Debes seleccionar departamento, provincia y distrito"}, status=400
            )
        if not tipo_ie:
            return JsonResponse(
                {"error": "Debes seleccionar el tipo de institución (Nacional o Particular)"}, status=400
            )
        if tipo_ie not in ("Nacional", "Particular"):
            return JsonResponse({"error": "Tipo de institución inválido"}, status=400)
        if not Distrito.objects.filter(id=distrito_id).exists():
            return JsonResponse({"error": "El distrito seleccionado no existe"}, status=400)
        if InstitucionEducativa.objects.filter(nombre__iexact=nombre).exists():
            return JsonResponse({"error": "Este colegio ya se encuentra registrado."}, status=400)

        colegio = InstitucionEducativa.objects.create(
            nombre=      nombre,
            distrito_id= distrito_id,
            tipo_ie=     tipo_ie,
        )

        return JsonResponse({"id": colegio.id, "nombre": colegio.nombre, "tipo_ie": colegio.tipo_ie})


@login_required
@permiso_requerido(["admin", "secretaria"])
def nuevo_registro(request):
    # Limpio la sesión y arranco el flujo de registro desde cero
    request.session.pop("alumno",              None)
    request.session.pop("apoderado",           None)
    request.session.pop("formacion_academica", None)
    request.session.pop("formacion_adicional", None)
    return redirect("registrar_alumno")
