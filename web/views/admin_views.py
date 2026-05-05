from django.shortcuts import render
from web.permisos import permiso_requerido
from django.contrib.auth.decorators import login_required

from ..models import Ciclo
from ..models import Sede
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from ..models import Sede

from django.shortcuts import render, redirect, get_object_or_404
from web.models import Sede


from django.shortcuts import redirect, get_object_or_404
from web.models import Sede
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from web.models import Perfil, Sede

from django.contrib.auth.models import User
from web.models import Perfil


@login_required
@permiso_requerido(['admin'])
def lista_ciclos(request):
    ciclos = Ciclo.objects.all()

    return render(request, 'web/administrador/ciclos/lista.html', {
        'ciclos': ciclos
    })
@login_required
@permiso_requerido(['admin'])
def lista_sedes(request):
    sedes = Sede.objects.all()

    return render(request, 'web/administrador/sedes/lista_sedes.html', {
        'sedes': sedes
    })
@login_required
def crear_sede(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")

        if not nombre:
            messages.error(request, "El nombre es obligatorio")
            return redirect("crear_sede")

        Sede.objects.create(nombre=nombre)

        messages.success(request, "Sede creada correctamente")
        return redirect("lista_sedes")

    return render(request, "web/administrador/sedes/crear_sede.html")


def editar_sede(request, id):
    sede = get_object_or_404(Sede, id=id)

    if request.method == "POST":
        nombre = request.POST.get("nombre")

        if nombre:
            sede.nombre = nombre
            sede.save()
            return redirect("lista_sedes")

    return render(request, "web/administrador/sedes/editar_sede.html", {
        "sede": sede
    })

def eliminar_sede(request, id):
    sede = get_object_or_404(Sede, id=id)

    sede.delete()

    return redirect("lista_sedes")



def crear_usuario(request):
    sedes = Sede.objects.all()

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        tipo_usuario = request.POST.get("tipo_usuario")
        sede_id = request.POST.get("sede")

        if not username or not password:
            return render(request, "web/administrador/usuarios/crear_usuario.html", {
                "error": "Todos los campos son obligatorios",
                "sedes": sedes
            })

        if User.objects.filter(username=username).exists():
            return render(request, "web/administrador/usuarios/crear_usuario.html", {
                "error": "El usuario ya existe",
                "sedes": sedes
            })

        user = User.objects.create(
            username=username,
            password=make_password(password)
        )

        Perfil.objects.create(
            user=user,
            tipo_usuario=tipo_usuario,
            sede_id=sede_id
        )

        return redirect("lista_usuarios")

    return render(request, "web/administrador/usuarios/crear_usuario.html", {
        "sedes": sedes
    })



def lista_usuarios(request):
    usuarios = User.objects.select_related("perfil", "perfil__sede").all()

    return render(request, "web/administrador/usuarios/lista_usuarios.html", {
        "usuarios": usuarios
    })
def editar_usuario(request, id):
    user = User.objects.get(id=id)
    perfil = user.perfil
    sedes = Sede.objects.all()

    if request.method == "POST":
        user.username = request.POST.get("username")
        perfil.tipo_usuario = request.POST.get("tipo_usuario")
        perfil.sede_id = request.POST.get("sede")

        user.save()
        perfil.save()

        return redirect("lista_usuarios")

    return render(request, "web/administrador/usuarios/editar_usuario.html", {
        "user": user,
        "perfil": perfil,
        "sedes": sedes
    })

def eliminar_usuario(request, id):
    user = User.objects.get(id=id)
    user.delete()

    return redirect("lista_usuarios")

@login_required
@permiso_requerido(["admin"])
def crear_ciclo(request):

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        precio = request.POST.get("precio")
        fecha_inicio = request.POST.get("fecha_inicio")
        fecha_fin = request.POST.get("fecha_fin")

        # 🔥 validaciones básicas
        if not nombre or not precio or not fecha_inicio or not fecha_fin:
            messages.error(request, "Todos los campos son obligatorios")
            return redirect("crear_ciclo")

        # sede automática del usuario
        sede = request.user.perfil.sede

        Ciclo.objects.create(
            nombre=nombre,
            precio=precio,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            sede=sede,
        )

        messages.success(request, "Ciclo creado correctamente")
        return redirect("lista_ciclos")

    return render(request, "web/administrador/ciclos/crear_ciclo.html")

@login_required
@permiso_requerido(["admin"])
def lista_ciclos(request):

    sede = request.user.perfil.sede

    ciclos = Ciclo.objects.filter(sede=sede)

    return render(
        request,
        "web/administrador/ciclos/lista_ciclos.html",
        {"ciclos": ciclos},
    )