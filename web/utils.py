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


def validar_email(email):
    """
    Valida formato de correo con dominio y extensión reales.
    Retorna None si es válido (o vacío), o un mensaje de error específico.
    """
    if not email:
        return None  # email es opcional

    if '@' not in email:
        return "Debe ingresar un correo válido."

    partes = email.split('@')
    if len(partes) != 2:
        return "Debe ingresar un correo válido."

    local, dominio = partes

    if not local:
        return "Debe ingresar un correo válido."

    if not dominio:
        return "El correo debe incluir un dominio válido (ej. gmail.com)."

    if '.' not in dominio:
        return "El correo debe incluir un dominio válido (ej. gmail.com)."

    partes_dominio = dominio.split('.')
    nombre_dominio = '.'.join(partes_dominio[:-1])
    extension = partes_dominio[-1]

    if not nombre_dominio or len(nombre_dominio) < 2:
        return "El correo debe incluir un dominio válido (ej. gmail.com)."

    if not extension or len(extension) < 2:
        return "El correo debe incluir una extensión válida (.com, .pe, etc.)."

    if not re.match(r'^[a-zA-Z]+$', extension):
        return "El correo debe incluir una extensión válida (.com, .pe, etc.)."

    return None


def validar_celular(celular):
    """Retorna True si el celular tiene 9 dígitos y comienza con 9."""
    if not celular:
        return True  # celular es opcional salvo se indique lo contrario
    return bool(re.match(r'^9\d{8}$', str(celular)))


def estado_pago_matricula(m, today):
    """
    Calcula el estado de pago de una matrícula anotada con deuda_db y total_pagado_db.
    Fuente de verdad única usada en Matrículas y Reportes de Ciclo.

    Devuelve: 'pagado' | 'vencido' | 'parcial' | 'sin_pago'
    """
    if m.deuda_db <= 0:
        return 'pagado'
    if m.ciclo.fecha_fin < today:
        return 'vencido'
    if m.total_pagado_db > 0:
        return 'parcial'
    return 'sin_pago'


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
