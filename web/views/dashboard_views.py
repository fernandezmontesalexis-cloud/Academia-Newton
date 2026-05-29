import json
from datetime import date
from decimal import Decimal

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

from ..models import Alumno, Ciclo, Matricula, Pago, Sede


@login_required
def dashboard(request):
    perfil = getattr(request, 'perfil', None)
    if not perfil:
        return redirect('login')

    if perfil.tipo_usuario == 'admin':
        hoy = date.today()
        mes_inicio = hoy.replace(day=1)

        # KPIs globales
        total_alumnos = Alumno.objects.filter(estado='activo').count()
        ingresos_mes = (
            Pago.objects.filter(fecha_pago__gte=mes_inicio)
            .aggregate(total=Sum('monto'))['total'] or 0
        )
        ingresos_hoy = (
            Pago.objects.filter(fecha_pago=hoy)
            .aggregate(total=Sum('monto'))['total'] or 0
        )
        # 2 queries en lugar de N+1: suma precios y suma pagos por separado
        _mats_pend = Matricula.objects.filter(alumno__estado='activo', estado='pendiente')
        _total_precio  = _mats_pend.aggregate(t=Sum('ciclo__precio'))['t'] or Decimal('0')
        _total_pagado  = (
            Pago.objects.filter(matricula__in=_mats_pend)
            .aggregate(t=Sum('monto'))['t'] or Decimal('0')
        )
        deuda_total = _total_precio - _total_pagado

        # Datos para gráficos por sede
        chart_labels = []
        chart_incomes = []    # dona: ingresos del mes
        chart_esperado = []   # barras: esperado ciclo activo
        chart_cobrado = []    # barras: cobrado ciclo activo

        for sede in Sede.objects.filter(is_active=True):
            ingresos_mes_sede = float(
                Pago.objects.filter(
                    matricula__alumno__sede=sede,
                    fecha_pago__gte=mes_inicio
                ).aggregate(total=Sum('monto'))['total'] or 0
            )
            chart_labels.append(sede.nombre)
            chart_incomes.append(ingresos_mes_sede)

            ciclos_activos = list(Ciclo.objects.filter(
                sede=sede, fecha_fin__gte=hoy
            ))
            sede_esperado = 0.0
            sede_cobrado = 0.0
            for ciclo in ciclos_activos:
                total_mat = Matricula.objects.filter(ciclo=ciclo).count()
                sede_esperado += float(ciclo.precio * total_mat)
                sede_cobrado += float(
                    Pago.objects.filter(matricula__ciclo=ciclo)
                    .aggregate(total=Sum('monto'))['total'] or 0
                )
            chart_esperado.append(sede_esperado)
            chart_cobrado.append(sede_cobrado)

        return render(request, 'web/administrador/dashboard_admin.html', {
            'total_alumnos': total_alumnos,
            'ingresos_mes': ingresos_mes,
            'ingresos_hoy': ingresos_hoy,
            'deuda_total': deuda_total,
            'chart_labels':   json.dumps(chart_labels),
            'chart_incomes':  json.dumps(chart_incomes),
            'chart_esperado': json.dumps(chart_esperado),
            'chart_cobrado':  json.dumps(chart_cobrado),
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
