import json
from datetime import date

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count

from ..models import Alumno, Matricula, Pago


@login_required
def dashboard(request):
    perfil = getattr(request.user, 'perfil', None)
    if not perfil:
        return redirect('login')

    if perfil.tipo_usuario == 'admin':
        hoy = date.today()
        mes_inicio = hoy.replace(day=1)

        total_alumnos = Alumno.objects.filter(estado='activo').count()
        matriculas_activas = Matricula.objects.filter(estado='pendiente').count()
        ingresos_mes = (
            Pago.objects.filter(fecha_pago__gte=mes_inicio)
            .aggregate(total=Sum('monto'))['total'] or 0
        )

        # Deuda total: suma de todas las deudas pendientes
        todas_matriculas = Matricula.objects.filter(estado='pendiente')
        deuda_total = sum(m.deuda() for m in todas_matriculas)

        # Chart: alumnos activos por sede
        alumnos_por_sede = list(
            Alumno.objects.filter(estado='activo')
            .values('sede__nombre')
            .annotate(total=Count('id'))
            .order_by('sede__nombre')
        )
        chart_sedes_labels = json.dumps([x['sede__nombre'] for x in alumnos_por_sede])
        chart_sedes_data = json.dumps([x['total'] for x in alumnos_por_sede])

        # Chart: matrículas por estado
        matriculas_por_estado = list(
            Matricula.objects.values('estado').annotate(total=Count('id'))
        )
        chart_estado_labels = json.dumps([x['estado'].capitalize() for x in matriculas_por_estado])
        chart_estado_data = json.dumps([x['total'] for x in matriculas_por_estado])

        return render(request, 'web/administrador/dashboard_admin.html', {
            'total_alumnos': total_alumnos,
            'matriculas_activas': matriculas_activas,
            'ingresos_mes': ingresos_mes,
            'deuda_total': deuda_total,
            'chart_sedes_labels': chart_sedes_labels,
            'chart_sedes_data': chart_sedes_data,
            'chart_estado_labels': chart_estado_labels,
            'chart_estado_data': chart_estado_data,
        })

    if perfil.tipo_usuario == 'secretaria':
        hoy = date.today()
        sede = perfil.sede

        total_alumnos = Alumno.objects.filter(sede=sede, estado='activo').count()
        matriculas_pendientes = Matricula.objects.filter(
            alumno__sede=sede, estado='pendiente'
        ).count()
        pagos_hoy = (
            Pago.objects.filter(fecha_pago=hoy, matricula__alumno__sede=sede)
            .aggregate(total=Sum('monto'))['total'] or 0
        )

        return render(request, 'web/secretaria/dashboard_secre.html', {
            'total_alumnos': total_alumnos,
            'matriculas_pendientes': matriculas_pendientes,
            'pagos_hoy': pagos_hoy,
        })

    return redirect('login')
