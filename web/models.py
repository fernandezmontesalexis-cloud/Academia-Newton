from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import RegexValidator


class Sede(models.Model):
    """Representa una sede física de la academia (ej. Huaura, Sayán, Huacho)."""
    nombre    = models.CharField(max_length=70)
    direccion = models.CharField(max_length=100)
    # Soft-delete: en lugar de borrar la sede, la desactivo con is_active=False
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Perfil(models.Model):
    """
    Extiende el User de Django con el rol y la sede asignada.
    Un usuario puede tener varios perfiles (uno por sede si cambió de sede),
    pero solo uno puede estar activo a la vez.
    """
    TIPO_USUARIO = [
        ('admin',      'Administrador'),
        ('secretaria', 'Secretaria'),
    ]
    user          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='perfiles')
    tipo_usuario  = models.CharField(max_length=20, choices=TIPO_USUARIO)
    sede          = models.ForeignKey(Sede, on_delete=models.CASCADE)
    activo        = models.BooleanField(default=True)
    fecha_desactivacion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username


class Apoderado(models.Model):
    """Padre, madre o tutor del alumno. El DNI es único — si ya existe, se reutiliza."""
    nombre_completo = models.CharField(max_length=100)
    dni             = models.CharField(max_length=8, unique=True)
    celular         = models.CharField(max_length=9)
    direccion       = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre_completo


class Alumno(models.Model):
    """
    Representa a un alumno registrado en el sistema.
    El DNI es único en toda la base de datos — no pueden existir dos alumnos con el mismo DNI,
    aunque estén en sedes diferentes.
    """
    apellido_paterno = models.CharField(max_length=70)
    apellido_materno = models.CharField(max_length=70)
    nombres          = models.CharField(max_length=70)
    dni = models.CharField(
        max_length=8, unique=True,
        validators=[RegexValidator(r'^\d{8}$', 'El DNI debe tener 8 digitos')]
    )
    celular          = models.CharField(max_length=9)
    fecha_nacimiento = models.DateField()
    direccion        = models.CharField(max_length=100)
    distrito         = models.ForeignKey('Distrito', on_delete=models.SET_NULL, null=True)
    email            = models.EmailField(null=True, blank=True)

    ESTADOS = [
        ('activo',    'Activo'),     # está matriculado o disponible para matricularse
        ('inactivo',  'Inactivo'),   # no renovó en 2+ ciclos — se inactiva automáticamente
        ('bloqueado', 'Bloqueado'),  # expulsado o con deuda grave — no puede matricularse en ninguna sede
    ]
    estado = models.CharField(max_length=10, choices=ESTADOS, default='activo')

    sede      = models.ForeignKey(Sede, on_delete=models.CASCADE)
    apoderado = models.ForeignKey(Apoderado, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.nombres} {self.apellido_paterno}"


class Ciclo(models.Model):
    """
    Período académico de una sede (ej. "Ciclo I 2025").
    Cada sede puede tener sus propios ciclos con fechas y precios diferentes.
    """
    nombre       = models.CharField(max_length=100)
    precio       = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_inicio = models.DateField()
    fecha_fin    = models.DateField()
    sede         = models.ForeignKey(Sede, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre

    @property
    def alerta_vigencia(self):
        """
        Calcula el estado del ciclo respecto a la fecha de hoy.
        Lo uso para mostrar badges en los reportes y separar vigentes de finalizados.

        Posibles valores:
            'activo'          → el ciclo está en curso
            'pendiente'       → aún no comenzó
            'finaliza_pronto' → faltan 14 días o menos para que termine
            'finalizado'      → ya terminó
        """
        today = timezone.localdate()
        if self.fecha_fin < today:
            return 'finalizado'
        if self.fecha_inicio > today:
            return 'pendiente'
        if (self.fecha_fin - today).days <= 14:
            return 'finaliza_pronto'
        return 'activo'


class Matricula(models.Model):
    """
    Relaciona un alumno con un ciclo. Es el registro central del sistema.
    Una matrícula empieza en estado 'pendiente' y pasa a 'pagado' cuando
    el alumno cancela el precio completo del ciclo.
    """
    alumno           = models.ForeignKey(Alumno,  on_delete=models.CASCADE)
    ciclo            = models.ForeignKey(Ciclo,   on_delete=models.CASCADE)
    fecha_matricula  = models.DateField()
    # Fecha del próximo pago — obligatoria si el alumno hizo un pago parcial
    proximo_pago     = models.DateField(null=True, blank=True)

    ESTADOS = [
        ('pendiente', 'Pendiente'),  # tiene deuda
        ('pagado',    'Pagado'),     # canceló el precio completo
    ]
    estado         = models.CharField(max_length=20, choices=ESTADOS)
    registrado_por = models.ForeignKey(Perfil, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.alumno} {self.ciclo}"

    def total_pagado(self):
        """
        Suma todos los pagos de esta matrícula.
        Cuando se usa con prefetch_related('pago_set'), Django aprovecha
        la caché del prefetch y no hace una consulta extra a la BD.
        """
        return sum(p.monto for p in self.pago_set.all()) or 0

    def deuda(self):
        """Cuánto le falta pagar al alumno: precio del ciclo menos lo que ya pagó."""
        return self.ciclo.precio - self.total_pagado()


class Pago(models.Model):
    """
    Registra cada pago parcial o total que hace un alumno para una matrícula.
    Cada vez que se guarda un pago, automáticamente actualiza el estado de la matrícula.
    """
    matricula      = models.ForeignKey(Matricula, on_delete=models.CASCADE)
    registrado_por = models.ForeignKey(Perfil, on_delete=models.CASCADE)
    # Nombre de quien entregó el dinero (puede ser el apoderado, no el alumno)
    apoderado      = models.CharField(max_length=100, blank=True, default='')
    fecha_pago     = models.DateField(default=timezone.now)
    monto          = models.DecimalField(max_digits=10, decimal_places=2)

    METODOS = [
        ('efectivo',      'Efectivo'),
        ('yape',          'Yape'),
        ('transferencia', 'Transferencia'),
    ]
    metodo_pago = models.CharField(max_length=20, choices=METODOS)

    def __str__(self):
        return f"{self.monto} {self.matricula}"

    def save(self, *args, **kwargs):
        """
        Después de guardar el pago, recalculo automáticamente el estado de la matrícula.
        Si la deuda llega a 0 o menos, la matrícula pasa a 'pagado'.
        Si sigue habiendo deuda, se mantiene en 'pendiente'.
        Así no tengo que actualizar el estado manualmente en ninguna vista.
        """
        super().save(*args, **kwargs)

        matricula = self.matricula

        if matricula.deuda() <= 0:
            matricula.estado = 'pagado'
        else:
            matricula.estado = 'pendiente'

        matricula.save()


class DesactivacionLog(models.Model):
    """
    Historial de cada vez que un alumno fue bloqueado.
    Guarda el motivo y quién lo registró para tener trazabilidad.
    """
    MOTIVOS = [
        ('retiro_voluntario', 'Retiro voluntario'),
        ('deuda_pendiente',   'Deuda pendiente'),
        ('inasistencia',      'Inasistencia prolongada'),
        ('expulsion',         'Expulsión'),
        ('otro',              'Otro'),
    ]
    alumno         = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='desactivaciones')
    motivo         = models.CharField(max_length=30, choices=MOTIVOS)
    comentario     = models.TextField(blank=True)  # opcional — para detalles adicionales
    fecha          = models.DateTimeField(auto_now_add=True)
    registrado_por = models.ForeignKey(Perfil, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-fecha']  # muestro los más recientes primero

    def __str__(self):
        return f"{self.alumno} — {self.get_motivo_display()}"


# ══════════════════════════════════════════════════════════════════
#  FORMACIÓN ACADÉMICA Y ADICIONAL
#  Datos complementarios del alumno — se crean en el paso 3 y 4 del registro
# ══════════════════════════════════════════════════════════════════

class FormacionAcademica(models.Model):
    """Colegio de procedencia del alumno."""
    alumno           = models.OneToOneField(Alumno, on_delete=models.CASCADE)
    tipo_institucion = models.CharField(max_length=20)  # Nacional o Particular
    institucion      = models.ForeignKey(
        'InstitucionEducativa', on_delete=models.SET_NULL, null=True, blank=True
    )


class FormacionAdicional(models.Model):
    """Información sobre experiencia previa en academias y carrera de interés."""
    alumno            = models.OneToOneField(Alumno, on_delete=models.CASCADE)
    estudio_previo    = models.BooleanField()
    tipo_estudio      = models.CharField(max_length=20)
    academia_anterior = models.CharField(max_length=100)
    carrera_interes   = models.CharField(max_length=100)
    segunda_carrera   = models.CharField(max_length=100, null=True, blank=True)


# ══════════════════════════════════════════════════════════════════
#  UBIGEO PERUANO
#  Datos geográficos: departamentos, provincias, distritos e instituciones educativas
#  Se cargan una sola vez desde el fixture — no se modifican desde el sistema
# ══════════════════════════════════════════════════════════════════

class Departamento(models.Model):
    nombre = models.CharField(max_length=100)
    def __str__(self):
        return self.nombre

class Provincia(models.Model):
    nombre       = models.CharField(max_length=100)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE)
    def __str__(self):
        return self.nombre

class Distrito(models.Model):
    nombre   = models.CharField(max_length=100)
    provincia = models.ForeignKey(Provincia, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.nombre} - {self.provincia.nombre} - {self.provincia.departamento.nombre}"

class InstitucionEducativa(models.Model):
    TIPO_IE = [
        ('Nacional',    'Nacional'),
        ('Particular',  'Particular'),
    ]
    nombre   = models.CharField(max_length=150)
    distrito = models.ForeignKey(Distrito, on_delete=models.CASCADE)
    tipo_ie  = models.CharField(max_length=20, choices=TIPO_IE, blank=True, default='')

    def __str__(self):
        return self.nombre
