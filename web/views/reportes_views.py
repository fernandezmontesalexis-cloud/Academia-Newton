from django.shortcuts import render
from web.permisos import permiso_requerido
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from ..models import Sede, Alumno, Matricula, Pago


@login_required
@permiso_requerido(['admin'])
def reportes_sedes(request):
    sedes = Sede.objects.all()

    data_sedes = []
    for sede in sedes:
        alumnos_activos = Alumno.objects.filter(sede=sede, estado='activo').count()
        matriculas_qs = Matricula.objects.filter(alumno__sede=sede)
        ingresos = (
            Pago.objects.filter(matricula__alumno__sede=sede)
            .aggregate(total=Sum('monto'))['total'] or 0
        )
        deuda = sum(m.deuda() for m in matriculas_qs)

        data_sedes.append({
            'sede': sede,
            'alumnos_activos': alumnos_activos,
            'total_matriculas': matriculas_qs.count(),
            'ingresos': ingresos,
            'deuda': deuda,
        })

    return render(request, 'web/administrador/reportes/reportes_sedes.html', {
        'data_sedes': data_sedes,
    })
