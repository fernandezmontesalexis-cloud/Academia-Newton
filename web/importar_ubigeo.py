import os
import django
import csv

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Academia_Newton.settings')
django.setup()

from web.models import Departamento, Provincia, Distrito


ruta = os.path.join(os.getcwd(), "web", "data", "ubigeo_distrito.csv")

with open(ruta, newline="", encoding="latin-1") as file:
    reader = csv.reader(file)
    next(reader)

    for row in reader:
        departamento_nombre = row[2]
        provincia_nombre = row[3]
        distrito_nombre = row[4]

        dep, _ = Departamento.objects.get_or_create(
            nombre=departamento_nombre
        )

        prov, _ = Provincia.objects.get_or_create(
            nombre=provincia_nombre,
            departamento=dep
        )

        Distrito.objects.get_or_create(
            nombre=distrito_nombre,
            provincia=prov
        )

print("Ubigeo importado correctamente")
