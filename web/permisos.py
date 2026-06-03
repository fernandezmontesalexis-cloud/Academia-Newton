import functools
from django.core.exceptions import PermissionDenied


def permiso_requerido(roles_permitidos):
    """
    Decorador que uso para proteger las vistas según el rol del usuario.

    Uso:
        @permiso_requerido(['admin'])              → solo el administrador puede entrar
        @permiso_requerido(['admin', 'secretaria']) → ambos roles pueden entrar

    Si el usuario no tiene el rol permitido, Django muestra la página 403 (Prohibido).
    El perfil del usuario llega a través de request.perfil — lo inyecta PerfilActivoMiddleware.
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # request.perfil es inyectado por PerfilActivoMiddleware en cada petición
            perfil = getattr(request, 'perfil', None)

            if not perfil or perfil.tipo_usuario not in roles_permitidos:
                # El usuario no tiene permiso — muestro la página 403.html
                raise PermissionDenied

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
