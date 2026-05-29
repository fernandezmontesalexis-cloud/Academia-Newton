from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.utils import timezone
from web.permisos import permiso_requerido
from web.models import Perfil, Sede
from ..models import Ciclo
from ..utils import estado_ciclo_hoy


@login_required
@permiso_requerido(['admin'])
def lista_ciclos(request):
    from datetime import date as _date
    hoy = _date.today()
    sedes = Sede.objects.all()
    data_sedes = []
    for sede in sedes:
        ciclos = Ciclo.objects.filter(sede=sede)
        # Mismo criterio que estado_ciclo_hoy == 'activa'
        ciclos_activos = ciclos.filter(
            fecha_inicio__lte=hoy, fecha_fin__gte=hoy
        ).count()
        proximo = ciclos.filter(fecha_inicio__gt=hoy).order_by('fecha_inicio').first()
        ultimo = ciclos.order_by('-fecha_inicio').first()
        data_sedes.append({
            'sede': sede,
            'total_ciclos': ciclos.count(),
            'ciclos_activos': ciclos_activos,
            'proximo_inicio': proximo.fecha_inicio if proximo else None,
            'ultimo_ciclo': ultimo.nombre if ultimo else None,
        })
    return render(request, "web/administrador/ciclos/lista_ciclos.html", {"data_sedes": data_sedes})


@login_required
@permiso_requerido(['admin'])
def ciclos_sede_detalle(request, sede_id):
    from datetime import date as _date
    hoy = _date.today()
    sede = get_object_or_404(Sede, id=sede_id)
    ciclos = list(Ciclo.objects.filter(sede=sede).order_by('-fecha_inicio'))
    for c in ciclos:
        c.estado_ciclo = estado_ciclo_hoy(c, hoy)
        total_dias = (c.fecha_fin - c.fecha_inicio).days
        if total_dias > 0:
            c.progreso = max(0, min(100, int((hoy - c.fecha_inicio).days / total_dias * 100)))
        else:
            c.progreso = 100
        c.tiene_matriculas = c.matricula_set.exists()
    from django.core.paginator import Paginator
    # Separar activos/próximos de finalizados
    orden = {'activa': 0, 'pendiente': 1}
    activos_proximos = sorted(
        [c for c in ciclos if c.estado_ciclo in ('activa', 'pendiente')],
        key=lambda c: orden.get(c.estado_ciclo, 2)
    )
    finalizados = [c for c in ciclos if c.estado_ciclo == 'finalizada']
    # Paginación del historial
    paginator = Paginator(finalizados, 10)
    hpage = request.GET.get('hpage', 1)
    finalizados_page = paginator.get_page(hpage)
    historial_abierto = 'hpage' in request.GET
    return render(request, "web/administrador/ciclos/ciclos_sede_detalle.html", {
        "sede": sede,
        "activos_proximos": activos_proximos,
        "finalizados_page": finalizados_page,
        "historial_abierto": historial_abierto,
        "total_finalizados": len(finalizados),
    })


@login_required
@permiso_requerido(['admin'])
def lista_sedes(request):
    sedes = Sede.objects.all()
    data_sedes = []
    for sede in sedes:
        data_sedes.append({
            'sede': sede,
            'usuarios_count': sede.perfil_set.count(),
            'alumnos_count': sede.alumno_set.count(),
        })
    return render(request, 'web/administrador/sedes/lista_sedes.html', {'data_sedes': data_sedes})


@login_required
@permiso_requerido(['admin'])
def crear_sede(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        direccion = request.POST.get("direccion", "").strip()
        if not nombre:
            messages.error(request, "El nombre es obligatorio")
            return render(request, "web/administrador/sedes/crear_sede.html", {"direccion": direccion})
        Sede.objects.create(nombre=nombre, direccion=direccion, is_active=True)
        return redirect("lista_sedes")
    return render(request, "web/administrador/sedes/crear_sede.html")


@login_required
@permiso_requerido(['admin'])
def editar_sede(request, id):
    sede = get_object_or_404(Sede, id=id)
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        direccion = request.POST.get("direccion", "").strip()
        if not nombre:
            messages.error(request, "El nombre es obligatorio")
            return render(request, "web/administrador/sedes/editar_sede.html", {"sede": sede})
        sede.nombre = nombre
        sede.direccion = direccion
        sede.is_active = request.POST.get("is_active") == "1"
        sede.save()
        return redirect("lista_sedes")
    return render(request, "web/administrador/sedes/editar_sede.html", {"sede": sede})


@login_required
@permiso_requerido(['admin'])
def eliminar_sede(request, id):
    sede = get_object_or_404(Sede, id=id)
    sede.is_active = False
    sede.save()
    return redirect("lista_sedes")


@login_required
@permiso_requerido(['admin'])
def reactivar_sede(request, id):
    sede = get_object_or_404(Sede, id=id)
    sede.is_active = True
    sede.save()
    return redirect("lista_sedes")


@login_required
@permiso_requerido(['admin'])
def crear_usuario(request):
    sedes = Sede.objects.filter(is_active=True)
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email    = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirmar_password = request.POST.get("confirmar_password", "")
        tipo_usuario = request.POST.get("tipo_usuario")
        sede_id = request.POST.get("sede")

        def render_error(msg):
            return render(request, "web/administrador/usuarios/crear_usuario.html", {
                "error": msg, "sedes": sedes,
                "username": username, "email": email,
                "tipo_usuario": tipo_usuario, "sede_id": sede_id,
            })

        if not username or not password:
            return render_error("El usuario y la contraseña son obligatorios")
        if password != confirmar_password:
            return render_error("Las contraseñas no coinciden")
        if len(password) < 6:
            return render_error("La contraseña debe tener al menos 6 caracteres")
        if User.objects.filter(username=username).exists():
            return render_error("Ese nombre de usuario ya existe")

        user = User.objects.create(username=username, email=email, password=make_password(password))
        Perfil.objects.create(user=user, tipo_usuario=tipo_usuario, sede_id=sede_id, activo=True)
        return redirect("lista_usuarios")

    return render(request, "web/administrador/usuarios/crear_usuario.html", {"sedes": sedes})


@login_required
@permiso_requerido(['admin'])
def lista_usuarios(request):
    from django.db.models import Prefetch
    from django.core.paginator import Paginator

    # Prefetch solo el perfil activo de cada usuario para evitar N+1
    base_qs = (
        User.objects
        .prefetch_related(
            Prefetch(
                'perfiles',
                queryset=Perfil.objects.filter(activo=True).select_related('sede'),
                to_attr='perfil_activo'
            )
        )
        .filter(perfiles__activo=True)
        .distinct()
    )

    # Activos evaluados en memoria para ordenar y contar sin queries extra
    activos_list = list(base_qs.filter(is_active=True))
    usuarios_activos = sorted(
        activos_list,
        key=lambda u: (
            0 if u.perfil_activo and u.perfil_activo[0].tipo_usuario == 'admin' else 1,
            u.username,
        )
    )
    total_admins     = sum(1 for u in activos_list if u.perfil_activo and u.perfil_activo[0].tipo_usuario == 'admin')
    total_secretarias = sum(1 for u in activos_list if u.perfil_activo and u.perfil_activo[0].tipo_usuario == 'secretaria')

    # Inactivos: paginados
    usuarios_inactivos_qs = base_qs.filter(is_active=False).order_by('username')
    paginator = Paginator(usuarios_inactivos_qs, 10)
    hpage = request.GET.get('hpage', 1)
    inactivos_page = paginator.get_page(hpage)
    historial_abierto = 'hpage' in request.GET

    return render(request, "web/administrador/usuarios/lista_usuarios.html", {
        "usuarios_activos":   usuarios_activos,
        "inactivos_page":     inactivos_page,
        "historial_abierto":  historial_abierto,
        "total_inactivos":    usuarios_inactivos_qs.count(),
        "total":              base_qs.count(),
        "total_admins":       total_admins,
        "total_secretarias":  total_secretarias,
        "total_activos":      len(activos_list),
    })


@login_required
@permiso_requerido(['admin'])
def editar_usuario(request, id):
    user = get_object_or_404(User, id=id)
    perfil = user.perfiles.filter(activo=True).select_related('sede').first()
    sedes = Sede.objects.all()

    if request.method == "POST":
        user.username      = request.POST.get("username")
        user.email         = request.POST.get("email", "").strip()
        user.is_active     = request.POST.get("is_active") == "1"
        nueva_sede_id      = request.POST.get("sede")
        nuevo_tipo_usuario = request.POST.get("tipo_usuario")

        nueva_password     = request.POST.get("nueva_password", "").strip()
        confirmar_password = request.POST.get("confirmar_password", "").strip()

        if nueva_password:
            if nueva_password != confirmar_password:
                return render(request, "web/administrador/usuarios/editar_usuario.html", {
                    "user": user, "perfil": perfil, "sedes": sedes,
                    "error_password": "Las contraseñas no coinciden",
                })
            if len(nueva_password) < 6:
                return render(request, "web/administrador/usuarios/editar_usuario.html", {
                    "user": user, "perfil": perfil, "sedes": sedes,
                    "error_password": "La contraseña debe tener al menos 6 caracteres",
                })
            user.set_password(nueva_password)
            update_session_auth_hash(request, user)

        user.save()

        # Si cambia de sede: desactiva el perfil actual y crea uno nuevo
        # en la sede destino para preservar el historial por sede.
        sede_cambio = str(perfil.sede_id) != str(nueva_sede_id)
        if sede_cambio:
            perfil.activo = False
            perfil.save()
            Perfil.objects.create(
                user=user,
                tipo_usuario=nuevo_tipo_usuario,
                sede_id=nueva_sede_id,
                activo=True,
            )
        else:
            # Misma sede: solo actualiza el tipo de usuario
            perfil.tipo_usuario = nuevo_tipo_usuario
            perfil.save()

        return redirect("lista_usuarios")

    return render(request, "web/administrador/usuarios/editar_usuario.html", {
        "user": user,
        "perfil": perfil,
        "sedes": sedes,
    })


@login_required
@permiso_requerido(['admin'])
def eliminar_usuario(request, id):
    user = get_object_or_404(User, id=id)
    user.is_active = False
    user.save()
    perfil = user.perfiles.filter(activo=True).first()
    if perfil:
        perfil.fecha_desactivacion = timezone.now()
        perfil.save()
    return redirect("lista_usuarios")


@login_required
@permiso_requerido(['admin'])
def reactivar_usuario(request, id):
    user = get_object_or_404(User, id=id)
    user.is_active = True
    user.save()
    perfil = user.perfiles.filter(activo=True).first()
    if perfil:
        perfil.fecha_desactivacion = None
        perfil.save()
    return redirect("lista_usuarios")


@login_required
@permiso_requerido(['admin'])
def configuracion(request):
    return render(request, 'web/administrador/configuracion/configuracion.html')


@login_required
@permiso_requerido(['admin'])
def editar_ciclo(request, id):
    from decimal import Decimal, InvalidOperation
    from datetime import date as _date
    ciclo = get_object_or_404(Ciclo, id=id)
    tiene_matriculas = ciclo.matricula_set.exists()
    estado_ciclo = estado_ciclo_hoy(ciclo, _date.today())

    def _ctx(extra=None):
        base = {"ciclo": ciclo, "tiene_matriculas": tiene_matriculas, "estado_ciclo": estado_ciclo}
        if extra:
            base.update(extra)
        return base

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        precio = request.POST.get("precio")
        fecha_inicio = request.POST.get("fecha_inicio")
        fecha_fin = request.POST.get("fecha_fin")
        if not nombre or not precio or not fecha_inicio or not fecha_fin:
            messages.error(request, "Todos los campos son obligatorios")
            return render(request, "web/administrador/ciclos/editar_ciclo.html", _ctx())
        try:
            precio_dec = Decimal(precio)
            if precio_dec <= 0:
                raise ValueError
            if precio_dec % Decimal('0.50') != 0:
                messages.error(request, "El precio debe ser en soles enteros o medios (ej. S/. 300.00 o S/. 300.50)")
                return render(request, "web/administrador/ciclos/editar_ciclo.html", _ctx())
        except (InvalidOperation, ValueError):
            messages.error(request, "El precio ingresado no es válido")
            return render(request, "web/administrador/ciclos/editar_ciclo.html", _ctx())
        ciclo.nombre = nombre
        ciclo.precio = precio_dec
        ciclo.fecha_inicio = fecha_inicio
        ciclo.fecha_fin = fecha_fin
        ciclo.save()
        return redirect("ciclos_sede_detalle", sede_id=ciclo.sede.id)
    return render(request, "web/administrador/ciclos/editar_ciclo.html", _ctx())


@login_required
@permiso_requerido(['admin'])
def eliminar_ciclo(request, id):
    ciclo = get_object_or_404(Ciclo, id=id)
    sede_id = ciclo.sede.id
    if ciclo.matricula_set.exists():
        messages.error(request, f"No se puede eliminar '{ciclo.nombre}': tiene matrículas registradas.")
        return redirect("ciclos_sede_detalle", sede_id=sede_id)
    ciclo.delete()
    return redirect("ciclos_sede_detalle", sede_id=sede_id)

@login_required
@permiso_requerido(['admin'])
def crear_ciclo(request):
    from decimal import Decimal, InvalidOperation
    sedes = Sede.objects.all()
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        precio = request.POST.get("precio")
        fecha_inicio = request.POST.get("fecha_inicio")
        fecha_fin = request.POST.get("fecha_fin")
        alcance = request.POST.get("alcance")
        sede_id = request.POST.get("sede_id")

        if not nombre or not precio or not fecha_inicio or not fecha_fin:
            messages.error(request, "Todos los campos son obligatorios")
            return render(request, "web/administrador/ciclos/crear_ciclo.html", {"sedes": sedes})

        try:
            precio_dec = Decimal(precio)
            if precio_dec <= 0:
                raise ValueError
            if precio_dec % Decimal('0.50') != 0:
                messages.error(request, "El precio debe ser en soles enteros o medios (ej. S/. 300.00 o S/. 300.50)")
                return render(request, "web/administrador/ciclos/crear_ciclo.html", {"sedes": sedes})
        except (InvalidOperation, ValueError):
            messages.error(request, "El precio ingresado no es válido")
            return render(request, "web/administrador/ciclos/crear_ciclo.html", {"sedes": sedes})

        if alcance == "todas":
            for sede in sedes:
                Ciclo.objects.create(
                    nombre=nombre, precio=precio_dec,
                    fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, sede=sede,
                )
        else:
            if not sede_id:
                messages.error(request, "Debes seleccionar una sede")
                return render(request, "web/administrador/ciclos/crear_ciclo.html", {"sedes": sedes})
            sede = get_object_or_404(Sede, id=sede_id)
            Ciclo.objects.create(
                nombre=nombre, precio=precio_dec,
                fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, sede=sede,
            )

        return redirect("lista_ciclos")

    return render(request, "web/administrador/ciclos/crear_ciclo.html", {"sedes": sedes})
