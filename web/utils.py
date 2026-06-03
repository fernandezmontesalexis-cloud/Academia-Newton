import re
from datetime import date as _date


def normalizar_nombre(texto):
    """Limpia un nombre propio: quita espacios al inicio/fin, colapsa espacios dobles y aplica Title Case."""
    if not texto:
        return ""
    return re.sub(r'\s+', ' ', texto.strip()).title()


def normalizar_texto(texto):
    """Limpia texto libre (direcciones, comentarios): quita espacios sobrantes pero no cambia las mayúsculas."""
    if not texto:
        return ""
    return re.sub(r'\s+', ' ', texto.strip())


def validar_dni(dni):
    """Devuelve True si el DNI tiene exactamente 8 dígitos numéricos."""
    if not dni:
        return False
    return bool(re.match(r'^\d{8}$', str(dni)))


def validar_email(email):
    """
    Valida el formato del correo electrónico.
    Devuelve None si el email es válido (o si está vacío — es campo opcional).
    Devuelve un mensaje de error si el formato no es correcto.
    """
    if not email:
        return None  # el email es opcional, vacío está bien

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
    extension      = partes_dominio[-1]

    if not nombre_dominio or len(nombre_dominio) < 2:
        return "El correo debe incluir un dominio válido (ej. gmail.com)."

    if not extension or len(extension) < 2:
        return "El correo debe incluir una extensión válida (.com, .pe, etc.)."

    # La extensión debe ser solo letras — sin números ni caracteres raros
    if not re.match(r'^[a-zA-Z]+$', extension):
        return "El correo debe incluir una extensión válida (.com, .pe, etc.)."

    return None  # todo correcto


def validar_celular(celular):
    """
    Devuelve True si el celular es válido para Perú.
    Debe tener 9 dígitos y comenzar con 9 (ej: 987654321).
    El campo es opcional — si viene vacío, devuelvo True para no bloquear el formulario.
    """
    if not celular:
        return True
    return bool(re.match(r'^9\d{8}$', str(celular)))


def estado_pago_matricula(m, today):
    """
    Calcula el estado de pago de una matrícula y lo devuelve como texto.
    Esta es la fuente de verdad única — la uso en Matrículas y en Reportes de Ciclo.

    Para funcionar correctamente, la matrícula debe venir anotada con:
        deuda_db       → precio del ciclo − total pagado (calculado en BD)
        total_pagado_db → suma de todos los pagos (calculado en BD)

    Posibles valores que devuelvo:
        'pagado'   → no hay deuda, el alumno pagó todo
        'vencido'  → tiene deuda pero el ciclo ya terminó
        'parcial'  → tiene pagos pero sigue debiendo, el ciclo aún está vigente
        'sin_pago' → no ha pagado nada todavía y el ciclo está vigente
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
    Devuelve el estado actual de un ciclo según las fechas de hoy.
    La uso en el módulo de Matrículas y en el registro de alumnos.

    Posibles valores:
        'activa'    → el ciclo está en curso (fecha inicio ≤ hoy ≤ fecha fin)
        'finalizada' → el ciclo ya terminó
        'pendiente' → el ciclo aún no ha comenzado
    """
    if today is None:
        today = _date.today()
    if ciclo.fecha_inicio <= today <= ciclo.fecha_fin:
        return 'activa'
    if ciclo.fecha_fin < today:
        return 'finalizada'
    return 'pendiente'
