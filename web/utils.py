import re
from datetime import date as _date


def normalizar_nombre(texto):
    """Strip, colapsa espacios dobles y aplica title-case. Para nombres propios."""
    if not texto:
        return ""
    return re.sub(r'\s+', ' ', texto.strip()).title()


def normalizar_texto(texto):
    """Strip y colapsa espacios dobles. Para direcciones y texto libre."""
    if not texto:
        return ""
    return re.sub(r'\s+', ' ', texto.strip())


def validar_dni(dni):
    """Retorna True si el DNI es exactamente 8 dígitos numéricos."""
    if not dni:
        return False
    return bool(re.match(r'^\d{8}$', str(dni)))


def validar_celular(celular):
    """Retorna True si el celular tiene 9 dígitos y comienza con 9."""
    if not celular:
        return True  # celular es opcional salvo se indique lo contrario
    return bool(re.match(r'^9\d{8}$', str(celular)))


def estado_ciclo_hoy(ciclo, today=None):
    """
    Fuente de verdad única para el estado académico de un ciclo.
    Usada por los módulos de Matrículas y Alumnos.

    Devuelve:
        'activa'     — el ciclo está en curso hoy
        'finalizada' — el ciclo ya terminó
        'pendiente'  — el ciclo aún no ha comenzado
    """
    if today is None:
        today = _date.today()
    if ciclo.fecha_inicio <= today <= ciclo.fecha_fin:
        return 'activa'
    if ciclo.fecha_fin < today:
        return 'finalizada'
    return 'pendiente'
