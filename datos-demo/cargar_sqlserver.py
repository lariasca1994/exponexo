"""Carga identidad.sql en SQL Server y verifica conteos y coherencia.

Uso: python datos-demo/cargar_sqlserver.py "<cadena ODBC>" [--asignados <archivo>]
Con --asignados escribe en ese archivo los ids de las cuentas fijas con rol personal o
administrador (los usa el script de MongoDB para asignar tickets). La base puede estar pausada:
el primer intento la despierta y se reintenta.
"""
import sys
import time
from pathlib import Path

import pyodbc

ESPERADO = {"empresas": 15, "eventos": 3, "pabellones": 4, "stands": 48, "salas": 8, "reservas_stand": 25,
            "entradas": 40, "disponibilidad": 10, "citas": 20}
COHERENCIA = {
    "reservas pagadas sin orden": "SELECT COUNT(*) FROM dbo.reservas_stand WHERE estado = 'pagada' AND orden_pago_id IS NULL",
    "entradas activas o usadas sin orden": "SELECT COUNT(*) FROM dbo.entradas WHERE estado IN ('activa','usada') AND orden_pago_id IS NULL",
    "stands con dos reservas vigentes": """SELECT COUNT(*) FROM (SELECT evento_id, stand_id FROM dbo.reservas_stand
        WHERE estado IN ('pendiente_pago','pagada') GROUP BY evento_id, stand_id HAVING COUNT(*) > 1) d""",
    "citas aceptadas que se cruzan": """SELECT COUNT(*) FROM dbo.citas a JOIN dbo.citas b ON a.id < b.id
        AND a.estado = 'aceptada' AND b.estado = 'aceptada' AND a.inicio < b.fin AND b.inicio < a.fin
        AND (a.sala_id = b.sala_id OR a.solicitante_id IN (b.solicitante_id, b.anfitrion_id)
             OR a.anfitrion_id IN (b.solicitante_id, b.anfitrion_id))""",
}


def conectar(cadena: str) -> pyodbc.Connection:
    for intento in range(1, 6):
        try:
            return pyodbc.connect(cadena, timeout=90, autocommit=False)
        except pyodbc.Error as error:
            print(f"Intento {intento}: la base no respondió ({str(error)[:80]}…); reintento en 30 s")
            time.sleep(30)
    sys.exit("No se pudo conectar a SQL Server")


def main() -> None:
    conexion = conectar(sys.argv[1])
    cursor = conexion.cursor()
    script = (Path(__file__).parent / "identidad.sql").read_text(encoding="utf-8")
    for lote in [b.strip() for b in script.split("\nGO\n") if b.strip() and not b.strip().startswith("SET NOCOUNT")]:
        cursor.execute(lote)
    conexion.commit()

    fallas = 0
    for tabla, esperado in ESPERADO.items():
        demo = cursor.execute(f"SELECT COUNT(*) FROM dbo.{tabla}").fetchone()[0]
        estado = "ok" if demo >= esperado else "FALTAN"
        fallas += estado != "ok"
        print(f"{tabla}: {demo} (mínimo {esperado}) {estado}")
    demo_usuarios = cursor.execute("SELECT COUNT(*) FROM dbo.usuarios WHERE correo LIKE '%@ejemplo.test'").fetchone()[0]
    print(f"usuarios de demostración: {demo_usuarios}")
    fallas += demo_usuarios != 40
    for nombre, consulta in COHERENCIA.items():
        valor = cursor.execute(consulta).fetchone()[0]
        print(f"{nombre}: {valor}")
        fallas += valor != 0

    if "--asignados" in sys.argv:
        filas = cursor.execute("SELECT id FROM dbo.usuarios WHERE rol IN ('personal','administrador') "
                               "AND correo NOT LIKE '%@ejemplo.test' ORDER BY rol DESC, creado_en").fetchall()
        destino = Path(sys.argv[sys.argv.index("--asignados") + 1])
        destino.write_text("var ASIGNADOS = [" + ", ".join(f"'{f[0]}'" for f in filas) + "];", encoding="utf-8")
        print(f"cuentas para asignar tickets: {len(filas)}")
    conexion.close()
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
