from django.db import models
from django.contrib.auth.models import User

class Sede(models.Model):
    nombre = models.CharField(max_length=70)
    direccion = models.CharField(max_length=100)

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

    def __str__(self):
        return self.user.username
    

class Apoderado(models.Model):
    nombre_completo = models.CharField(max_length=100)
    dni = models.CharField(max_length=8)
    celular = models.CharField(max_length=9)
    direccion = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre_completo
    

class Alumno(models.Model):
    apellido_paterno = models.CharField(max_length=70)
    apellido_materno = models.CharField(max_length=70)
    nombres = models.CharField(max_length=70)
    dni = models.CharField(max_length=8)
    celular = models.CharField(max_length=9)
    fecha_nacimiento = models.DateField()
    direccion = models.CharField(max_length=100)
    distrito = models.CharField(max_length=50)
    email = models.EmailField()

    Sede = models.ForeignKey(Sede, on_delete=models.CASCADE)
    apoderado = models.ForeignKey(Apoderado, on_delete=models.CASCADE)

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
    

class Matricula(models.Model):
    Alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    ciclo = models.ForeignKey(Ciclo, on_delete=models.CASCADE)

    fecha_matricula = models.DateField()
    estado = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.Alumno} {self.ciclo}"
    

class Pago (models.Model):
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE)
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE)

    fecha_pago = models.DateField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=30)
    estado = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.monto} {self.matricula}"


#no tocar falta implementar
class FormacionAcademica(models.Model):
    alumno = models.OneToOneField(Alumno, on_delete=models.CASCADE)
    tipo_institucion = models.CharField(max_length=20)
    nombre_ie = models.CharField(max_length=100)
    distrito_ie = models.CharField(max_length=50)



#no tocar falta implementar
class FormacionAdicional(models.Model):
    alumno = models.OneToOneField(Alumno, on_delete=models.CASCADE)
    estudio_previo = models.BooleanField()
    tipo_estudio = models.CharField(max_length=20)
    academia_anterior = models.CharField(max_length=100)
    carrera_interes = models.CharField(max_length=100)
    segunda_carrera = models.CharField(max_length=100, null=True, blank=True)