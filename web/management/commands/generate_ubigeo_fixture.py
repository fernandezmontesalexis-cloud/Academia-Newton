"""
Comando: python manage.py generate_ubigeo_fixture

Lee web/data/ubigeo_distrito.csv y regenera fixtures/ubigeo.json.
Útil si el CSV cambia o se necesita reiniciar el fixture desde cero.

Uso habitual (una sola vez por instalación nueva):
    python manage.py generate_ubigeo_fixture
    python manage.py loaddata fixtures/ubigeo.json
"""
import csv
import json
import os

from django.core.management.base import BaseCommand

VALID_DEPTS = {
    "AMAZONAS", "ANCASH", "APURIMAC", "AREQUIPA", "AYACUCHO", "CAJAMARCA",
    "CALLAO", "CUSCO", "HUANCAVELICA", "HUANUCO", "ICA", "JUNIN",
    "LA LIBERTAD", "LAMBAYEQUE", "LIMA", "LORETO", "MADRE DE DIOS",
    "MOQUEGUA", "PASCO", "PIURA", "PUNO", "SAN MARTIN", "TACNA",
    "TUMBES", "UCAYALI",
}


class Command(BaseCommand):
    help = "Genera fixtures/ubigeo.json desde web/data/ubigeo_distrito.csv"

    def handle(self, *args, **options):
        csv_path = os.path.join("web", "data", "ubigeo_distrito.csv")
        out_path = os.path.join("fixtures", "ubigeo.json")

        if not os.path.exists(csv_path):
            self.stderr.write(self.style.ERROR(f"No se encontró: {csv_path}"))
            return

        os.makedirs("fixtures", exist_ok=True)

        departamentos = {}
        provincias = {}
        fixture = []
        dept_id = prov_id = dist_id = 0

        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dept = row["departamento"].strip()
                prov = row["provincia"].strip()
                dist = row["distrito"].strip()

                if dept not in VALID_DEPTS:
                    continue

                if dept not in departamentos:
                    dept_id += 1
                    departamentos[dept] = dept_id
                    fixture.append({
                        "model": "web.departamento",
                        "pk": dept_id,
                        "fields": {"nombre": dept},
                    })

                prov_key = (dept, prov)
                if prov_key not in provincias:
                    prov_id += 1
                    provincias[prov_key] = prov_id
                    fixture.append({
                        "model": "web.provincia",
                        "pk": prov_id,
                        "fields": {
                            "nombre": prov,
                            "departamento": departamentos[dept],
                        },
                    })

                dist_id += 1
                fixture.append({
                    "model": "web.distrito",
                    "pk": dist_id,
                    "fields": {
                        "nombre": dist,
                        "provincia": provincias[prov_key],
                    },
                })

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(fixture, f, ensure_ascii=False, indent=2)

        self.stdout.write(self.style.SUCCESS(f"Fixture generado: {out_path}"))
        self.stdout.write(f"  Departamentos : {len(departamentos)}")
        self.stdout.write(f"  Provincias    : {len(provincias)}")
        self.stdout.write(f"  Distritos     : {dist_id}")
        self.stdout.write("")
        self.stdout.write("Para cargar los datos:")
        self.stdout.write("  python manage.py loaddata fixtures/ubigeo.json")
