# PROPUESTA COMERCIAL
## Sistema de Gestión Académica — Academia Newton

---

> **Documento preparado por:** Equipo de Desarrollo  
> **Fecha:** Mayo 2026  
> **Versión:** 1.0

---

## RESUMEN EJECUTIVO

Academia Newton actualmente gestiona sus matrículas, pagos y registro de alumnos de forma manual, usando hojas de cálculo en Excel y documentos físicos. Este proceso genera errores, pérdida de tiempo y dificultad para acceder a información importante cuando se necesita.

El **Sistema de Gestión Academia Newton** es una solución web desarrollada a medida que digitaliza y centraliza toda la operación administrativa de la academia. El gerente puede ver el estado de todas sus sedes desde un solo lugar, las secretarias registran alumnos y pagos en minutos, y el sistema genera reportes automáticamente.

**En términos simples: lo que hoy se hace en papel y Excel, el sistema lo hace de forma ordenada, rápida y accesible desde cualquier computadora o celular.**

---

## 1. EL PROBLEMA ACTUAL

| Situación actual | Consecuencia |
|---|---|
| Registro de alumnos en Excel o papel | Errores de escritura, datos duplicados, información difícil de encontrar |
| Control de pagos manual | No se sabe fácilmente quién debe y cuánto |
| Información separada por sede | El gerente no puede ver el estado de todas sus sedes al mismo tiempo |
| Exportaciones manuales | Perder horas armando reportes para reuniones |
| Sin historial de cambios | No se sabe quién registró qué, ni cuándo |

---

## 2. ¿QUÉ ES EL SISTEMA?

Es un **programa web** (funciona en el navegador, como el correo o el banco en línea) diseñado específicamente para las necesidades de Academia Newton. No necesita instalar nada en las computadoras. Solo se necesita internet y el sistema está listo para usar.

El sistema tiene **dos tipos de acceso** según el rol de cada persona:

### 👤 Administrador (Gerente)
Tiene visión total de todas las sedes y control sobre la configuración del sistema.

### 👤 Secretaria
Accede únicamente a los datos de su sede. Registra alumnos, matrículas y pagos del día a día.

---

## 3. FUNCIONALIDADES DEL SISTEMA

### 3.1 Gestión de Alumnos

- **Registro completo de nuevos alumnos**: datos personales, contacto, fecha de nacimiento, dirección con departamento, provincia y distrito.
- **Registro del apoderado**: nombre, DNI, celular — vinculado automáticamente al alumno.
- **Historial académico del alumno**: colegio de procedencia (nacional o particular), carreras de interés, si estudió en otra academia previamente.
- **Estados del alumno**: el sistema distingue automáticamente entre alumnos *activos*, *sin matrícula*, *inactivos* y *bloqueados*.
- **Bloqueo con motivo registrado**: cuando un alumno es bloqueado (por deuda, expulsión, retiro, etc.), el sistema guarda el motivo y quién lo bloqueó.
- **Búsqueda por DNI** para encontrar cualquier alumno en segundos.
- **Edición de datos**: la secretaria puede actualizar celular, correo y datos del apoderado en cualquier momento.

### 3.2 Matrículas y Ciclos

- **Ciclos académicos por sede**: cada sede puede tener sus propios ciclos con nombre, precio, fecha de inicio y fecha de fin.
- **Creación de ciclo para todas las sedes a la vez**: si el gerente quiere crear el mismo ciclo en todas las sedes, puede hacerlo con un solo clic.
- **Alerta de vigencia de ciclos**: el sistema avisa automáticamente cuando un ciclo está por finalizar (menos de 14 días) o ya terminó.
- **Matrícula en pocos pasos**: el registro de un nuevo alumno guía a la secretaria paso a paso hasta completar la matrícula y el primer pago.
- **Renovación de matrícula**: para alumnos ya registrados, la secretaria puede renovarlos en un ciclo nuevo en segundos.
- **Protección contra matrículas duplicadas**: el sistema no permite registrar al mismo alumno dos veces con el mismo DNI, incluso en otra sede.

### 3.3 Control de Pagos

- **Registro de pagos**: cada pago queda registrado con monto, fecha, método (efectivo, Yape, transferencia) y quién lo recibió.
- **Estado automático de deuda**: el sistema calcula en tiempo real cuánto debe cada alumno y actualiza su estado (pagado / pendiente) al instante.
- **Alertas de pagos vencidos**: la lista de matrículas ordena primero a los alumnos con pagos atrasados o próximos a vencer.
- **Historial de pagos por alumno**: se puede ver cada pago realizado, en qué fecha y por qué método.
- **Control de próximo pago**: la secretaria puede registrar la fecha del próximo pago acordado con el alumno.

### 3.4 Panel de Control (Dashboard)

**Vista del Gerente:**
- Total de alumnos activos en todas las sedes
- Ingresos del mes actual
- Ingresos del día de hoy
- Deuda total pendiente en toda la academia
- Gráfico comparativo de ingresos por sede (este mes)
- Gráfico de recaudación esperada vs. cobrada por sede (ciclos activos)

**Vista de la Secretaria:**
- Total de alumnos activos en su sede
- Matrículas con pago pendiente
- Total cobrado hoy en su sede

### 3.5 Reportes Financieros

- **Reporte general de todas las sedes**: comparativo de alumnos, matrículas, ingresos totales y deuda por sede.
- **Estado de salud financiera**: el sistema califica automáticamente cada sede como *Saludable*, *Riesgo medio* o *Alta deuda* según el porcentaje de recaudación.
- **Gráfico de ingresos de los últimos 6 meses** por sede.
- **Reporte por ciclo**: para cada ciclo, el sistema muestra cuánto se esperaba recaudar, cuánto se cobró, cuánto falta y cuántos alumnos tienen deuda.
- **Tabla de ingresos anuales**: historial de los últimos 4 años con crecimiento porcentual año a año.
- **Exportación a Excel**: generación de reportes en formato Excel con un solo clic, listos para imprimir o compartir.

### 3.6 Gestión de Sedes

- Crear, editar y desactivar sedes desde el panel del gerente.
- Cada sede tiene su propio grupo de secretarias, alumnos, ciclos y reportes.
- El gerente puede ver cuántos usuarios y alumnos tiene cada sede.

### 3.7 Gestión de Usuarios del Sistema

- El gerente puede crear, editar y desactivar cuentas de secretarias.
- Cada secretaria solo ve los datos de su sede, no puede ver ni modificar los de otras sedes.
- El gerente puede cambiar contraseñas de usuarios cuando sea necesario.
- Registro de fecha de desactivación de usuarios inactivos.

### 3.8 Seguridad

- **Sesión con tiempo límite**: si el sistema no se usa por 30 minutos, cierra la sesión automáticamente para proteger la información.
- **Control de acceso por roles**: las secretarias no pueden acceder a funciones del gerente, y viceversa.
- **Protección de formularios**: el sistema valida todos los datos ingresados antes de guardarlos.
- **Historial de operaciones**: cada matrícula y pago registra quién lo hizo y en qué sede.

---

## 4. BENEFICIOS PARA LA ACADEMIA

### ⏱️ Ahorro de tiempo
El registro de un alumno nuevo, que antes podía tomar 15–20 minutos entre buscar la ficha, escribir en Excel y guardar el papel, **ahora toma 3–5 minutos** con el sistema guiando cada paso.

### 📊 Información al instante
El gerente no necesita esperar a que la secretaria "prepare el reporte" para saber cuánto ingresó la academia este mes. **La información está disponible en tiempo real, las 24 horas**.

### 🔒 Eliminación de errores
Los datos se validan automáticamente: no se puede ingresar un DNI duplicado, un celular con menos de 9 dígitos, ni una fecha incorrecta. **Se eliminan los errores humanos típicos del Excel manual**.

### 📁 Historial permanente
Todo queda registrado: quién matriculó a cada alumno, quién recibió cada pago, por qué se bloqueó un alumno. **La información nunca se pierde y siempre se puede consultar**.

### 🏢 Control multi-sede
Si la academia tiene o planea tener más de una sede, el gerente puede **administrar todo desde un solo sistema**, sin necesidad de llamar a cada sede para saber cómo va el día.

### 💰 Control financiero real
El sistema muestra en todo momento cuánto se debería haber cobrado, cuánto se cobró y cuánto falta. **El gerente sabe exactamente la salud financiera de su academia sin necesidad de contabilidad manual**.

### 🌐 Acceso desde cualquier lugar
Al ser un sistema web, **se puede consultar desde cualquier computadora, laptop o celular** que tenga internet, sin instalar programas adicionales.

---

## 4.1 ¿La academia ya usa Drive y matrículas virtuales? — Esto es lo que cambia

Es completamente válido que la academia ya cuente con herramientas digitales como Google Drive o formularios en línea para registrar matrículas. Sin embargo, existe una diferencia fundamental entre **guardar información** y **gestionar información**.

**Google Drive** es un almacén de archivos en la nube: guarda documentos, hojas de cálculo y formularios, pero no procesa ni conecta esos datos entre sí. Alguien tiene que abrir cada archivo, buscar manualmente, calcular a mano y actualizar uno por uno.

**Las matrículas virtuales** (formularios en línea) permiten recibir datos del alumno, pero una vez que ese dato llega, alguien tiene que copiarlo a otro lugar, calcular cuánto debe, registrar si pagó, recordar cuándo vence su próximo pago — todo de forma manual.

**El sistema hace todo eso automáticamente**, sin intervención humana adicional.

#### Comparativo directo

| ¿Puede hacerlo? | Google Drive + Formularios | Sistema de Gestión |
|---|---|---|
| Registrar datos de un alumno | ✅ (manual, en una hoja) | ✅ (guiado, con validación automática) |
| Calcular automáticamente cuánto debe cada alumno | ❌ | ✅ |
| Avisar qué alumnos tienen pagos vencidos hoy | ❌ | ✅ |
| Generar reporte financiero de todas las sedes en segundos | ❌ | ✅ |
| Impedir que un alumno bloqueado se vuelva a matricular | ❌ | ✅ |
| Saber quién registró cada pago y en qué sede | ❌ | ✅ |
| Controlar que una secretaria no vea datos de otra sede | ❌ | ✅ |
| Exportar un reporte a Excel con un clic | ❌ (hay que armarlo) | ✅ |
| Ver el estado financiero de la academia en tiempo real | ❌ | ✅ |
| Funciona sin que alguien "prepare" la información | ❌ | ✅ |

> **En conclusión:** Drive y los formularios resuelven el problema de *guardar* datos. El sistema resuelve el problema de *usar* esos datos para tomar decisiones, controlar pagos y gestionar la academia sin depender de que alguien los procese manualmente cada vez.
>
> Ambas herramientas pueden coexistir: el sistema no reemplaza Drive para almacenar contratos o documentos escaneados. Lo que reemplaza es la hoja de cálculo donde alguien suma, resta y busca a mano.

---

## 5. INFRAESTRUCTURA Y TECNOLOGÍA

*(Explicación simplificada para no especialistas)*

### ¿Dónde vive el sistema?

El sistema no se instala en ninguna computadora de la academia. Vive en **servidores en la nube** — computadoras de alta potencia ubicadas en centros de datos profesionales. El proveedor elegido es **Render**, una plataforma de alojamiento web reconocida a nivel mundial, que garantiza:

- ✅ Disponibilidad del sistema las 24 horas, los 7 días de la semana
- ✅ Copias de seguridad automáticas de los datos cada día
- ✅ Protección contra pérdida de información
- ✅ Actualizaciones de seguridad del servidor incluidas

### ¿Qué pasa si se va la luz o el internet en la academia?

Los datos no se pierden. El sistema y todos los datos están en los servidores de Render. Cuando vuelva el internet, todo sigue exactamente como estaba.

### ¿Qué tecnología usa el sistema?

| Componente | Tecnología | ¿Qué significa? |
|---|---|---|
| Lenguaje de programación | Python / Django | Uno de los lenguajes más usados en el mundo para sistemas web |
| Base de datos | PostgreSQL | Base de datos profesional, la misma que usan empresas como Instagram y Spotify |
| Alojamiento | Render (nube) | Servidores profesionales con alta disponibilidad |
| Seguridad | HTTPS / CSRF | La misma tecnología de seguridad que usa un banco en línea |

---

## 6. PROPUESTA ECONÓMICA

### 6.1 Pago por el Desarrollo del Sistema (único, no se repite)

El desarrollo de un sistema personalizado de esta envergadura tiene un costo de mercado de **S/. 4,000 a S/. 8,000** en empresas de software. Al ser un equipo de practicantes comprometidos con el proyecto, ofrecemos una tarifa especial:

| Concepto | Precio |
|---|---|
| Desarrollo completo del sistema (precio mercado) | S/. 4,000 |
| Descuento por equipo practicante | − S/. 2,600 |
| **Precio especial para Academia Newton** | **S/. 1,400** |

> Este pago cubre: todo el desarrollo ya realizado, la configuración del servidor y la puesta en marcha del sistema en producción.

---

### 6.2 Costo de Alojamiento en la Nube (mensual, fijo)

Este costo corresponde al alquiler de los servidores donde vivirá el sistema. Es un costo real de infraestructura que se paga al proveedor (Render). El sistema necesita dos componentes: el servidor que ejecuta la aplicación y el servidor que guarda los datos.

Se ofrecen dos opciones según el presupuesto inicial:

#### Opción A — Plan Inicial (recomendado para empezar)

| Servicio | Plan | Costo mensual (USD) | Costo mensual (S/.) aprox. |
|---|---|---|---|
| Servidor web (aplicación) | Starter | $7.00 | S/. 27 |
| Servidor de base de datos | Basic-256mb | $6.00 | S/. 23 |
| **Total Opción A** | | **$13.00/mes** | **≈ S/. 49/mes** |

> **Para comenzar, la Opción A es suficiente para el volumen actual de la academia y cuesta S/. 49 al mes. Si en algún momento sienten que el sistema va lento o necesitan más capacidad, se amplía en un día sin perder ningún dato.**

#### Opción B — Plan Crecimiento (mayor capacidad desde el inicio)

| Servicio | Plan | Costo mensual (USD) | Costo mensual (S/.) aprox. |
|---|---|---|---|
| Servidor web (aplicación) | Starter | $7.00 | S/. 27 |
| Servidor de base de datos | Basic-1gb | $19.00 | S/. 72 |
| **Total Opción B** | | **$26.00/mes** | **≈ S/. 99/mes** |

> Mayor capacidad de almacenamiento y rendimiento. Recomendado si se planea crecer en sedes o en cantidad de alumnos en el corto plazo.

> *Tipo de cambio referencial: S/. 3.80 por dólar. Puede variar ligeramente.*  
> *El costo en soles puede ajustarse mínimamente según el tipo de cambio del mes.*  
> *El alojamiento se factura mensualmente. No existe modalidad anual en este proveedor.*

---

### 6.3 Mantenimiento — ¿Cada cuánto tiempo es necesario?

Una preocupación frecuente es pensar que el mantenimiento es un costo fijo e inevitable todos los meses. La realidad es diferente: **la frecuencia del mantenimiento depende del estado del sistema**, y un sistema bien desarrollado tiende a necesitar cada vez menos intervención con el tiempo.

#### ¿Cómo evoluciona el mantenimiento?

| Período | Situación esperada | Frecuencia recomendada |
|---|---|---|
| **Meses 1–3** | Primeros meses de uso real. Pueden aparecer errores menores al usar funciones en situaciones no previstas durante el desarrollo. | Mensual (S/. 100/mes) |
| **Meses 4–6** | El sistema ya está estable. El equipo lo conoce bien. Los errores, si los hay, son puntuales y menores. | Cada 2 meses (S/. 100 c/2 meses) |
| **A partir del mes 7** | Sistema en funcionamiento pleno. El mantenimiento pasa a ser preventivo: revisión general, optimización y limpieza de datos. | Cada 4–6 meses |
| **Anual** | Limpieza profunda de datos: registros históricos, archivos innecesarios, optimización de la base de datos. | 1 vez al año |

> **Importante:** el mantenimiento no es un contrato obligatorio mensual de por vida. Si el sistema funciona correctamente y no hay nada que corregir o mejorar, **no hay nada que cobrar**. Solo se cobra cuando hay trabajo real que hacer.

#### Primer mes: completamente gratuito ✅

El primer mes después de la puesta en marcha no tiene costo de mantenimiento. Esto permite que el equipo de la academia use el sistema con total confianza, reporte cualquier detalle que requiera ajuste, y el equipo de desarrollo lo atiende sin costo adicional.

#### Tarifas de mantenimiento (cuando aplica)

| Tipo de intervención | Precio | Incluye |
|---|---|---|
| **Correctivo** (corrección de errores) | S/. 100 | Identificación y corrección del problema, pruebas, actualización del sistema |
| **Preventivo** (revisión general cada 4–6 meses) | S/. 100 | Revisión de rendimiento, actualización de seguridad, limpieza de registros temporales |
| **Limpieza anual de datos** | S/. 100 | Organización de datos históricos, optimización de la base de datos, respaldo completo |
| **Mejora o nueva funcionalidad** | Cotización aparte | Según el alcance del cambio solicitado |

> En un escenario realista, la academia podría pagar mantenimiento **3 a 4 veces al año** una vez que el sistema esté estable — lo que equivale a aproximadamente **S/. 300–400 anuales** en lugar de S/. 1,200 si fuera mensual fijo.

---

### 6.4 Resumen Total

| Concepto | Tipo de pago | Opción A | Opción B |
|---|---|---|---|
| Desarrollo del sistema | Único | S/. 1,400 | S/. 1,400 |
| Alojamiento en la nube | Mensual (desde mes 1) | ≈ S/. 49/mes | ≈ S/. 99/mes |
| Mantenimiento | Mensual (**primer mes gratis**) | S/. 100–180/mes | S/. 100–180/mes |

#### Ejemplo de inversión en el tiempo (Opción A — Plan Inicial):

| Período | Costo estimado |
|---|---|
| Mes 1 (puesta en marcha) | S/. 1,400 desarrollo + S/. 49 servidor = **S/. 1,449** |
| Mes 2 en adelante | S/. 49 servidor + S/. 100 mantenimiento = **S/. 149/mes** |
| **Costo anual desde el año 2** | **≈ S/. 1,788/año** (≈ S/. 149/mes × 12) |

#### Ejemplo de inversión en el tiempo (Opción B — Plan Crecimiento):

| Período | Costo estimado |
|---|---|
| Mes 1 (puesta en marcha) | S/. 1,400 desarrollo + S/. 99 servidor = **S/. 1,499** |
| Mes 2 en adelante | S/. 99 servidor + S/. 100 mantenimiento = **S/. 199/mes** |
| **Costo anual desde el año 2** | **≈ S/. 2,388/año** (≈ S/. 199/mes × 12) |

> Para comparar: una secretaria dedica aproximadamente **10–15 horas al mes** solo a armar reportes en Excel y buscar información entre papeles. A S/. 10/hora, eso equivale a S/. 100–150 solo en tiempo perdido, que el sistema elimina por completo.

---

### 6.5 ¿Cuánto le ahorra realmente el sistema?

Esta sección muestra, en términos concretos, lo que representa el costo del sistema frente al ahorro real que genera en la operación diaria de la academia.

#### El escenario sin el sistema (situación actual)

Gestionar matrículas, pagos y reportes de forma manual requiere dedicación constante del personal administrativo. Tareas como buscar fichas, actualizar Excel, calcular deudas y armar reportes consumen horas de trabajo que se pagan mes a mes.

**Costo de una secretaria administrativa (sueldo mínimo referencial):**

| Concepto | Detalle | Monto mensual |
|---|---|---|
| Sueldo neto secretaria | Remuneración mensual mínima referencial | S/. 1,025 |
| **Total costo personal/mes** | | **S/. 1,025** |

---

#### El escenario con el sistema

El sistema automatiza las tareas administrativas repetitivas: cálculo de deudas, búsqueda de alumnos, generación de reportes y control de pagos. Lo que antes requería dos personas, con el sistema lo maneja una sola con mayor precisión y en menos tiempo.

**Costo mensual real del sistema (Opción A — Plan Inicial):**

| Concepto | Explicación | Monto mensual |
|---|---|---|
| Desarrollo del sistema | S/. 1,400 repartidos en 12 meses del primer año | S/. 117 |
| Alojamiento en la nube | Servidores donde vive el sistema (Render, Opción A) | S/. 49 |
| Mantenimiento básico | Soporte técnico, corrección de errores | S/. 100 |
| **Costo total del sistema/mes** | | **S/. 266** |

---

#### Comparativo: ¿cuánto se ahorra?

| Concepto | Sin el sistema | Con el sistema | Diferencia |
|---|---|---|---|
| Personal administrativo extra | S/. 1,025/mes | S/. 0 | −S/. 1,025 |
| Costo del sistema | S/. 0 | S/. 266/mes | +S/. 266 |
| **Resultado mensual** | **S/. 1,025** | **S/. 266** | **Ahorro: S/. 759/mes** |
| **Resultado anual** | **S/. 12,300** | **S/. 3,192** | **Ahorro: ≈ S/. 9,100/año** |

---

> 💡 **En resumen:** el sistema no representa un gasto de S/. 266 al mes — representa un **ahorro neto de S/. 759 al mes** desde el primer año de uso. Dicho de otra forma: por cada sol invertido en el sistema, la academia recupera aproximadamente **S/. 3.85**.

---

## 7. GARANTÍAS Y CONDICIONES

### ✅ Garantías que ofrecemos

- **30 días de soporte gratuito** a partir de la puesta en marcha del sistema, para resolver cualquier duda o ajuste necesario.
- **Disponibilidad del sistema**: Render garantiza un 99.5% de tiempo en línea (menos de 1 hora de caída al mes en promedio).
- **Backups automáticos diarios**: la base de datos se respalda cada 24 horas. En caso de cualquier problema, se puede restaurar hasta el día anterior.
- **Capacitación incluida**: una sesión de capacitación para el equipo de secretarias y administradores sobre el uso del sistema.

### 📋 Condiciones

- El costo de alojamiento ($14/mes) se paga mensualmente. Si la academia decide no continuar con el servicio, puede cancelar con 15 días de aviso previo.
- El mantenimiento mensual es opcional pero recomendado. Sin mantenimiento, los errores y mejoras no están cubiertos.
- Los datos de la academia (alumnos, matrículas, pagos) son propiedad exclusiva de la academia. En caso de cancelación del servicio, se entrega una copia completa de todos los datos.
- Cualquier funcionalidad nueva que exceda el alcance del mantenimiento básico se cotizará por separado.

---

## 8. PRÓXIMOS PASOS

Si Academia Newton decide avanzar con el proyecto, el proceso sería el siguiente:

| Paso | Descripción | Tiempo estimado |
|---|---|---|
| **1. Acuerdo y pago inicial** | Firma del acuerdo y pago del desarrollo | Inmediato |
| **2. Migración a PostgreSQL** | Adaptación de la base de datos para producción | 1–2 días |
| **3. Configuración en Render** | Despliegue del sistema en los servidores de la nube | 1–2 días |
| **4. Pruebas finales** | Verificación de que todo funciona correctamente en producción | 1 día |
| **5. Capacitación** | Sesión de uso del sistema para secretarias y gerente | 1–2 horas |
| **6. Puesta en marcha** | El sistema comienza a usarse en producción | — |

**Tiempo total estimado para estar operativo: 1 semana.**

---

## CONTACTO

Para cualquier consulta adicional sobre esta propuesta, estamos disponibles para coordinar una reunión y aclarar todos los detalles.

---

*Este documento fue preparado exclusivamente para Academia Newton.*  
*Los precios indicados tienen validez de 30 días a partir de la fecha de emisión.*

---
