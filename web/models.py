from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import RegexValidator

class Sede(models.Model):
    nombre = models.CharField(max_length=70)
    direccion = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
    

class Perfil(models.Model):

    TIPO_USUARIO = [
        ('admin','Administrador'),
        ('secretaria','Secretaria'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO)
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE)
    fecha_desactivacion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username
    

class Apoderado(models.Model):
    nombre_completo = models.CharField(max_length=100)
    dni = models.CharField(max_length=8, unique=True) 
    celular = models.CharField(max_length=9)
    direccion = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre_completo
    

class Alumno(models.Model):
    apellido_paterno = models.CharField(max_length=70)
    apellido_materno = models.CharField(max_length=70)
    nombres = models.CharField(max_length=70)
    dni = models.CharField(max_length=8, unique=True,
                           validators=[RegexValidator(r'^\d{8}$','El DNI debe tener 8 digitos')])
    celular = models.CharField(max_length=9)
    fecha_nacimiento = models.DateField()
    direccion = models.CharField(max_length=100)
    distrito = models.ForeignKey('Distrito', on_delete=models.SET_NULL, null=True)
    email = models.EmailField(null=True, blank=True)
    ESTADOS =[
        ('activo',   'Activo'),
        ('inactivo', 'Inactivo'),
        ('bloqueado','Bloqueado'),
    ]
    estado = models.CharField(max_length=10, choices=ESTADOS, default='activo' )

    sede = models.ForeignKey(Sede, on_delete=models.CASCADE)
    apoderado = models.ForeignKey(Apoderado, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.nombres} {self.apellido_paterno}"
    

class Ciclo(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    sede = models.ForeignKey(Sede, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre

    @property
    def alerta_vigencia(self):
        today = timezone.localdate()
        if self.fecha_fin < today:
            return 'finalizado'
        if self.fecha_inicio > today:
            return 'pendiente'
        if (self.fecha_fin - today).days <= 14:
            return 'finaliza_pronto'
        return 'activo'


class Matricula(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    ciclo = models.ForeignKey(Ciclo, on_delete=models.CASCADE)
    fecha_matricula = models.DateField()
    proximo_pago = models.DateField(null=True, blank=True)

    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADOS)

    registrado_por = models.ForeignKey(Perfil, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.alumno} {self.ciclo}"

    def total_pagado(self):
        # sum() usa la caché de prefetch_related cuando está disponible (evita N+1)
        return sum(p.monto for p in self.pago_set.all()) or 0

    def deuda(self):
        return self.ciclo.precio - self.total_pagado()

class Pago(models.Model):
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE)
    registrado_por = models.ForeignKey(Perfil, on_delete=models.CASCADE)
    apoderado = models.CharField(max_length=100, blank=True, default='')

    fecha_pago = models.DateField(default=timezone.now)
    monto = models.DecimalField(max_digits=10, decimal_places=2)

    METODOS = [
        ('efectivo', 'Efectivo'),
        ('yape', 'Yape'),
        ('transferencia', 'Transferencia'),
    ]
    metodo_pago = models.CharField(max_length=20, choices=METODOS)

    def __str__(self):
        return f"{self.monto} {self.matricula}"

    # 🔥 NUEVO
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        matricula = self.matricula

        if matricula.deuda() <= 0:
            matricula.estado = 'pagado'
        else:
            matricula.estado = 'pendiente'

        matricula.save()

class DesactivacionLog(models.Model):
    MOTIVOS = [
        ('retiro_voluntario', 'Retiro voluntario'),
        ('deuda_pendiente',   'Deuda pendiente'),
        ('inasistencia',      'Inasistencia prolongada'),
        ('expulsion',         'Expulsión'),
        ('otro',              'Otro'),
    ]
    alumno         = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='desactivaciones')
    motivo         = models.CharField(max_length=30, choices=MOTIVOS)
    comentario     = models.TextField(blank=True)
    fecha          = models.DateTimeField(auto_now_add=True)
    registrado_por = models.ForeignKey(Perfil, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.alumno} — {self.get_motivo_display()}"


class FormacionAcademica(models.Model):
    alumno = models.OneToOneField(Alumno, on_delete=models.CASCADE)
    tipo_institucion = models.CharField(max_length=20)
    institucion = models.ForeignKey(
    'InstitucionEducativa',on_delete=models.SET_NULL,null=True,blank=True)
    


class FormacionAdicional(models.Model):
    alumno = models.OneToOneField(Alumno, on_delete=models.CASCADE)
    estudio_previo = models.BooleanField()
    tipo_estudio = models.CharField(max_length=20)
    academia_anterior = models.CharField(max_length=100)
    carrera_interes = models.CharField(max_length=100)
    segunda_carrera = models.CharField(max_length=100, null=True, blank=True)

class Departamento(models.Model):
    nombre = models.CharField(max_length=100)
    def __str__(self):
        return self.nombre

class Provincia(models.Model):
    nombre = models.CharField(max_length=100)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE)
    def __str__(self):
        return self.nombre

class Distrito(models.Model):
    nombre = models.CharField(max_length=100)
    provincia = models.ForeignKey(Provincia, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.nombre} - {self.provincia.nombre} - {self.provincia.departamento.nombre}"
    
class InstitucionEducativa(models.Model):
    TIPO_IE = [
        ('Nacional', 'Nacional'),
        ('Particular', 'Particular'),
    ]
    nombre = models.CharField(max_length=150)
    distrito = models.ForeignKey(Distrito, on_delete=models.CASCADE)
    tipo_ie = models.CharField(max_length=20, choices=TIPO_IE, blank=True, default='')

    def __str__(self):
        return self.nombre
    
    