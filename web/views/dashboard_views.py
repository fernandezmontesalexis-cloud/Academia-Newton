import json
from datetime import date
from decimal import Decimal

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

from ..models import Alumno, Ciclo, Matricula, Pago, Sede


@login_required
def dashboard(request):
    # Obtengo el perfil del usuario — si no tiene perfil activo lo mando al login
    perfil = getattr(request, 'perfil', None)
    if not perfil:
        return redirect('login')

    # Dependiendo del rol, muestro un dashboard diferente
    if perfil.tipo_usuario == 'admin':
        hoy = date.today()
        mes_inicio = hoy.replace(day=1)  # primer día del mes actual

        # ── Tarjetas de resumen global ────────────────────────────────────
        # Cuento todos los alumnos activos en el sistema (todas las sedes)
        total_alumnos = Alumno.objects.filter(estado='activo').count()

        # Sumo todos los pagos registrados desde el 1ro del mes hasta hoy
        ingresos_mes = (
            Pago.objects.filter(fecha_pago__gte=mes_inicio)
            .aggregate(total=Sum('monto'))['total'] or 0
        )

        # Sumo solo los pagos de hoy
        ingresos_hoy = (
            Pago.objects.filter(fecha_pago=hoy)
            .aggregate(total=Sum('monto'))['total'] or 0
        )

        # Calculo la deuda total del sistema: lo que se esperaba cobrar menos lo que ya se cobró
        # Uso 2 queries separadas en lugar de recorrer fila por fila — es mucho más rápido
        _mats_pend = Matricula.objects.filter(alumno__estado='activo', estado='pendiente')
        _total_precio  = _mats_pend.aggregate(t=Sum('ciclo__precio'))['t'] or Decimal('0')
        _total_pagado  = (
            Pago.objects.filter(matricula__in=_mats_pend)
            .aggregate(t=Sum('monto'))['t'] or Decimal('0')
        )
        deuda_total = _total_precio - _total_pagado

        # ── Datos para los gráficos ───────────────────────────────────────
        # Preparo listas para Chart.js: una entrada por cada sede activa
        chart_labels  = []   # nombres de las sedes
        chart_incomes = []   # ingresos del mes por sede (gráfico dona)
        chart_esperado = []  # lo que se esperaba cobrar en ciclos activos (gráfico de barras)
        chart_cobrado  = []  # lo que realmente se cobró en ciclos activos (gráfico de barras)

        for sede in Sede.objects.filter(is_active=True):
            # Ingresos del mes para esta sede — para el gráfico dona
            ingresos_mes_sede = float(
                Pago.objects.filter(
                    matricula__alumno__sede=sede,
                    fecha_pago__gte=mes_inicio
                ).aggregate(total=Sum('monto'))['total'] or 0
            )
            chart_labels.append(sede.nombre)
            chart_incomes.append(ingresos_mes_sede)

            # Para el gráfico de barras: recorro los ciclos activos de esta sede
            ciclos_activos = list(Ciclo.objects.filter(
                sede=sede, fecha_fin__gte=hoy
            ))
            sede_esperado = 0.0
            sede_cobrado  = 0.0
            for ciclo in ciclos_activos:
                total_mat = Matricula.objects.filter(ciclo=ciclo).count()
                sede_esperado += float(ciclo.precio * total_mat)
                sede_cobrado  += float(
                    Pago.objects.filter(matricula__ciclo=ciclo)
                    .aggregate(total=Sum('monto'))['total'] or 0
                )
            chart_esperado.append(sede_esperado)
            chart_cobrado.append(sede_cobrado)

        # Paso los datos como JSON para que Chart.js los pueda leer en el template
        return render(request, 'web/administrador/dashboard_admin.html', {
            'total_alumnos': total_alumnos,
            'ingresos_mes':  ingresos_mes,
            'ingresos_hoy':  ingresos_hoy,
            'deuda_total':   deuda_total,
            'chart_labels':   json.dumps(chart_labels),
            'chart_incomes':  json.dumps(chart_incomes),
            'chart_esperado': json.dumps(chart_esperado),
            'chart_cobrado':  json.dumps(chart_cobrado),
        })

    if perfil.tipo_usuario == 'secretaria':
        hoy  = date.today()
        sede = perfil.sede  # la secretaria solo ve datos de su propia sede

        # Tarjetas simples: alumnos activos, matrículas con deuda y lo cobrado hoy
        total_alumnos = Alumno.objects.filter(sede=sede, estado='activo').count()
        matriculas_pendientes = Matricula.objects.filter(
            alumno__sede=sede, alumno__estado='activo', estado='pendiente'
        ).count()
        pagos_hoy = (
            Pago.objects.filter(fecha_pago=hoy, matricula__alumno__sede=sede)
            .aggregate(total=Sum('monto'))['total'] or 0
        )

        return render(request, 'web/secretaria/dashboard_secre.html', {
            'total_alumnos':         total_alumnos,
            'matriculas_pendientes': matriculas_pendientes,
            'pagos_hoy':             pagos_hoy,
        })

    # Si el perfil tiene un rol desconocido, mando al login por seguridad
    return redirect('login')
