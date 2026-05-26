class NoCacheMiddleware:
    """
    Evita que el navegador guarde en caché las páginas del sistema.
    Así, al cerrar sesión y presionar Atrás, el navegador consulta
    a Django y éste redirige al login en vez de mostrar una página vieja.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response
