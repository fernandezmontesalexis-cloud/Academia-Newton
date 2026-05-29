import functools
from django.core.exceptions import PermissionDenied


def permiso_requerido(roles_permitidos):
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # request.perfil es inyectado por PerfilActivoMiddleware
            perfil = getattr(request, 'perfil', None)

            if not perfil or perfil.tipo_usuario not in roles_permitidos:
                raise PermissionDenied

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
