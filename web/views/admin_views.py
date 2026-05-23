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
    return render(request, "web/administrador/ciclos/ciclos_sede_detalle.html", {
        "sede": sede,
        "ciclos": ciclos,
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
        messages.success(request, f"Sede '{nombre}' creada correctamente")
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
        messages.success(request, "Sede actualizada correctamente")
        return redirect("lista_sedes")
    return render(request, "web/administrador/sedes/editar_sede.html", {"sede": sede})


@login_required
@permiso_requerido(['admin'])
def eliminar_sede(request, id):
    sede = get_object_or_404(Sede, id=id)
    sede.is_active = False
    sede.save()
    messages.success(request, f"Sede '{sede.nombre}' desactivada")
    return redirect("lista_sedes")


@login_required
@permiso_requerido(['admin'])
def reactivar_sede(request, id):
    sede = get_object_or_404(Sede, id=id)
    sede.is_active = True
    sede.save()
    messages.success(request, f"Sede '{sede.nombre}' reactivada")
    return redirect("lista_sedes")


@login_required
@permiso_requerido(['admin'])
def crear_usuario(request):
    sedes = Sede.objects.filter(is_active=True)
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        confirmar_password = request.POST.get("confirmar_password", "")
        tipo_usuario = request.POST.get("tipo_usuario")
        sede_id = request.POST.get("sede")

        def render_error(msg):
            return render(request, "web/administrador/usuarios/crear_usuario.html", {
                "error": msg, "sedes": sedes,
                "username": username, "tipo_usuario": tipo_usuario, "sede_id": sede_id,
            })

        if not username or not password:
            return render_error("El usuario y la contraseña son obligatorios")
        if password != confirmar_password:
            return render_error("Las contraseñas no coinciden")
        if len(password) < 6:
            return render_error("La contraseña debe tener al menos 6 caracteres")
        if User.objects.filter(username=username).exists():
            return render_error("Ese nombre de usuario ya existe")

        user = User.objects.create(username=username, password=make_password(password))
        Perfil.objects.create(user=user, tipo_usuario=tipo_usuario, sede_id=sede_id)
        messages.success(request, f"Usuario '{username}' creado correctamente")
        return redirect("lista_usuarios")

    return render(request, "web/administrador/usuarios/crear_usuario.html", {"sedes": sedes})


@login_required
@permiso_requerido(['admin'])
def lista_usuarios(request):
    q = request.GET.get('q', '').strip()
    sede_id = request.GET.get('sede_id', '')
    rol = request.GET.get('rol', '')
    estado = request.GET.get('estado', '')

    usuarios = User.objects.select_related("perfil", "perfil__sede").all()
    if q:
        usuarios = usuarios.filter(username__icontains=q)
    if sede_id:
        usuarios = usuarios.filter(perfil__sede_id=sede_id)
    if rol:
        usuarios = usuarios.filter(perfil__tipo_usuario=rol)
    if estado == 'activo':
        usuarios = usuarios.filter(is_active=True)
    elif estado == 'inactivo':
        usuarios = usuarios.filter(is_active=False)

    todos = User.objects.select_related("perfil").all()
    sedes = Sede.objects.all()

    return render(request, "web/administrador/usuarios/lista_usuarios.html", {
        "usuarios": usuarios,
        "sedes": sedes,
        "total": todos.count(),
        "total_admins": todos.filter(perfil__tipo_usuario='admin').count(),
        "total_secretarias": todos.filter(perfil__tipo_usuario='secretaria').count(),
        "total_activos": todos.filter(is_active=True).count(),
        "q": q,
        "sede_id_sel": sede_id,
        "rol_sel": rol,
        "estado_sel": estado,
    })


@login_required
@permiso_requerido(['admin'])
def editar_usuario(request, id):
    user = get_object_or_404(User, id=id)
    perfil = user.perfil
    sedes = Sede.objects.all()

    if request.method == "POST":
        user.username = request.POST.get("username")
        perfil.tipo_usuario = request.POST.get("tipo_usuario")
        perfil.sede_id = request.POST.get("sede")
        user.is_active = request.POST.get("is_active") == "1"

        nueva_password = request.POST.get("nueva_password", "").strip()
        confirmar_password = request.POST.get("confirmar_password", "").strip()

        if nueva_password:
            if nueva_password != confirmar_password:
                messages.error(request, "Las contraseñas no coinciden")
                return render(request, "web/administrador/usuarios/editar_usuario.html", {
                    "user": user, "perfil": perfil, "sedes": sedes,
                })
            if len(nueva_password) < 6:
                messages.error(request, "La contraseña debe tener al menos 6 caracteres")
                return render(request, "web/administrador/usuarios/editar_usuario.html", {
                    "user": user, "perfil": perfil, "sedes": sedes,
                })
            user.set_password(nueva_password)
            update_session_auth_hash(request, user)

        user.save()
        perfil.save()
        messages.success(request, "Usuario actualizado correctamente")
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
    messages.success(request, f"Usuario '{user.username}' desactivado")
    return redirect("lista_usuarios")


@login_required
@permiso_requerido(['admin'])
def reactivar_usuario(request, id):
    user = get_object_or_404(User, id=id)
    user.is_active = True
    user.save()
    messages.success(request, f"Usuario '{user.username}' reactivado")
    return redirect("lista_usuarios")


@login_required
@permiso_requerido(['admin'])
def configuracion(request):
    return render(request, 'web/administrador/configuracion/configuracion.html')


@login_required
@permiso_requerido(['admin'])
def editar_ciclo(request, id):
    from decimal import Decimal, InvalidOperation
    ciclo = get_object_or_404(Ciclo, id=id)
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        precio = request.POST.get("precio")
        fecha_inicio = request.POST.get("fecha_inicio")
        fecha_fin = request.POST.get("fecha_fin")
        if not nombre or not precio or not fecha_inicio or not fecha_fin:
            messages.error(request, "Todos los campos son obligatorios")
            return render(request, "web/administrador/ciclos/editar_ciclo.html", {"ciclo": ciclo})
        try:
            precio_dec = Decimal(precio)
            if precio_dec <= 0:
                raise ValueError
            if precio_dec % Decimal('0.50') != 0:
                messages.error(request, "El precio debe ser en soles enteros o medios (ej. S/. 300.00 o S/. 300.50)")
                return render(request, "web/administrador/ciclos/editar_ciclo.html", {"ciclo": ciclo})
        except (InvalidOperation, ValueError):
            messages.error(request, "El precio ingresado no es válido")
            return render(request, "web/administrador/ciclos/editar_ciclo.html", {"ciclo": ciclo})
        ciclo.nombre = nombre
        ciclo.precio = precio_dec
        ciclo.fecha_inicio = fecha_inicio
        ciclo.fecha_fin = fecha_fin
        ciclo.save()
        messages.success(request, "Ciclo actualizado correctamente")
        return redirect("ciclos_sede_detalle", sede_id=ciclo.sede.id)
    return render(request, "web/administrador/ciclos/editar_ciclo.html", {"ciclo": ciclo})


@login_required
@permiso_requerido(['admin'])
def eliminar_ciclo(request, id):
    ciclo = get_object_or_404(Ciclo, id=id)
    sede_id = ciclo.sede.id
    nombre = ciclo.nombre
    ciclo.delete()
    messages.success(request, f"Ciclo '{nombre}' eliminado correctamente")
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
            messages.success(request, f"Ciclo '{nombre}' creado para todas las sedes")
        else:
            if not sede_id:
                messages.error(request, "Debes seleccionar una sede")
                return render(request, "web/administrador/ciclos/crear_ciclo.html", {"sedes": sedes})
            sede = get_object_or_404(Sede, id=sede_id)
            Ciclo.objects.create(
                nombre=nombre, precio=precio_dec,
                fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, sede=sede,
            )
            messages.success(request, f"Ciclo '{nombre}' creado para {sede.nombre}")

        return redirect("lista_ciclos")

    return render(request, "web/administrador/ciclos/crear_ciclo.html", {"sedes": sedes})
