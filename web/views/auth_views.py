from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

# @never_cache le dice al navegador que nunca guarde esta página en caché
# — así si el usuario presiona "atrás" después de cerrar sesión, no verá la página anterior
@never_cache
def login_view(request):

    # Si el usuario ya está logueado, lo mando directo al dashboard — no tiene que volver a ingresar
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        # Django verifica si el usuario y contraseña son correctos
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Credenciales correctas — inicio sesión y mando al dashboard
            login(request, user)
            return redirect('dashboard')
        else:
            # Credenciales incorrectas — muestro mensaje de error en el formulario
            messages.error(request, 'Usuario o Contraseña incorrecto')

    return render(request, 'web/auth/login.html')


@login_required
def logout_view(request):
    # Cierro la sesión del usuario y lo mando de vuelta al login
    logout(request)
    return redirect('login')
