"""Genera docs/arquitectura.svg (mismo estilo de los diagramas del portafolio: lienzo oscuro,
zonas punteadas por nube coloreadas por plataforma, tarjetas con sombra y flechas curvas).
Uso: python docs/arquitectura.py
"""
from pathlib import Path

ANCHO, ALTO = 1480, 940
partes: list[str] = []


def zona(x, y, w, h, color, titulo, nota=""):
    ancho_etiqueta = 14 + len(titulo) * 7.2
    partes.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="24" fill="{color}" fill-opacity=".07" stroke="{color}" '
        f'stroke-opacity=".6" stroke-width="1.6" stroke-dasharray="7 6"/>'
        f'<rect x="{x + 18}" y="{y - 12}" width="{ancho_etiqueta:.1f}" height="24" rx="12" fill="{color}"/>'
        f'<text x="{x + 18 + ancho_etiqueta / 2:.1f}" y="{y + 4}" text-anchor="middle" font-size="11.5" font-weight="700" fill="#FFFFFF">{titulo}</text>'
    )
    if nota:
        partes.append(f'<text x="{x + w - 16}" y="{y + h - 12}" text-anchor="end" font-size="10.5" fill="{color}" fill-opacity=".95">{nota}</text>')


def tarjeta(cx, cy, color, titulo, sub, w=210, h=66):
    x, y = cx - w / 2, cy - h / 2
    partes.append(
        f'<g filter="url(#sh)"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#111C30" stroke="{color}" '
        f'stroke-opacity=".85" stroke-width="1.6"/><rect x="{x}" y="{y + 12}" width="4" height="{h - 24}" rx="2" fill="{color}"/></g>'
        f'<text x="{cx}" y="{cy - 3}" text-anchor="middle" font-size="13" font-weight="700" fill="#F1F5F9">{titulo}</text>'
        f'<text x="{cx}" y="{cy + 15}" text-anchor="middle" font-size="10.8" fill="#94A3B8">{sub}</text>'
    )


def curva(d, etiqueta="", ex=0, ey=0):
    partes.append(f'<path d="{d}" fill="none" stroke="#7C8BA1" stroke-width="2.2" stroke-opacity=".9" marker-end="url(#arrow)" stroke-dasharray="6 5"/>')
    if etiqueta:
        w = 12 + len(etiqueta) * 6.1
        partes.append(
            f'<rect x="{ex - w / 2:.1f}" y="{ey - 10}" width="{w:.1f}" height="20" rx="10" fill="#0F172A" stroke="#334155"/>'
            f'<text x="{ex}" y="{ey + 4}" text-anchor="middle" font-size="10.5" fill="#CBD5E1">{etiqueta}</text>'
        )


def flecha(x1, y1, x2, y2, etiqueta="", color="#7C8BA1", discontinua=False):
    mx = (x1 + x2) / 2
    trazo = ' stroke-dasharray="6 5"' if discontinua else ""
    partes.append(
        f'<path d="M{x1},{y1} C{mx},{y1} {mx},{y2} {x2},{y2}" fill="none" stroke="{color}" stroke-width="2.2" '
        f'stroke-opacity=".9" marker-end="url(#arrow)"{trazo}/>'
    )
    if etiqueta:
        ex, ey = mx, (y1 + y2) / 2
        w = 12 + len(etiqueta) * 6.1
        partes.append(
            f'<rect x="{ex - w / 2:.1f}" y="{ey - 10}" width="{w:.1f}" height="20" rx="10" fill="#0F172A" stroke="#334155"/>'
            f'<text x="{ex}" y="{ey + 4}" text-anchor="middle" font-size="10.5" fill="#CBD5E1">{etiqueta}</text>'
        )


VERCEL, AZURE, GCP, AWS, OCI, MONGO, CLOUD, GITHUB = "#6B7280", "#0078D4", "#4285F4", "#FF9900", "#C74634", "#13AA52", "#3448C5", "#8B5CF6"

# Zonas por plataforma
zona(40, 330, 250, 160, VERCEL, "Vercel", "PWA instalable")
zona(380, 110, 430, 330, AZURE, "Microsoft Azure", "escala a cero")
zona(380, 520, 430, 180, GCP, "Google Cloud Run", "escala a cero")
zona(900, 110, 260, 160, AZURE, "Azure SQL")
zona(900, 330, 260, 160, MONGO, "MongoDB Atlas")
zona(900, 550, 260, 160, OCI, "Oracle Cloud (OCI)")
zona(1230, 110, 210, 600, AWS, "AWS", "eventos")
zona(40, 760, 1400, 100, GITHUB, "GitHub Actions", "despliegue con OIDC · depuración cada 15 días")

# Componentes
tarjeta(165, 410, VERCEL, "Portal React", "visitantes · expositores · personal")
tarjeta(595, 200, AZURE, "Identidad y reservas", "FastAPI · MFA · JWT · agenda")
tarjeta(595, 350, AZURE, "Mesa de ayuda", "ASP.NET Core · SLA · dispositivos")
tarjeta(595, 610, GCP, "Pagos", "Spring Boot · QR · facturas")
tarjeta(1030, 190, AZURE, "SQL Server", "procedimientos almacenados", w=200)
tarjeta(1030, 410, MONGO, "MongoDB", "tickets · lecturas", w=200)
tarjeta(1030, 630, OCI, "Oracle Autonomous", "paquete PL/SQL", w=200)
tarjeta(1335, 200, AWS, "Tema SNS", "exponexo-eventos", w=170)
tarjeta(1335, 360, AWS, "Lambda repartidor", "SQS → rutas internas", w=170)
tarjeta(1335, 520, AWS, "Lambda avisos", "Brevo · Telegram", w=170)
tarjeta(1335, 660, CLOUD, "Cloudinary", "imágenes", w=170)
tarjeta(300, 810, GITHUB, "CI/CD", "pruebas · despliegue", w=220, h=56)
tarjeta(740, 810, GITHUB, "qa-evidencia", "E2E diario con capturas", w=220, h=56)
tarjeta(1180, 810, GITHUB, "portafolio-status", "salud a horas fijas", w=220, h=56)

# Flujos
flecha(270, 400, 488, 200, "JWT")
flecha(270, 415, 488, 350)
flecha(270, 425, 488, 605)
flecha(700, 195, 928, 190, "SQL")
flecha(700, 355, 928, 410)
flecha(700, 615, 928, 630, "JDBC · mTLS")
curva("M595,167 C595,20 1335,20 1335,167", "bandeja de salida → SNS (eventos)", 965, 57)
flecha(1335, 233, 1335, 325)
curva("M1420,200 C1462,200 1462,520 1420,520")

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ANCHO} {ALTO}" width="{ANCHO}" height="{ALTO}" font-family="Segoe UI, -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif" role="img" aria-label="Arquitectura de ExpoNexo">
<defs>
  <radialGradient id="bg" cx="50%" cy="45%" r="75%"><stop offset="0" stop-color="#16233F"/><stop offset="1" stop-color="#0A1020"/></radialGradient>
  <filter id="sh" x="-30%" y="-30%" width="160%" height="170%"><feDropShadow dx="0" dy="4" stdDeviation="5" flood-color="#000" flood-opacity=".45"/></filter>
  <marker id="arrow" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#7C8BA1"/></marker>
</defs>
<rect width="{ANCHO}" height="{ALTO}" rx="26" fill="url(#bg)"/>
<text x="36" y="46" font-size="21" font-weight="800" fill="#F8FAFC">ExpoNexo</text>
<text x="36" y="70" font-size="12.5" fill="#94A3B8">Recinto de ferias: cuatro servicios con su propia base, avisándose por eventos, en cinco nubes y planes gratuitos</text>
<g transform="translate(0,40)">
{chr(10).join(partes)}
</g>
</svg>
'''
(Path(__file__).parent / "arquitectura.svg").write_text(svg, encoding="utf-8")
print("docs/arquitectura.svg generado")
