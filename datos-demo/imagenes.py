"""Genera y sube a Cloudinary las imágenes de los datos de demostración.

  - Portada de cada evento (1200 x 630), con la paleta del proyecto.
  - Logo de cada empresa expositora (monograma, 256 x 256).
  - Plano de cada pabellón con sus stands por tipo (1200 x 720).

Uso:
  python datos-demo/imagenes.py --solo-generar               genera en datos-demo/imagenes/
  python datos-demo/imagenes.py --subir <salida.sql>         sube y escribe los UPDATE de las URL
Para subir usa CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY y CLOUDINARY_API_SECRET (nunca impresos).
Las URL no se guardan en el repositorio: dependen de la nube configurada.
"""
import hashlib
import json
import os
import sys
import time
import urllib.request
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CARPETA = Path(__file__).parent
sys.path.insert(0, str(CARPETA))
import generar  # noqa: E402  (reutiliza catálogos e identificadores deterministas)

SALIDA = CARPETA / "imagenes"
CARPETA_NUBE = "exponexo/demo"
PALETA = [((204, 41, 39), (122, 18, 18)), ((199, 70, 52), (110, 30, 22)), ((0, 104, 74), (0, 52, 37))]
TIPO_COLOR = {"basico": (226, 232, 240), "esquinero": (253, 222, 214), "isla": (204, 236, 221)}


def fuente(tamano: int, negrita: bool = True) -> ImageFont.FreeTypeFont:
    nombre = "DejaVuSans-Bold.ttf" if negrita else "DejaVuSans.ttf"
    for carpeta in ("/usr/share/fonts/truetype/dejavu", "C:/Windows/Fonts"):
        ruta = Path(carpeta) / nombre
        if ruta.exists():
            return ImageFont.truetype(str(ruta), tamano)
    for alternativa in ("segoeuib.ttf" if negrita else "segoeui.ttf", "arialbd.ttf" if negrita else "arial.ttf"):
        ruta = Path("C:/Windows/Fonts") / alternativa
        if ruta.exists():
            return ImageFont.truetype(str(ruta), tamano)
    return ImageFont.load_default(tamano)


def degradado(ancho: int, alto: int, inicio: tuple, fin: tuple) -> Image.Image:
    imagen = Image.new("RGB", (ancho, alto))
    pixeles = imagen.load()
    for x in range(ancho):
        for y in range(0, alto, 1):
            t = (x / ancho) * 0.65 + (y / alto) * 0.35
            pixeles[x, y] = tuple(int(inicio[c] + (fin[c] - inicio[c]) * t) for c in range(3))
    return imagen


def portada_evento(i: int, evento: dict) -> Image.Image:
    inicio, fin = PALETA[(i - 1) % 3]
    imagen = degradado(1200, 630, inicio, fin)
    dibujo = ImageDraw.Draw(imagen, "RGBA")
    # Retícula de stands del recinto como motivo
    for fila in range(6):
        for col in range(9):
            x, y = 640 + col * 62, 70 + fila * 82
            dibujo.rounded_rectangle((x, y, x + 50, y + 66), 8, outline=(255, 255, 255, 60), width=2,
                                     fill=(255, 255, 255, 22 if (fila + col + i) % 4 else 70))
    dibujo.rectangle((0, 600, 1200, 630), fill=(0, 0, 0, 40))
    for k, color in enumerate(((204, 41, 39), (199, 70, 52), (0, 104, 74))):
        dibujo.rectangle((k * 400, 622, (k + 1) * 400, 630), fill=color)
    dibujo.text((72, 80), "EXPONEXO", font=fuente(30), fill=(255, 255, 255, 210))
    titulo = evento["nombre"].replace("ExpoNexo ", "")
    dibujo.text((72, 250), titulo, font=fuente(68), fill=(255, 255, 255))
    dibujo.text((72, 345), evento["descripcion"], font=fuente(28, False), fill=(255, 255, 255, 220))
    fechas = f"{evento['inicio'][:10]}  →  {evento['fin'][:10]}"
    dibujo.text((72, 470), fechas, font=fuente(26), fill=(255, 255, 255, 230))
    return imagen


def logo_empresa(i: int, empresa: dict) -> Image.Image:
    inicio, fin = PALETA[(i - 1) % 3]
    imagen = degradado(256, 256, inicio, fin)
    mascara = Image.new("L", (256, 256), 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, 255, 255), 48, fill=255)
    lienzo = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    lienzo.paste(imagen, (0, 0), mascara)
    palabras = [p for p in empresa["razon_social"].replace("S.A.S.", "").replace("Ltda", "").split() if p[0].isupper()]
    iniciales = "".join(p[0] for p in palabras[:2]) or empresa["razon_social"][:2]
    dibujo = ImageDraw.Draw(lienzo)
    letra = fuente(104)
    caja = dibujo.textbbox((0, 0), iniciales, font=letra)
    dibujo.text(((256 - (caja[2] - caja[0])) / 2 - caja[0], (256 - (caja[3] - caja[1])) / 2 - caja[1]),
                iniciales, font=letra, fill=(255, 255, 255))
    return lienzo


def plano_pabellon(pabellon: dict, stands: list[dict]) -> Image.Image:
    imagen = Image.new("RGB", (1200, 720), (248, 250, 252))
    dibujo = ImageDraw.Draw(imagen)
    dibujo.rectangle((0, 0, 1200, 8), fill=(204, 41, 39))
    dibujo.text((60, 40), pabellon["nombre"], font=fuente(40), fill=(17, 24, 39))
    dibujo.text((60, 96), "Plano de stands · 3 filas × 4 columnas", font=fuente(22, False), fill=(75, 85, 99))
    for s in stands:
        x = 60 + (s["columna"] - 1) * 270
        y = 170 + (s["fila"] - 1) * 170
        dibujo.rounded_rectangle((x, y, x + 245, y + 145), 14, fill=TIPO_COLOR[s["tipo"]], outline=(203, 213, 225), width=2)
        dibujo.text((x + 18, y + 16), s["codigo"], font=fuente(30), fill=(17, 24, 39))
        dibujo.text((x + 18, y + 64), f"{s['tipo']} · {s['metros_cuadrados']} m²", font=fuente(20, False), fill=(55, 65, 81))
        dibujo.text((x + 18, y + 98), f"$ {int(s['precio_base']):,}".replace(",", "."), font=fuente(22), fill=(55, 65, 81))
    leyenda = [("Básico", "basico"), ("Esquinero", "esquinero"), ("Isla", "isla")]
    for k, (texto, tipo) in enumerate(leyenda):
        x = 60 + k * 200
        dibujo.rounded_rectangle((x, 680, x + 22, 702), 4, fill=TIPO_COLOR[tipo], outline=(148, 163, 184))
        dibujo.text((x + 32, 680), texto, font=fuente(20, False), fill=(55, 65, 81))
    return imagen


def generar_todo() -> list[tuple[str, Path, str, str]]:
    """Devuelve (nombre en la nube, archivo, tabla, id) de cada imagen generada."""
    SALIDA.mkdir(exist_ok=True)
    piezas = []
    for i, evento in enumerate(generar.eventos, 1):
        archivo = SALIDA / f"evento-{evento['slug']}.png"
        portada_evento(i, evento).save(archivo, optimize=True)
        piezas.append((f"evento-{evento['slug']}", archivo, "eventos", evento["id"]))
    for i, empresa in enumerate(generar.empresas, 1):
        archivo = SALIDA / f"empresa-{i:02d}.png"
        logo_empresa(i, empresa).save(archivo, optimize=True)
        piezas.append((f"empresa-{i:02d}", archivo, "empresas", empresa["id"]))
    for p, pabellon in enumerate(generar.pabellones, 1):
        archivo = SALIDA / f"pabellon-{p}.png"
        propios = [s for s in generar.stands if s["pabellon_id"] == pabellon["id"]]
        plano_pabellon(pabellon, propios).save(archivo, optimize=True)
        piezas.append((f"pabellon-{p}", archivo, "pabellones", pabellon["id"]))
    print(f"Imágenes generadas: {len(piezas)}")
    return piezas


def subir(nombre: str, archivo: Path) -> None:
    nube, llave, secreto = (os.environ[k] for k in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"))
    parametros = {"overwrite": "true", "public_id": f"{CARPETA_NUBE}/{nombre}", "timestamp": str(int(time.time()))}
    firma = hashlib.sha1(("&".join(f"{k}={v}" for k, v in sorted(parametros.items())) + secreto).encode()).hexdigest()
    limite = uuid.uuid4().hex
    partes = []
    for clave, valor in {**parametros, "api_key": llave, "signature": firma}.items():
        partes.append(f'--{limite}\r\nContent-Disposition: form-data; name="{clave}"\r\n\r\n{valor}\r\n'.encode())
    partes.append(f'--{limite}\r\nContent-Disposition: form-data; name="file"; filename="{archivo.name}"\r\n'
                  f"Content-Type: image/png\r\n\r\n".encode() + archivo.read_bytes() + b"\r\n")
    partes.append(f"--{limite}--\r\n".encode())
    pedido = urllib.request.Request(f"https://api.cloudinary.com/v1_1/{nube}/image/upload", data=b"".join(partes),
                                    headers={"Content-Type": f"multipart/form-data; boundary={limite}"})
    with urllib.request.urlopen(pedido, timeout=60) as respuesta:
        json.load(respuesta)


def main() -> None:
    piezas = generar_todo()
    if "--subir" not in sys.argv:
        return
    nube = os.environ["CLOUDINARY_CLOUD_NAME"]
    columna = {"eventos": "imagen_url", "empresas": "logo_url", "pabellones": "plano_url"}
    sentencias = []
    for nombre, archivo, tabla, ident in piezas:
        subir(nombre, archivo)
        url = f"https://res.cloudinary.com/{nube}/image/upload/f_auto,q_auto/{CARPETA_NUBE}/{nombre}"
        sentencias.append(f"UPDATE dbo.{tabla} SET {columna[tabla]} = '{url}' WHERE id = '{ident}';")
    Path(sys.argv[sys.argv.index("--subir") + 1]).write_text("\nGO\n".join(sentencias) + "\nGO\n", encoding="utf-8")
    print(f"Imágenes subidas a Cloudinary: {len(piezas)}")


if __name__ == "__main__":
    main()
