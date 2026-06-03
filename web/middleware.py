# Los middleware se ejecutan en cada petición, antes y después de que Django llame a la vista.
# Están registrados en settings.py dentro de la lista MIDDLEWARE.


class PerfilActivoMiddleware:
    """
    En cada petición, busco el Perfil activo del usuario y lo adjunto a request.perfil.
    Así todas las vistas y templates pueden usar request.perfil directamente
    sin tener que ir a la BD cada vez que necesiten saber el rol o la sede del usuario.
    Si el usuario no está logueado o no tiene perfil activo, request.perfil queda en None.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Traigo el perfil activo junto con la sede para no hacer otra consulta después
            request.perfil = (
                request.user.perfiles
                .filter(activo=True)
                .select_related('sede')
                .first()
            )
        else:
            request.perfil = None
        return self.get_response(request)


class NoCacheMiddleware:
    """
    Le digo al navegador que no guarde ninguna página en caché mientras el usuario esté logueado.
    Esto evita que al cerrar sesión y presionar "Atrás" el navegador muestre
    una página vieja en lugar de redirigir al login.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            # Estos headers le dicen al navegador: no guardes esta respuesta, pídela siempre de nuevo
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma']  = 'no-cache'
            response['Expires'] = '0'
        return response
