from django.shortcuts import redirect

def permiso_requerido(roles_permitidos):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            perfil = getattr(request.user, 'perfil', None)

            if not perfil or perfil.tipo_usuario not in roles_permitidos:
                return redirect('dashboard')

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator