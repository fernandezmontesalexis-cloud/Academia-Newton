from datetime import date as _date


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
