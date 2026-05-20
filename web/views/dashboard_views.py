from datetime import date

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

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
        matriculas_activas = Matricula.objects.filter(
            alumno__estado='activo', estado='pendiente'
        ).count()
        ingresos_mes = (
            Pago.objects.filter(fecha_pago__gte=mes_inicio)
            .aggregate(total=Sum('monto'))['total'] or 0
        )
        deuda_total = sum(
            m.deuda() for m in Matricula.objects.filter(
                alumno__estado='activo', estado='pendiente'
            )
        )
        ingresos_hoy = (
            Pago.objects.filter(fecha_pago=hoy)
            .aggregate(total=Sum('monto'))['total'] or 0
        )
        alumnos_con_deuda = (
            Alumno.objects.filter(
                estado='activo', matricula__estado='pendiente'
            ).distinct().count()
        )
        actividad_reciente = list(
            Pago.objects.select_related('matricula__alumno')
            .order_by('-fecha_pago', '-id')[:5]
        )

        return render(request, 'web/administrador/dashboard_admin.html', {
            'total_alumnos': total_alumnos,
            'matriculas_activas': matriculas_activas,
            'ingresos_mes': ingresos_mes,
            'deuda_total': deuda_total,
            'ingresos_hoy': ingresos_hoy,
            'alumnos_con_deuda': alumnos_con_deuda,
            'actividad_reciente': actividad_reciente,
        })

    if perfil.tipo_usuario == 'secretaria':
        hoy = date.today()
        sede = perfil.sede

        total_alumnos = Alumno.objects.filter(sede=sede, estado='activo').count()
        matriculas_pendientes = Matricula.objects.filter(
            alumno__sede=sede, alumno__estado='activo', estado='pendiente'
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
