"""Genera los datos de demostración de ExpoNexo para las tres bases, coherentes entre sí.

Salida (en esta carpeta):
  identidad.sql   T-SQL para Azure SQL (identidad-reservas); lotes separados por GO
  pagos.sql       SQL para Oracle (pagos); una sentencia por bloque terminado en ';'
  mesa-ayuda.js   mongosh para MongoDB (mesa-ayuda)

Reglas: IDs UUID deterministas (uuid5), así cada ejecución produce lo mismo y los tres scripts se
referencian sin errores; todo es idempotente (MERGE por id en SQL, upsert por _id en MongoDB);
nombres y empresas ficticios con correos @ejemplo.test (dominio que no recibe correo); no se tocan
las cuentas fijas ni las tablas de eventos internos (bandeja_salida, eventos_procesados).
Uso:  python datos-demo/generar.py
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import uuid

CARPETA = Path(__file__).parent
ESPACIO = uuid.UUID("6f1d4c0e-7b2a-4e5f-9a3d-2c8b1e0f5a71")
UTC = timezone.utc


def uid(tipo: str, n: int) -> str:
    return str(uuid.uuid5(ESPACIO, f"exponexo-demo/{tipo}/{n}"))


def ts(d: datetime) -> str:
    return d.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S")


def sql_str(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (int, Decimal)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def dv_nit(base: str) -> int:
    """Dígito de verificación de NIT (algoritmo DIAN)."""
    pesos = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
    total = sum(int(d) * pesos[i] for i, d in enumerate(reversed(base)))
    r = total % 11
    return r if r in (0, 1) else 11 - r


# ---------------------------------------------------------------- catálogos
EMPRESAS = [
    ("Soluciones Andinas S.A.S.", "Tecnología"), ("Café del Valle Export S.A.S.", "Alimentos"),
    ("Logística Pacífico Ltda", "Logística"), ("Construcciones Aurora S.A.S.", "Construcción"),
    ("Textiles del Caribe S.A.S.", "Textil"), ("AgroFuturo Colombia S.A.S.", "Agro"),
    ("Energía Verde Andina S.A.S.", "Energía"), ("Salud Integral del Centro S.A.S.", "Salud"),
    ("Educación Digital S.A.S.", "Educación"), ("Turismo Cóndor S.A.S.", "Turismo"),
    ("Muebles Roble S.A.S.", "Mobiliario"), ("Editorial Horizonte S.A.S.", "Editorial"),
    ("Farmacéutica del Sur S.A.S.", "Farmacéutico"), ("MetalMecánica Titán S.A.S.", "Manufactura"),
    ("Cosmética Natural S.A.S.", "Cosmética"),
]
NOMBRES = [
    "Ana María Ríos", "Carlos Pérez", "Laura Gómez", "Diego Ruiz", "Sofía Martínez", "Andrés Ramírez",
    "Paula Torres", "Julián Castro", "Valentina Ortiz", "Felipe Herrera", "Mariana Silva",
    "Sebastián Vargas", "Camila Rojas", "Daniel Molina", "Natalia Suárez", "Juan Pablo Mejía",
    "María José Londoño", "Santiago Ospina", "Diana Carolina Ruiz", "Alejandro Gil", "Isabella Correa",
    "Mateo Restrepo", "Sara Álvarez", "Samuel Jiménez", "Manuela Duarte", "Emilio Salazar",
    "Julieta Peña", "Tomás Cárdenas", "María Fernanda Cano", "Nicolás Rincón", "Daniela Escobar",
    "Juan Sebastián Vega", "Ximena Puentes", "Sergio Aguilar", "Gabriela Pineda", "Esteban Cely",
    "Lorena Ortiz", "Camilo Pardo", "Valeria Ferreira", "Ricardo Duarte",
]
SIN_TILDES = str.maketrans("áéíóúñÁÉÍÓÚÑ", "aeiounAEIOUN")


def correo_de(nombre: str, n: int) -> str:
    partes = nombre.translate(SIN_TILDES).lower().split()
    return f"{partes[0]}.{partes[-1]}{n:02d}@ejemplo.test"


ALTA = datetime(2026, 11, 1, 13, 0, tzinfo=UTC)

# ---------------------------------------------------------------- identidad
empresas = []
for i, (razon, sector) in enumerate(EMPRESAS, 1):
    base = f"9001{i:05d}"
    empresas.append(dict(id=uid("empresa", i), nit=f"{base}-{dv_nit(base)}", razon_social=razon,
                         sector=sector, sitio_web=f"https://empresa{i:02d}.ejemplo.test", logo_url=None))

usuarios = []
for i, nombre in enumerate(NOMBRES, 1):
    expositor = i <= 15
    usuarios.append(dict(
        id=uid("usuario", i), correo=correo_de(nombre, i), nombre=nombre,
        hash_contrasena="sin-acceso-datos-demo", rol="expositor" if expositor else "visitante",
        empresa_id=empresas[i - 1]["id"] if expositor else None, activo=True, correo_verificado=True,
        creado_en=ts(ALTA + timedelta(minutes=7 * i)), actualizado_en=ts(ALTA + timedelta(minutes=7 * i)),
    ))
expositores = [u for u in usuarios if u["rol"] == "expositor"]
visitantes = [u for u in usuarios if u["rol"] == "visitante"]

factores = [dict(id=uid("factor", i), usuario_id=u["id"], tipo="correo", secreto_cifrado=None,
                 activo=True, preferido=True, ultimo_paso=None, creado_en=u["creado_en"])
            for i, u in enumerate(usuarios, 1)]

EVENTOS = [
    ("ExpoNexo Innovación 2026", "exponexo-innovacion-2026", "Feria de innovación, tecnología y negocios.",
     datetime(2026, 11, 24, 14, 0, tzinfo=UTC), datetime(2026, 11, 27, 23, 0, tzinfo=UTC), "publicado", "85000.00", 5000),
    ("ExpoNexo Manufactura 2027", "exponexo-manufactura-2027", "Manufactura, automatización e industria 4.0.",
     datetime(2027, 3, 9, 14, 0, tzinfo=UTC), datetime(2027, 3, 12, 23, 0, tzinfo=UTC), "publicado", "120000.00", 4000),
    ("ExpoNexo Agroindustria 2027", "exponexo-agroindustria-2027", "Agroindustria, sostenibilidad y cadena de suministro.",
     datetime(2027, 6, 15, 14, 0, tzinfo=UTC), datetime(2027, 6, 18, 23, 0, tzinfo=UTC), "borrador", "95000.00", 3000),
]
eventos = [dict(id=uid("evento", i), nombre=n, slug=s, descripcion=d, inicio=ts(a), fin=ts(b), estado=e,
                precio_entrada=Decimal(p), aforo=af, creado_en=ts(ALTA), actualizado_en=ts(ALTA))
           for i, (n, s, d, a, b, e, p, af) in enumerate(EVENTOS, 1)]

PABELLONES = [("Pabellón Norte", "N"), ("Pabellón Sur", "S"), ("Pabellón Oriente", "O"), ("Pabellón Occidente", "C")]
pabellones, stands, salas = [], [], []
PRECIO = {"basico": Decimal("2500000.00"), "esquinero": Decimal("3200000.00"), "isla": Decimal("4800000.00")}
AREA = {"basico": Decimal("9.00"), "esquinero": Decimal("12.00"), "isla": Decimal("18.00")}
for p, (nombre, letra) in enumerate(PABELLONES, 1):
    pid = uid("pabellon", p)
    pabellones.append(dict(id=pid, nombre=nombre, capacidad_stands=12, plano_url=None,
                           creado_en=ts(ALTA), actualizado_en=ts(ALTA)))
    for fila in range(1, 4):
        for col in range(1, 5):
            n = (p - 1) * 12 + (fila - 1) * 4 + col
            tipo = "esquinero" if fila in (1, 3) and col in (1, 4) else ("isla" if fila == 2 and col in (2, 3) else "basico")
            stands.append(dict(id=uid("stand", n), pabellon_id=pid, codigo=f"{letra}-{fila}{col:02d}",
                               metros_cuadrados=AREA[tipo], tipo=tipo, precio_base=PRECIO[tipo], fila=fila,
                               columna=col, creado_en=ts(ALTA), actualizado_en=ts(ALTA)))
    for s in (1, 2):
        salas.append(dict(id=uid("sala", (p - 1) * 2 + s), pabellon_id=pid, codigo=f"SALA-{letra}{s}", capacidad=4 + 2 * s))

# Reservas: 15 en el evento 1 y 10 en el 2; cada stand una sola vez por evento
ESTADOS_RESERVA = (["pagada"] * 12) + (["pendiente_pago"] * 7) + (["cancelada"] * 4) + (["vencida"] * 2)
reservas = []
for r in range(1, 26):
    evento = eventos[0] if r <= 15 else eventos[1]
    stand = stands[(r - 1) * 2 if r <= 15 else (r - 16) * 4 + 1]
    expositor = expositores[(r - 1) % 15]
    creado = ALTA + timedelta(hours=r)
    estado = ESTADOS_RESERVA[r - 1]
    reservas.append(dict(
        id=uid("reserva", r), evento_id=evento["id"], stand_id=stand["id"], empresa_id=expositor["empresa_id"],
        usuario_id=expositor["id"], estado=estado, monto=stand["precio_base"],
        vence_en=ts(creado + timedelta(minutes=30)), orden_pago_id=None, clave_idempotencia=f"demo-reserva-{r:03d}",
        version=1, creado_en=ts(creado), actualizado_en=ts(creado),
    ))

# Entradas: 25 en el evento 1 y 15 en el 2
ESTADOS_E1 = ["activa"] * 9 + ["usada"] * 6 + ["pendiente_pago"] * 6 + ["cancelada"] * 4
ESTADOS_E2 = ["activa"] * 5 + ["pendiente_pago"] * 7 + ["cancelada"] * 3
TIPOS = ["general", "general", "negocios", "general", "prensa"]
entradas = []
for e in range(1, 41):
    evento = eventos[0] if e <= 25 else eventos[1]
    estado = ESTADOS_E1[e - 1] if e <= 25 else ESTADOS_E2[e - 26]
    creada = ALTA + timedelta(days=1, minutes=11 * e)
    entradas.append(dict(
        id=uid("entrada", e), evento_id=evento["id"], usuario_id=visitantes[(e - 1) % 25]["id"],
        tipo=TIPOS[(e - 1) % 5], estado=estado, orden_pago_id=None,
        codigo_qr=f"demo-qr-{e:03d}" if estado in ("activa", "usada") else None,
        usada_en=ts(datetime(2026, 11, 24, 15, 0, tzinfo=UTC) + timedelta(minutes=5 * e)) if estado == "usada" else None,
        usada_en_dispositivo="TRN-01" if estado == "usada" else None, creada_en=ts(creada),
    ))

# Agenda del evento 1: disponibilidad de 10 expositores y 20 citas en franjas de 30 min sin cruces
disponibilidad, citas = [], []
for d in range(1, 11):
    dia = datetime(2026, 11, 25, 14, 0, tzinfo=UTC)
    disponibilidad.append(dict(id=uid("disponibilidad", d), usuario_id=expositores[d - 1]["id"],
                               evento_id=eventos[0]["id"], desde=ts(dia), hasta=ts(dia + timedelta(hours=6))))
ESTADOS_CITA = ["aceptada"] * 8 + ["propuesta"] * 6 + ["rechazada"] * 4 + ["cancelada"] * 2
for c in range(1, 21):
    inicio = datetime(2026, 11, 25, 14, 0, tzinfo=UTC) + timedelta(minutes=30 * (c - 1))
    estado = ESTADOS_CITA[c - 1]
    citas.append(dict(
        id=uid("cita", c), evento_id=eventos[0]["id"], solicitante_id=visitantes[c - 1]["id"],
        anfitrion_id=expositores[(c - 1) % 10]["id"], sala_id=salas[(c - 1) % 8]["id"] if estado == "aceptada" else None,
        inicio=ts(inicio), fin=ts(inicio + timedelta(minutes=30)), estado=estado,
        mensaje="Me interesa conocer su portafolio y condiciones comerciales.", creada_en=ts(ALTA + timedelta(days=2, minutes=c)),
    ))

# ---------------------------------------------------------------- pagos (coherente con identidad)
ordenes, transacciones, facturas, detalles, reembolsos = [], [], [], [], []
IVA = Decimal("0.19")


def agregar_orden(n, referencia, origen, usuario_id, monto, estado, creada, cliente, descripcion):
    oid = uid("orden", n)
    ordenes.append(dict(id=oid, referencia=referencia, origen=origen, usuario_id=usuario_id, monto=monto,
                        moneda="COP", estado=estado, clave_idempotencia=f"demo-orden-{n:03d}",
                        creada_en=ts(creada), actualizada_en=ts(creada + timedelta(minutes=5))))
    tx_estado = {"aprobada": "aprobada", "reembolsada": "aprobada", "rechazada": "rechazada"}.get(estado, "iniciada")
    transacciones.append(dict(id=uid("transaccion", n), orden_id=oid, metodo="qr" if n % 2 else "tarjeta",
                              estado=tx_estado, codigo_autorizacion=f"AUT{n:06d}" if tx_estado == "aprobada" else None,
                              ocurrida_en=ts(creada + timedelta(minutes=4))))
    if estado in ("aprobada", "reembolsada"):
        subtotal = monto
        impuesto = (subtotal * IVA).quantize(Decimal("0.01"))
        fid = uid("factura", n)
        facturas.append(dict(id=fid, orden_id=oid, fecha=ts(creada + timedelta(minutes=5)), nit_cliente=cliente[0],
                             razon_social=cliente[1], subtotal=subtotal, impuesto=impuesto, total=subtotal + impuesto,
                             estado="anulada" if estado == "reembolsada" else "emitida"))
        detalles.append(dict(id=uid("detalle", n), factura_id=fid, descripcion=descripcion, cantidad=Decimal("1.00"),
                             valor_unitario=subtotal, impuesto=impuesto))
    return oid


n_orden = 0
empresa_por_id = {e["id"]: e for e in empresas}
for r in reservas:
    estado_orden = {"pagada": "aprobada"}.get(r["estado"])
    if r["estado"] == "pendiente_pago" and int(r["clave_idempotencia"][-3:]) % 2 == 0:
        estado_orden = "pendiente"
    if r["estado"] == "cancelada" and r["clave_idempotencia"].endswith("020"):
        estado_orden = "reembolsada"
    if r["estado"] == "vencida":
        estado_orden = "rechazada"
    if estado_orden:
        n_orden += 1
        emp = empresa_por_id[r["empresa_id"]]
        r["orden_pago_id"] = agregar_orden(n_orden, r["id"], "stand", r["usuario_id"], r["monto"], estado_orden,
                                           datetime.strptime(r["creado_en"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC) + timedelta(minutes=10),
                                           (emp["nit"], emp["razon_social"]), "Reserva de stand")
        if estado_orden == "reembolsada":
            reembolsos.append(dict(id=uid("reembolso", 1), orden_id=r["orden_pago_id"], monto=r["monto"],
                                   motivo="Cancelación del expositor dentro del plazo permitido.", estado="aprobado",
                                   creado_en=ts(ALTA + timedelta(days=3))))

usuario_por_id = {u["id"]: u for u in usuarios}
evento_por_id = {e["id"]: e for e in eventos}
for e in entradas:
    if e["estado"] in ("activa", "usada"):
        n_orden += 1
        persona = usuario_por_id[e["usuario_id"]]
        e["orden_pago_id"] = agregar_orden(n_orden, e["id"], "entrada", e["usuario_id"],
                                           evento_por_id[e["evento_id"]]["precio_entrada"], "aprobada",
                                           datetime.strptime(e["creada_en"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC) + timedelta(minutes=3),
                                           ("222222222222", persona["nombre"]), f"Entrada {e['tipo']}")
# Una devolución en trámite sobre una entrada pagada
reembolsos.append(dict(id=uid("reembolso", 2), orden_id=entradas[0]["orden_pago_id"],
                       monto=evento_por_id[entradas[0]["evento_id"]]["precio_entrada"],
                       motivo="Solicitud del visitante por cambio de agenda.", estado="solicitado",
                       creado_en=ts(ALTA + timedelta(days=4))))


# ---------------------------------------------------------------- escritura de scripts
def merge_tsql(tabla: str, filas: list[dict]) -> str:
    cols = list(filas[0].keys())
    valores = ",\n".join("  (" + ", ".join(sql_str(f[c]) for c in cols) + ")" for f in filas)
    sets = ", ".join(f"t.{c} = s.{c}" for c in cols if c != "id")
    return (f"MERGE dbo.{tabla} AS t\nUSING (VALUES\n{valores}\n) AS s ({', '.join(cols)})\nON t.id = s.id\n"
            f"WHEN MATCHED THEN UPDATE SET {sets}\n"
            f"WHEN NOT MATCHED THEN INSERT ({', '.join(cols)}) VALUES ({', '.join('s.' + c for c in cols)});\nGO\n")


def merge_oracle(tabla: str, filas: list[dict], fechas: set[str], extra_insert: dict | None = None) -> str:
    bloques = []
    for f in filas:
        cols = list(f.keys())
        sel = ", ".join((f"TO_TIMESTAMP_TZ({sql_str(f[c])} || ' +00:00', 'YYYY-MM-DD HH24:MI:SS TZH:TZM')" if c in fechas
                         else sql_str(f[c])) + f" AS {c}" for c in cols)
        ins_cols = cols + list((extra_insert or {}).keys())
        ins_vals = [f"s.{c}" for c in cols] + list((extra_insert or {}).values())
        bloques.append(f"MERGE INTO {tabla} t USING (SELECT {sel} FROM dual) s ON (t.id = s.id)\n"
                       f"WHEN NOT MATCHED THEN INSERT ({', '.join(ins_cols)}) VALUES ({', '.join(ins_vals)});")
    return "\n".join(bloques) + "\n"


cabecera = "Generado por datos-demo/generar.py: no editar a mano."
identidad = [f"-- {cabecera}\nSET NOCOUNT ON;\nGO\n"]
for tabla, filas in [("empresas", empresas), ("usuarios", usuarios), ("factores_mfa", factores),
                     ("eventos", eventos), ("pabellones", pabellones), ("stands", stands), ("salas", salas),
                     ("reservas_stand", reservas), ("entradas", entradas), ("disponibilidad", disponibilidad),
                     ("citas", citas)]:
    identidad.append(f"-- {tabla}: {len(filas)}\n" + merge_tsql(tabla, filas))
(CARPETA / "identidad.sql").write_text("\n".join(identidad), encoding="utf-8", newline="\n")

pagos = [f"-- {cabecera}"]
pagos.append(merge_oracle("ordenes_pago", ordenes, {"creada_en", "actualizada_en"}))
pagos.append(merge_oracle("transacciones", transacciones, {"ocurrida_en"}))
pagos.append(merge_oracle("facturas", facturas, {"fecha"},
                          {"numero": "'EXN-' || LPAD(TO_CHAR(seq_numero_factura.NEXTVAL), 6, '0')"}))
pagos.append(merge_oracle("detalle_factura", detalles, set()))
pagos.append(merge_oracle("reembolsos", reembolsos, {"creado_en"}))
pagos.append("COMMIT;\n")
(CARPETA / "pagos.sql").write_text("\n".join(pagos), encoding="utf-8", newline="\n")

# ---------------------------------------------------------------- mesa de ayuda (MongoDB)
UBICACIONES = ["Pabellón Norte", "Pabellón Sur", "Pabellón Oriente", "Pabellón Occidente", "Acceso principal", "Plazoleta de comidas"]
DESCRIPCIONES = {
    "red": "Sin conexión a internet en la zona de stands.", "electrico": "Toma eléctrica sin energía en el stand.",
    "mobiliario": "Mesa del stand llegó averiada.", "acceso": "Torniquete no lee los códigos QR.",
    "dispositivo": "Kiosco de registro no responde.", "otro": "Solicitud de señalización adicional.",
}
CATEGORIAS = list(DESCRIPCIONES)
PRIORIDADES = ["baja", "media", "alta", "critica"]
SLA = {"baja": 480, "media": 240, "alta": 120, "critica": 60}
FLUJO = {
    "abierto": [("abierto", "N1")], "en_atencion": [("abierto", "N1"), ("en_atencion", "N1")],
    "escalado": [("abierto", "N1"), ("en_atencion", "N1"), ("escalado", "N2")],
    "resuelto": [("abierto", "N1"), ("en_atencion", "N1"), ("resuelto", "N1")],
    "cerrado": [("abierto", "N1"), ("en_atencion", "N1"), ("resuelto", "N1"), ("cerrado", "N1")],
}
ESTADOS_TICKET = ["abierto"] * 6 + ["en_atencion"] * 6 + ["escalado"] * 4 + ["resuelto"] * 7 + ["cerrado"] * 7
DISPOSITIVOS = [("KSK", "kiosco", 4), ("TRN", "torniquete", 5), ("PNT", "pantalla", 3)]

dispositivos = []
for prefijo, tipo, cantidad in DISPOSITIVOS:
    for k in range(1, cantidad + 1):
        dispositivos.append(dict(_id=uid("dispositivo", len(dispositivos) + 1), codigo=f"{prefijo}-{k:02d}", tipo=tipo,
                                 ubicacion=UBICACIONES[len(dispositivos) % len(UBICACIONES)]))

tickets = []
for t in range(1, 31):
    categoria = CATEGORIAS[(t - 1) % 6]
    prioridad = PRIORIDADES[(t - 1) % 4]
    estado = ESTADOS_TICKET[t - 1]
    creado = datetime(2026, 11, 24, 14, 0, tzinfo=UTC) + timedelta(minutes=37 * t)
    pasos = FLUJO[estado]
    tickets.append(dict(
        _id=uid("ticket", t), numero=f"TCK-{t:04d}", evento_id=eventos[0]["id"],
        creado_por_id=expositores[(t - 1) % 15]["id"], ubicacion=UBICACIONES[(t - 1) % 6], categoria=categoria,
        prioridad=prioridad, nivel_actual=pasos[-1][1], estado=estado, descripcion=DESCRIPCIONES[categoria],
        creado=creado, sla_min=SLA[prioridad], pasos=pasos,
        resuelto_en_min=(SLA[prioridad] // 2 if t % 5 else SLA[prioridad] + 30) if estado in ("resuelto", "cerrado") else None,
    ))


def js_fecha(d: datetime) -> str:
    return f'ISODate("{d.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}")'


lineas = [
    f"// {cabecera}",
    "// Uso: mongosh \"<uri>\" --eval \"var ASIGNADOS=['<id personal>','<id admin>']\" --file mesa-ayuda.js",
    "// ASIGNADOS son los ids de las cuentas fijas con rol personal o administrador (se consultan en",
    "// identidad al cargar); sin ellos los tickets quedan sin asignar.",
    "const asignados = (typeof ASIGNADOS !== 'undefined' && ASIGNADOS.length) ? ASIGNADOS : [null];",
    "const ahora = new Date();",
    "// Misma definición que crea mesa de ayuda: series de tiempo con retención de 30 días",
    "if (!db.getCollectionNames().includes('lecturas_dispositivo')) {",
    "  db.createCollection('lecturas_dispositivo', { timeseries: { timeField: 'momento', metaField: 'dispositivo_id',",
    "    granularity: 'seconds' }, expireAfterSeconds: 30 * 24 * 3600 });",
    "}",
    "let cambios = 0;",
    "",
    "const dispositivos = [",
]
for i, d in enumerate(dispositivos):
    sin_reporte = d["codigo"] in ("KSK-04", "PNT-03")
    lineas.append(
        f"  {{ _id: '{d['_id']}', codigo: '{d['codigo']}', tipo: '{d['tipo']}', ubicacion: '{d['ubicacion']}', "
        f"secreto_hash: 'sin-acceso-datos-demo', estado: '{'sin_reporte' if sin_reporte else 'en_linea'}', "
        f"ultimo_reporte_en: new Date(ahora.getTime() - {(180 if sin_reporte else 5)} * 60000), "
        f"version_firmware: '2.{i % 3}.{i % 4}', ticket_abierto_id: {repr(tickets[4]['_id']) if d['codigo'] == 'KSK-04' else 'null'} }},")
lineas += [
    "];",
    "for (const d of dispositivos) {",
    "  cambios += db.dispositivos.replaceOne({ _id: d._id }, d, { upsert: true }).upsertedCount;",
    "}",
    "",
    "const tickets = [",
]
for t in tickets:
    historial = []
    momento = t["creado"]
    previo = None
    for k, (estado_paso, nivel) in enumerate(t["pasos"]):
        if k:
            momento = momento + timedelta(minutes=(t["resuelto_en_min"] or 40) // max(1, len(t["pasos"]) - 1))
        actor = f"'{t['creado_por_id']}'" if k == 0 else "asignados[0]"
        historial.append(f"{{ fecha: {js_fecha(momento)}, actor_id: {actor}, de_estado: {repr(previo) if previo else 'null'}, "
                         f"a_estado: '{estado_paso}', nivel: '{nivel}', nota: {repr('Ticket creado' if k == 0 else 'Cambio de estado')} }}")
        previo = estado_paso
    asignado = "null" if t["estado"] == "abierto" else ("asignados[asignados.length - 1]" if t["estado"] == "escalado" else "asignados[0]")
    sla_vence = t["creado"] + timedelta(minutes=t["sla_min"])
    cumplido = "null" if t["resuelto_en_min"] is None else ("true" if t["resuelto_en_min"] <= t["sla_min"] else "false")
    lineas.append(
        f"  {{ _id: '{t['_id']}', numero: '{t['numero']}', evento_id: '{t['evento_id']}', creado_por_id: '{t['creado_por_id']}', "
        f"ubicacion: '{t['ubicacion']}', categoria: '{t['categoria']}', prioridad: '{t['prioridad']}', "
        f"nivel_actual: '{t['nivel_actual']}', estado: '{t['estado']}', asignado_a_id: {asignado}, "
        f"descripcion: {repr(t['descripcion'])}, sla_vence_en: {js_fecha(sla_vence)}, sla_cumplido: {cumplido}, "
        f"sla_alerta_emitida: {'true' if cumplido == 'false' else 'false'}, historial: [{', '.join(historial)}], "
        f"creado_en: {js_fecha(t['creado'])} }},")
lineas += [
    "];",
    "for (const t of tickets) {",
    "  cambios += db.tickets.replaceOne({ _id: t._id }, t, { upsert: true }).upsertedCount;",
    "}",
    "",
    "// Lecturas de las últimas 5 horas (la colección borra sola lo más viejo que su retención)",
    "const conReporte = dispositivos.filter(d => d.estado === 'en_linea');",
    "db.lecturas_dispositivo.deleteMany({ dispositivo_id: { $in: dispositivos.map(d => d._id) } });",
    "const lecturas = [];",
    "conReporte.forEach((d, i) => {",
    "  for (let k = 0; k < 20; k++) {",
    "    lecturas.push({ _id: require('crypto').randomUUID(), dispositivo_id: d._id,",
    "      momento: new Date(ahora.getTime() - k * 15 * 60000),",
    "      cpu_porcentaje: 15 + ((i * 7 + k * 3) % 50), memoria_porcentaje: 30 + ((i * 5 + k * 2) % 45),",
    "      temperatura_c: 35 + ((i + k) % 20), conectado: true });",
    "  }",
    "});",
    "db.lecturas_dispositivo.insertMany(lecturas);",
    "printjson({ nuevos: cambios, dispositivos: dispositivos.length, tickets: tickets.length, lecturas: lecturas.length });",
]
(CARPETA / "mesa-ayuda.js").write_text("\n".join(lineas) + "\n", encoding="utf-8", newline="\n")

print(f"identidad: {len(empresas)} empresas, {len(usuarios)} usuarios, {len(eventos)} eventos, {len(stands)} stands, "
      f"{len(salas)} salas, {len(reservas)} reservas, {len(entradas)} entradas, {len(citas)} citas")
print(f"pagos: {len(ordenes)} órdenes, {len(facturas)} facturas, {len(reembolsos)} reembolsos")
print(f"mesa-ayuda: {len(dispositivos)} dispositivos, {len(tickets)} tickets, 200 lecturas")
