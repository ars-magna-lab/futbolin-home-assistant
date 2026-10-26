#!/usr/bin/env python3
"""Genera los diagramas SVG de la documentación (docs/img/).

    python3 docs/img/diagramas.py

Los colores usan variables CSS con valor por defecto: en la web (SVG en línea)
siguen el tema claro/oscuro de la página; en GitHub o en un visor se ven con el
color por defecto. Las gráficas del piezo son ILUSTRATIVAS: modelos físicos
aproximados, no medidas.
"""

import math
import pathlib
import random

DIR = pathlib.Path(__file__).resolve().parent

ESTILO = """<style>
.t{fill:var(--tinta,#1d1d1b);font:13px system-ui,sans-serif}
.ts{fill:var(--suave,#6b6a65);font:12px system-ui,sans-serif}
.tc{text-anchor:middle}
.te{text-anchor:end}
.tb{font-weight:600}
.l{stroke:var(--tinta,#1d1d1b);stroke-width:1.5;fill:none}
.ls{stroke:var(--suave,#6b6a65);stroke-width:1;fill:none}
.lg{stroke:var(--linea,#e3e1db);stroke-width:1;fill:none}
.caja{fill:var(--papel,#fff);stroke:var(--suave,#6b6a65);stroke-width:1.2}
.zona{fill:var(--chip,#efede8);stroke:var(--linea,#e3e1db)}
.punteada{stroke-dasharray:5 4}
.madera{fill:var(--madera,#c9a77c);stroke:var(--madera-borde,#9c7a50)}
.bola{fill:var(--bola,#ecebe6);stroke:var(--tinta,#1d1d1b);stroke-width:1.5}
.rojo{fill:var(--rojo,#c0392b)}
.srojo{stroke:var(--rojo,#c0392b);stroke-width:2;fill:none}
.s1{stroke:var(--serie1,#2563a8);stroke-width:2;fill:none}
.f1{fill:var(--serie1,#2563a8)}
.s2{stroke:var(--serie2,#b8860b);stroke-width:2;fill:none}
.f2{fill:var(--serie2,#b8860b)}
.sombra1{fill:var(--serie1,#2563a8);opacity:.12}
.sombra2{fill:var(--serie2,#b8860b);opacity:.15}
.sombrar{fill:var(--rojo,#c0392b);opacity:.12}
</style>"""


def svg(nombre: str, ancho: int, alto: int, titulo: str, cuerpo: str) -> None:
    # Cada SVG lleva su propio marcador de flecha con id único (van todos en la misma página)
    flecha = (f'<defs><marker id="fl-{nombre}" viewBox="0 0 10 10" refX="9" refY="5" '
              f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
              f'<path d="M0,0 L10,5 L0,10 z" style="fill:var(--tinta,#1d1d1b)"/></marker></defs>')
    contenido = cuerpo.replace("FLECHA2", f'marker-start="url(#fl-{nombre})"')
    contenido = contenido.replace("FLECHA", f'marker-end="url(#fl-{nombre})"')
    texto = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" '
             f'width="{ancho}" height="{alto}" role="img" aria-label="{titulo}">'
             f'<title>{titulo}</title>{ESTILO}{flecha}{contenido}</svg>\n')
    (DIR / f"{nombre}.svg").write_text(texto, encoding="utf-8")


def caja(x, y, w, h, lineas, clase="caja", negrita_primera=True):
    """Rectángulo redondeado con varias líneas de texto centradas."""
    s = f'<rect class="{clase}" x="{x}" y="{y}" width="{w}" height="{h}" rx="6"/>'
    alto_linea = 15
    y0 = y + h / 2 - (len(lineas) - 1) * alto_linea / 2 + 4
    for i, linea in enumerate(lineas):
        c = "t tc tb" if (i == 0 and negrita_primera) else ("t tc" if i == 0 else "ts tc")
        s += f'<text class="{c}" x="{x + w / 2}" y="{y0 + i * alto_linea}">{linea}</text>'
    return s


def flecha(x1, y1, x2, y2, clase="l", extra=""):
    return f'<line class="{clase}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" FLECHA {extra}/>'


def polilinea(puntos, clase):
    d = " ".join(f"{x:.1f},{y:.1f}" for x, y in puntos)
    return f'<polyline class="{clase}" points="{d}"/>'


# ---------------------------------------------------------------- arquitectura
def arquitectura():
    c = ""
    c += '<rect class="zona" x="10" y="10" width="430" height="340" rx="10"/>'
    c += '<text class="t tb" x="26" y="34">Futbolín · a batería, todo oculto</text>'
    c += '<rect class="zona" x="500" y="10" width="250" height="340" rx="10"/>'
    c += '<text class="t tb" x="516" y="34">Casa</text>'

    c += caja(30, 150, 170, 40, ["Barreras IR", "una por carril"])
    c += flecha(200, 170, 248, 195)
    c += caja(30, 205, 170, 40, ["Piezo del fondo", "futuro (velocidad)"], clase="caja punteada")
    c += '<line class="l punteada" x1="200" y1="225" x2="248" y2="215" FLECHA/>'

    c += caja(250, 50, 170, 50, ["Baterías 12 V", "2 × plomo 7 Ah · interruptor"])
    c += flecha(335, 100, 335, 168)
    c += '<text class="ts" x="342" y="138">buck 12→5 V</text>'
    c += caja(250, 170, 170, 70, ["ESP32 · ESPHome", "lleva la partida", "cuenta aunque caiga HA"])
    c += '<line class="l punteada" x1="335" y1="240" x2="335" y2="278" FLECHA/>'
    c += '<text class="ts" x="342" y="264">presets (WiFi local)</text>'
    c += caja(250, 280, 170, 44, ["Gledopto · WLED", "controlador de tiras"])
    c += flecha(250, 302, 202, 302)
    c += caja(30, 280, 170, 44, ["Tiras LED actuales", "2 × 28 píxeles, 12 V"])

    c += caja(520, 60, 210, 120, ["Home Assistant", "entidades ESPHome y WLED",
                                   "dashboard del marcador", "Assist (voz)", "automatizaciones"])
    c += '<line class="l punteada" x1="422" y1="195" x2="518" y2="140" FLECHA FLECHA2/>'
    c += '<text class="ts tc" x="462" y="152">API ESPHome</text>'
    c += '<line class="l punteada" x1="422" y1="295" x2="518" y2="170" FLECHA FLECHA2/>'
    c += '<text class="ts tc" x="488" y="262">WLED</text>'
    c += '<text class="t tc tb" x="470" y="345">WiFi</text>'
    c += '<line class="l" x1="625" y1="182" x2="625" y2="238" FLECHA FLECHA2/>'
    c += caja(520, 240, 210, 70, ["Tablet", "marcador en grande", "mando por voz"])
    svg("arquitectura", 760, 360, "Arquitectura: futbolín a batería con ESPHome y WLED, controlado desde Home Assistant", c)


# ---------------------------------------------------------------- secuencia de un gol
def secuencia():
    pasos = [
        (["1. Disparo"], "t = 0"),
        (["2. Choca con", "el fondo", "(piezo: fuerza)"], "+ ms"),
        (["3. Cae por la", "ranura al", "carril"], "décimas de s"),
        (["4. Rueda y", "tapa la", "barrera IR"], "≈ 35 ms tapada"),
        (["5. ESP32: suma,", "decide la fase,", "preset en WLED"], "&lt; 0,1 s"),
        (["6. HA: marcador", "en la tablet", "y avisos"], "&lt; 0,5 s"),
    ]
    c = ""
    w, gap, x = 112, 16, 4
    for i, (lineas, tiempo) in enumerate(pasos):
        clase = "caja punteada" if i == 1 else "caja"
        c += caja(x, 20, w, 80, lineas, clase=clase)
        c += f'<text class="ts tc" x="{x + w / 2}" y="122">{tiempo}</text>'
        if i < len(pasos) - 1:
            c += flecha(x + w + 1, 60, x + w + gap - 1, 60)
        x += w + gap
    c += '<rect class="sombra2" x="4" y="136" width="368" height="26" rx="4"/>'
    c += '<text class="ts tc" x="188" y="154">dentro de la portería y el mueble</text>'
    c += '<rect class="sombra1" x="388" y="136" width="368" height="26" rx="4"/>'
    c += '<text class="ts tc" x="572" y="154">electrónica y red: casi instantáneo</text>'
    svg("secuencia-gol", 760, 170, "Recorrido de un gol desde el disparo hasta la tablet", c)


# ---------------------------------------------------------------- barrera IR
def barrera():
    c = '<text class="t tb" x="40" y="24">Corte del carril, visto de frente</text>'
    # paredes y suelo del carril
    c += '<rect class="madera" x="40" y="50" width="40" height="160"/>'
    c += '<rect class="madera" x="220" y="50" width="40" height="160"/>'
    c += '<rect class="madera" x="40" y="210" width="220" height="22"/>'
    # taladros y componentes retranqueados
    c += '<rect style="fill:var(--papel,#fff)" x="40" y="153" width="40" height="14"/>'
    c += '<rect style="fill:var(--papel,#fff)" x="220" y="153" width="40" height="14"/>'
    c += '<rect class="rojo" x="44" y="154" width="28" height="12" rx="3"/>'
    c += '<rect style="fill:var(--tinta,#1d1d1b)" x="228" y="154" width="28" height="12" rx="3"/>'
    # haz: llega hasta la bola, detrás no hay luz
    c += '<line class="srojo punteada" x1="72" y1="160" x2="98" y2="160"/>'
    c += '<line class="ls punteada" x1="202" y1="160" x2="228" y2="160"/>'
    c += '<circle class="bola" cx="150" cy="156" r="54"/>'
    c += '<text class="ts tc" style="fill:#4a4944" x="150" y="152">bola maciza</text>'
    c += '<text class="ts tc" style="fill:#4a4944" x="150" y="168">≈ 3,5 cm</text>'
    c += '<text class="ts" x="20" y="252">emisor IR 940 nm</text>'
    c += '<text class="ts" x="20" y="268">(siempre encendido)</text>'
    c += '<text class="ts te" x="285" y="252">receptor</text>'
    c += '<text class="ts te" x="285" y="268">(fototransistor)</text>'
    c += '<line class="ls" x1="88" y1="84" x2="72" y2="152"/>'
    c += '<text class="ts" x="86" y="80">retranqueado 2–3 mm</text>'

    # señal del receptor (escala de tiempo deformada para que se vea el pulso)
    x0, alto, bajo, base = 340, 80, 160, 196
    c += '<text class="t tb" x="340" y="24">Señal en el GPIO 32 (receptor)</text>'
    c += f'<text class="ts te" x="{x0 - 6}" y="{alto + 4}">haz libre</text>'
    c += f'<text class="ts te" x="{x0 - 6}" y="{bajo + 4}">tapado</text>'
    c += f'<line class="lg" x1="{x0}" y1="{base}" x2="745" y2="{base}"/>'
    c += '<rect class="sombra1" x="438" y="54" width="200" height="132"/>'
    c += '<text class="ts" x="548" y="102">bloqueo 400 ms:</text>'
    c += '<text class="ts" x="548" y="116">otro corte aquí</text>'
    c += '<text class="ts" x="548" y="130">se ignora</text>'
    puntos = [(x0, alto), (418, alto), (418, bajo), (438, bajo), (438, alto),
              (540, alto), (540, bajo), (543, bajo), (543, alto), (745, alto)]
    c += polilinea(puntos, "s1")
    c += f'<text class="ts tc" x="428" y="{base + 18}">≈ 35 ms</text>'
    c += '<circle class="f2" cx="438" cy="80" r="5"/>'
    c += '<text class="t tb" x="438" y="48" text-anchor="middle">GOL</text>'
    c += '<text class="ts tc" x="541" y="178">ruido: descartado</text>'
    c += '<text class="ts" x="340" y="240">El ESP32 mide cuánto dura el corte por interrupción (resolución de µs).</text>'
    c += '<text class="ts" x="340" y="256">Corte &lt; 0,5 ms = ruido · tapado &gt; 2 s = aviso de atasco.</text>'
    c += '<text class="ts" x="340" y="272">Autotest al arrancar: apaga el emisor (GPIO 14) y espera ver «tapado».</text>'
    svg("barrera-ir", 760, 285, "Barrera IR en el carril y la señal que recibe el ESP32", c)


# ---------------------------------------------------------------- alimentación
def alimentacion():
    c = ""
    y, h = 108, 48
    c += caja(10, y, 240, h, ["2 × plomo 12 V 7 Ah en paralelo", "~7 h · se sacan para cargar"])
    c += flecha(250, y + 24, 268, y + 24)
    c += caja(270, y, 80, h, ["Fusible", "5 A"])
    c += flecha(350, y + 24, 368, y + 24)
    c += caja(370, y, 100, h, ["Interruptor", "general externo"])
    c += f'<line class="l" x1="470" y1="{y + 24}" x2="495" y2="{y + 24}"/>'
    c += '<line class="l" x1="495" y1="44" x2="495" y2="224"/>'
    c += '<text class="ts tc" x="495" y="248">bus 12 V</text>'
    ramas = [
        (20, ["Gledopto", "WLED"], ["Tiras ×2", "8–10 W"]),
        (108, ["Buck 12→5 V", "HW-319 a 5,0 V"], ["ESP32", "+ sensores · 1,5 W"]),
        (196, ["Divisor", "100k / 22k"], ["ADC GPIO 34", "% de batería"]),
    ]
    for yr, a, b in ramas:
        c += flecha(495, yr + 24, 518, yr + 24)
        c += caja(520, yr, 110, h, a)
        c += flecha(630, yr + 24, 643, yr + 24)
        c += caja(645, yr, 110, h, b)
    svg("alimentacion", 760, 260, "Esquema de alimentación del futbolín", c)


def clema(x, y, titulo):
    """Una clema de regleta: un tornillo a cada lado. Devuelve el SVG y los puntos de entrada izquierdo y derecho."""
    c = f'<rect class="caja" x="{x}" y="{y}" width="50" height="24" rx="3"/>'
    c += f'<line class="ls" x1="{x + 25}" y1="{y}" x2="{x + 25}" y2="{y + 24}"/>'
    for xt in (x + 12, x + 38):
        c += (f'<circle class="caja" cx="{xt}" cy="{y + 12}" r="6"/>'
              f'<line class="ls" x1="{xt - 4}" y1="{y + 12}" x2="{xt + 4}" y2="{y + 12}"/>')
    c += f'<text class="ts tc" x="{x + 25}" y="{y - 6}">{titulo}</text>'
    return c, (x, y + 12), (x + 50, y + 12)


def bateria(x, y, n):
    """Batería con los bornes a la derecha: + arriba y − abajo. Devuelve el SVG y la posición de los bornes."""
    c = f'<rect class="caja" x="{x}" y="{y}" width="120" height="80" rx="4"/>'
    c += f'<text class="t tb" x="{x + 12}" y="{y + 34}">Batería {n}</text>'
    c += f'<text class="ts" x="{x + 12}" y="{y + 52}">plomo 12 V 7 Ah</text>'
    mas, menos = (x + 126, y + 20), (x + 126, y + 60)
    c += f'<rect class="rojo" x="{x + 120}" y="{y + 14}" width="10" height="12"/>'
    c += f'<rect x="{x + 120}" y="{y + 54}" width="10" height="12" style="fill:var(--tinta,#1d1d1b)"/>'
    c += f'<text class="t tb" x="{x + 104}" y="{y + 25}">+</text><text class="t tb" x="{x + 104}" y="{y + 65}">−</text>'
    return c, mas, menos


def fusible(x, y):
    return (f'<rect class="caja" x="{x}" y="{y - 8}" width="40" height="16" rx="8"/>'
            f'<text class="ts tc" x="{x + 20}" y="{y + 4}">5 A</text>')


def alimentacion_cableado():
    c = ""
    negro = "l"
    rojo = "srojo"
    b1, mas1, menos1 = bateria(10, 40, 1)
    b2, mas2, menos2 = bateria(10, 230, 2)
    c += b1 + b2
    c1, c1i, c1d = clema(500, 68, "C1 · +12 V")
    c2, c2i, c2d = clema(500, 128, "C2 · +12 V")
    c3, c3i, c3d = clema(500, 290, "C3 · GND")
    c += c1 + c2 + c3
    # positivos: borne → fusible pegado al borne → los dos en la borna de entrada del interruptor
    for (bx, by), xv in ((mas1, 300), (mas2, 290)):
        c += f'<line class="{rojo}" x1="{bx}" y1="{by}" x2="160" y2="{by}"/>' + fusible(160, by)
        c += polilinea([(200, by), (xv, by), (xv, 172), (382, 172)], rojo)
    c += '<text class="ts" x="150" y="26">portafusibles a &lt;10 cm del borne</text>'
    c += '<text class="ts" x="10" y="222">faston en los bornes</text>'
    # negativos a la clema de GND
    c += polilinea([menos1, (235, menos1[1]), (235, c3i[1]), c3i], negro)
    c += polilinea([menos2, (220, menos2[1]), (220, c3i[1]), c3i], negro)
    # interruptor → C1, y puente de C1 a C2
    c += '<circle class="caja" cx="400" cy="172" r="18"/><circle class="caja" cx="400" cy="172" r="9"/>'
    c += '<circle style="fill:var(--tinta,#1d1d1b)" cx="382" cy="172" r="3"/><circle style="fill:var(--tinta,#1d1d1b)" cx="418" cy="172" r="3"/>'
    c += '<text class="ts tc" x="400" y="210">interruptor</text><text class="ts tc" x="400" y="224">(debajo del mueble)</text>'
    c += '<text class="ts tc" x="400" y="242">los dos + en la misma borna</text>'
    c += polilinea([(418, 172), (450, 172), (450, c1i[1]), c1i], rojo)
    c += polilinea([c1i, (480, c1i[1]), (480, c2i[1]), c2i], rojo)
    c += '<text class="ts" x="486" y="168">puente</text>'
    # cargas
    c += caja(640, 40, 115, 56, ["Gledopto", "entrada 12 V"])
    c += caja(640, 150, 115, 56, ["Buck HW-319", "IN+ · IN−"])
    c += caja(640, 260, 115, 56, ["Interfaz", "divisor de batería"])
    c += polilinea([c1d, (600, c1d[1]), (600, 56), (640, 56)], rojo)
    c += polilinea([c1d, (580, c1d[1]), (580, 166), (640, 166)], rojo)
    c += polilinea([c2d, (565, c2d[1]), (565, 276), (640, 276)], "s2")
    c += polilinea([c3d, (620, c3d[1]), (620, 84), (640, 84)], negro)
    c += polilinea([c3d, (605, c3d[1]), (605, 190), (640, 190)], negro)
    c += ('<text class="ts" x="10" y="362">Rojo: positivo (1 mm²). Negro: GND (1 mm²). Ámbar: 12 V al divisor (hilo fino). '
          'Como máximo dos cables por tornillo.</text>')
    c += ('<text class="ts" x="10" y="378">C2 queda con un lado libre para el medidor de potencia o ampliaciones. '
          'Los cables de las dos baterías, con la misma longitud.</text>')
    svg("alimentacion-cableado", 760, 390, "Cableado de la alimentación con la regleta", c)


def alimentacion_montaje():
    """Vista en planta, aproximadamente a escala (1 mm ≈ 1,2 px)."""
    c = '<text class="t tb" x="10" y="22">Vista desde arriba, con el tablero abierto</text>'
    # listón de tope detrás de las baterías
    c += '<rect class="madera" x="20" y="44" width="186" height="10"/>'
    c += '<text class="ts" x="20" y="38">listón de tope</text>'
    for i, x in enumerate((24, 112)):
        c += f'<rect class="caja" x="{x}" y="56" width="78" height="181" rx="3"/>'
        c += f'<text class="t tb tc" x="{x + 39}" y="160">Bat. {i + 1}</text>'
        c += f'<rect class="rojo" x="{x + 52}" y="64" width="12" height="8"/>'
        c += f'<rect x="{x + 14}" y="64" width="12" height="8" style="fill:var(--tinta,#1d1d1b)"/>'
    c += '<text class="ts tc" x="113" y="256">151 × 65 mm cada una, de pie</text>'
    # correa
    c += '<rect x="16" y="190" width="190" height="10" class="sombra2"/>'
    c += '<text class="ts" x="20" y="274">franja ámbar: correa de velcro</text>'
    # panel
    c += '<rect class="madera" x="246" y="56" width="300" height="181" rx="3" style="opacity:.55"/>'
    c += '<text class="ts" x="420" y="256">panel de contrachapado ~25 × 15 cm</text>'
    c += '<line class="ls punteada" x1="396" y1="62" x2="396" y2="232"/>'
    c += '<text class="ts tc" x="320" y="76">zona 12 V</text><text class="ts tc" x="470" y="76">zona 5 V / 3,3 V</text>'
    c += '<rect class="caja" x="262" y="96" width="108" height="40" rx="3"/>'
    for i, txt in enumerate(("C1", "C2", "C3")):
        x = 262 + i * 36
        if i:
            c += f'<line class="ls" x1="{x}" y1="96" x2="{x}" y2="136"/>'
        c += f'<circle class="caja" cx="{x + 18}" cy="106" r="5"/><circle class="caja" cx="{x + 18}" cy="126" r="5"/>'
        c += f'<text class="ts tc" x="{x + 18}" y="152" style="font-size:10px">{txt}</text>'
    c += '<text class="ts tc" x="316" y="168">regleta: +12 · +12 · GND</text>'
    c += caja(258, 176, 112, 46, ["Buck", "12 → 5 V"])
    c += caja(406, 90, 130, 56, ["Interfaz", "3 clemas"], negrita_primera=False)
    c += caja(406, 160, 130, 66, ["ESP32", "antena → fuera"])
    # cables de las baterías al panel
    c += polilinea([(82, 64), (82, 48), (240, 48), (240, 242), (372, 242), (380, 262)], "srojo")
    c += polilinea([(170, 64), (170, 52), (232, 52), (232, 246), (370, 246), (378, 262)], "srojo")
    c += '<text class="ts" x="216" y="300">los + de las baterías, al interruptor;</text>'
    c += '<text class="ts" x="216" y="314">su vuelta, a la regleta</text>' 
    c += '<rect class="caja" x="96" y="42" width="22" height="10" rx="5"/><rect class="caja" x="184" y="46" width="22" height="10" rx="5"/>'
    c += '<text class="ts" x="250" y="40">fusibles junto al + de cada batería</text>'
    # salidas
    c += polilinea([(280, 96), (280, 62), (740, 62)], "srojo")
    c += '<text class="ts" x="606" y="54">al Gledopto y las tiras</text>'
    c += polilinea([(546, 120), (740, 120)], "s1")
    c += polilinea([(546, 130), (740, 130)], "s2")
    c += '<text class="ts" x="606" y="150">a los carriles Madrid y Barcelona</text>'
    c += '<text class="ts" x="606" y="164">(cables de 5 hilos)</text>'
    c += '<circle class="caja punteada" cx="380" cy="318" r="14"/>'
    c += polilinea([(380, 264), (380, 304)], "srojo punteada")
    c += '<text class="ts" x="402" y="322">interruptor, por debajo del mueble (taladro de 19 mm)</text>'
    svg("alimentacion-montaje", 760, 344, "Dónde va cada cosa: baterías y panel de electrónica", c)


def modo_enchufado():
    c = caja(10, 40, 130, 56, ["Fuente 12 V", "Mean Well GST36E12"])
    c += '<line class="l" x1="140" y1="68" x2="200" y2="68"/>'
    c += '<text class="ts tc" x="170" y="60">clavija</text>'
    c += caja(200, 44, 120, 48, ["Jack hembra", "5,5 × 2,1 mm"])
    c += polilinea([(320, 60), (420, 60)], "srojo")
    c += polilinea([(320, 76), (420, 116)], "l")
    c += '<text class="ts" x="330" y="52">centro +</text><text class="ts" x="336" y="112">masa</text>'
    for y, txt, cl in ((60, "faston", "rojo"), (116, "faston", "")):
        estilo = 'class="rojo"' if cl else 'style="fill:var(--tinta,#1d1d1b)"'
        c += f'<rect {estilo} x="420" y="{y - 6}" width="14" height="12" rx="2"/>'
    c += polilinea([(440, 60), (480, 60)], "srojo") + fusible(480, 60)
    c += polilinea([(520, 60), (600, 60)], "srojo")
    c += polilinea([(440, 116), (600, 116)], "l")
    c += caja(600, 36, 155, 104, ["Cables de la bat. 1", "(batería fuera)", "→ resto del montaje"])
    c += '<text class="ts" x="440" y="92">portafusibles del futbolín</text>'
    c += ('<text class="ts" x="10" y="170">Interruptor apagado para cambiar. Nunca fuente y baterías a la vez. '
          'En HA, activar Modo enchufado.</text>')
    svg("modo-enchufado", 760, 182, "Modo enchufado: la fuente en lugar de las baterías", c)


# ---------------------------------------------------------------- velocidad con dos haces
def haces():
    c = '<text class="t tb" x="40" y="22">Boca de la portería, vista desde arriba</text>'
    c += '<rect class="madera" x="40" y="40" width="20" height="190"/>'
    c += '<rect class="madera" x="340" y="40" width="20" height="190"/>'
    c += '<line class="ls punteada" x1="60" y1="44" x2="340" y2="44"/>'
    c += '<text class="ts tc" x="200" y="38">fondo (madera)</text>'
    c += '<text class="ts tc" x="200" y="250">campo</text>'
    # cono del emisor 1 (diafonía)
    c += '<polygon class="sombrar" points="60,160 340,121 340,199"/>'
    # haz 2 (emisor a la derecha) y haz 1 (emisor a la izquierda)
    c += '<rect class="rojo" x="334" y="114" width="8" height="12"/><line class="srojo" x1="334" y1="120" x2="66" y2="120"/>'
    c += '<rect style="fill:var(--tinta,#1d1d1b)" x="58" y="114" width="8" height="12"/>'
    c += '<rect class="rojo" x="58" y="154" width="8" height="12"/><line class="srojo" x1="66" y1="160" x2="334" y2="160"/>'
    c += '<rect style="fill:var(--tinta,#1d1d1b)" x="334" y="154" width="8" height="12"/>'
    c += '<text class="ts" x="70" y="114">haz 2 (emisor a la derecha)</text>'
    c += '<text class="ts" x="70" y="178">haz 1 (emisor a la izquierda)</text>'
    c += '<line class="l" x1="372" y1="120" x2="372" y2="160" FLECHA FLECHA2/>'
    c += '<text class="t" x="378" y="144">d</text>'
    c += '<circle class="bola" cx="230" cy="214" r="12"/>'
    c += '<line class="l" x1="230" y1="200" x2="230" y2="176" FLECHA/>'
    c += '<text class="ts" x="250" y="218">bola</text>'
    c += '<text class="ts tc" x="200" y="272">29 cm de ancho · cono del emisor (rojo claro): diafonía</text>'

    x0 = 420
    c += '<text class="t tb" x="420" y="22">Señales de los dos receptores</text>'
    for i, (yb, xc, etiqueta) in enumerate([(70, 500, "haz 1"), (140, 590, "haz 2")]):
        c += f'<text class="ts" x="{x0}" y="{yb - 14}">{etiqueta}</text>'
        c += polilinea([(x0, yb), (xc, yb), (xc, yb + 36), (xc + 14, yb + 36), (xc + 14, yb), (745, yb)], "s1")
    c += '<line class="ls punteada" x1="500" y1="60" x2="500" y2="190"/>'
    c += '<line class="ls punteada" x1="590" y1="130" x2="590" y2="190"/>'
    c += '<line class="l" x1="502" y1="186" x2="588" y2="186" FLECHA FLECHA2/>'
    c += '<text class="t tc" x="545" y="204">Δt</text>'
    c += '<text class="t tb" x="420" y="234">v = d / Δt</text>'
    c += '<text class="ts" x="420" y="252">Ej.: d = 40 mm a 100 km/h → Δt = 1,44 ms.</text>'
    c += '<text class="ts" x="420" y="268">Los módulos comerciales tardan 1–2 ms: no valen.</text>'
    svg("velocidad-haces", 760, 280, "Medida de velocidad con dos haces en la boca de la portería", c)


# ---------------------------------------------------------------- montaje del piezo
def piezo_montaje():
    c = '<text class="t tb" x="20" y="22">Corte lateral de la portería (propuesta)</text>'
    # campo y frontal
    c += '<line class="l" x1="20" y1="150" x2="380" y2="150"/>'
    c += '<text class="ts" x="30" y="170">campo</text>'
    c += '<rect class="madera" x="376" y="30" width="14" height="40"/>'
    c += '<text class="ts te" x="370" y="46">frontal</text>'
    # cavidad: techo, suelo, ranura y panel trasero
    c += '<line class="l" x1="390" y1="70" x2="520" y2="70"/>'
    c += '<line class="l" x1="380" y1="150" x2="465" y2="150"/>'
    c += '<text class="ts tc" x="487" y="168">ranura</text>'
    c += '<rect class="madera" x="520" y="40" width="16" height="170"/>'
    c += '<text class="ts" x="548" y="56">panel trasero</text>'
    c += '<text class="ts" x="548" y="72">(madera dura, encastrado)</text>'
    c += '<rect class="f2" x="536" y="96" width="6" height="28" rx="2"/>'
    c += '<text class="t tb" x="550" y="104">piezo Ø 27 mm</text>'
    c += '<text class="ts" x="550" y="120">pegado por fuera</text>'
    c += '<path class="s2" d="M542,110 C600,110 600,150 640,150"/>'
    c += caja(640, 132, 112, 40, ["ESP32", "pico → ADC"])
    # trayectoria de la bola
    c += '<circle class="bola" cx="150" cy="138" r="12"/>'
    c += '<line class="l punteada" x1="164" y1="134" x2="494" y2="110" FLECHA/>'
    c += '<text class="ts" x="210" y="112">disparo</text>'
    c += '<circle class="bola" cx="497" cy="110" r="12" style="opacity:.45"/>'
    c += '<path class="ls punteada" d="M494,124 C488,160 484,190 490,210"/>'
    # carril inclinado con la barrera IR
    c += '<polygon class="madera" points="440,214 740,262 740,276 440,228"/>'
    c += '<circle class="bola" cx="560" cy="222" r="11"/>'
    c += '<line class="srojo" x1="640" y1="222" x2="640" y2="252"/>'
    c += '<text class="ts" x="600" y="292">barrera IR: confirma el gol</text>'
    c += '<text class="ts" x="250" y="236">carril de recogida (bajo el tablero)</text>'
    svg("piezo-montaje", 760, 300, "Dónde iría el piezo: detrás del fondo de la portería", c)


# ---------------------------------------------------------------- circuito del piezo
def piezo_circuito():
    c = ""
    top, gnd = 60, 170
    c += f'<line class="l" x1="60" y1="{top}" x2="180" y2="{top}"/>'
    c += f'<line class="l" x1="230" y1="{top}" x2="270" y2="{top}"/>'
    c += f'<line class="l" x1="300" y1="{top}" x2="600" y2="{top}"/>'
    c += f'<line class="l" x1="60" y1="{gnd}" x2="500" y2="{gnd}"/>'
    # tierra
    c += f'<line class="l" x1="280" y1="{gnd}" x2="280" y2="{gnd + 10}"/>'
    c += f'<line class="l" x1="268" y1="{gnd + 10}" x2="292" y2="{gnd + 10}"/>'
    c += f'<line class="l" x1="273" y1="{gnd + 15}" x2="287" y2="{gnd + 15}"/>'
    c += f'<line class="l" x1="278" y1="{gnd + 20}" x2="282" y2="{gnd + 20}"/>'
    # piezo
    c += f'<line class="l" x1="60" y1="{top}" x2="60" y2="98"/><line class="l" x1="60" y1="132" x2="60" y2="{gnd}"/>'
    c += '<line class="l" x1="44" y1="98" x2="76" y2="98"/><line class="l" x1="44" y1="132" x2="76" y2="132"/>'
    c += '<rect class="f2" x="46" y="104" width="28" height="22" rx="2"/>'
    c += '<text class="t tb te" x="38" y="120">piezo</text>'

    def resistencia_v(x, etq, nota):
        s = f'<line class="l" x1="{x}" y1="{top}" x2="{x}" y2="95"/><line class="l" x1="{x}" y1="135" x2="{x}" y2="{gnd}"/>'
        s += f'<rect class="caja" x="{x - 7}" y="95" width="14" height="40"/>'
        s += f'<text class="t" x="{x + 12}" y="112">{etq}</text><text class="ts" x="{x + 12}" y="128">{nota}</text>'
        return s

    c += resistencia_v(120, "1 MΩ", "")
    # resistencia serie
    c += f'<rect class="caja" x="180" y="{top - 7}" width="50" height="14"/>'
    c += f'<text class="t tc" x="205" y="{top - 14}">10 kΩ</text>'
    # diodo
    c += f'<polygon style="fill:var(--tinta,#1d1d1b)" points="270,{top - 10} 270,{top + 10} 292,{top}"/>'
    c += f'<line class="l" x1="294" y1="{top - 11}" x2="294" y2="{top + 11}"/>'
    c += f'<text class="t tc" x="284" y="{top - 16}">BAT85</text>'
    # condensador
    c += f'<line class="l" x1="360" y1="{top}" x2="360" y2="110"/><line class="l" x1="360" y1="120" x2="360" y2="{gnd}"/>'
    c += '<line class="l" x1="346" y1="110" x2="374" y2="110"/><line class="l" x1="346" y1="120" x2="374" y2="120"/>'
    c += '<text class="t" x="380" y="119">100 nF</text>'
    c += resistencia_v(450, "1 MΩ", "")
    # zener
    c += f'<line class="l" x1="520" y1="{top}" x2="520" y2="102"/><line class="l" x1="520" y1="122" x2="520" y2="{gnd}"/>'
    c += '<polygon style="fill:var(--tinta,#1d1d1b)" points="510,122 530,122 520,104"/>'
    c += '<polyline class="l" points="506,100 510,102 530,102 534,104"/>'
    c += '<line class="l" x1="500" y1="170" x2="520" y2="170"/>'
    c += '<text class="t" x="536" y="119">zener 3,3 V</text>'
    c += '<circle style="fill:var(--tinta,#1d1d1b)" cx="360" cy="60" r="3"/><circle style="fill:var(--tinta,#1d1d1b)" cx="450" cy="60" r="3"/>'
    c += '<circle style="fill:var(--tinta,#1d1d1b)" cx="520" cy="60" r="3"/><circle style="fill:var(--tinta,#1d1d1b)" cx="120" cy="60" r="3"/>'
    c += caja(600, 40, 140, 40, ["GPIO 35", "ADC1, solo entrada"])
    # notas de función
    notas = [(60, "genera tensión"), (120, "descarga el piezo"), (205, "limita corriente"),
             (284, "solo deja subir"), (360, "guarda el pico"), (450, "lo vacía: τ = 0,1 s"),
             (530, "protege el ESP32")]
    for i, (x, t) in enumerate(notas):
        yy = 214 if i % 2 == 0 else 230
        c += f'<text class="ts tc" x="{x}" y="{yy}">{t}</text>'
    svg("piezo-circuito", 760, 240, "Detector de pico entre el piezo y el ESP32", c)


# ---------------------------------------------------------------- gráficas (ilustrativas)
class Grafica:
    """Ejes lineales sencillos dentro de un rectángulo."""

    def __init__(self, x, y, w, h, xmin, xmax, ymin, ymax):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.xmin, self.xmax, self.ymin, self.ymax = xmin, xmax, ymin, ymax

    def px(self, v):
        return self.x + (v - self.xmin) / (self.xmax - self.xmin) * self.w

    def py(self, v):
        return self.y + self.h - (v - self.ymin) / (self.ymax - self.ymin) * self.h

    def ejes(self, xticks, yticks, xetq, yetq, fmt_x=str, fmt_y=str):
        s = ""
        for v in yticks:
            s += f'<line class="lg" x1="{self.x}" y1="{self.py(v):.1f}" x2="{self.x + self.w}" y2="{self.py(v):.1f}"/>'
            s += f'<text class="ts te" x="{self.x - 6}" y="{self.py(v) + 4:.1f}">{fmt_y(v)}</text>'
        for v in xticks:
            s += f'<text class="ts tc" x="{self.px(v):.1f}" y="{self.y + self.h + 16}">{fmt_x(v)}</text>'
        s += f'<line class="ls" x1="{self.x}" y1="{self.y + self.h}" x2="{self.x + self.w}" y2="{self.y + self.h}"/>'
        s += f'<text class="ts tc" x="{self.x + self.w / 2}" y="{self.y + self.h + 34}">{xetq}</text>'
        s += f'<text class="ts" x="{self.x - 40}" y="{self.y - 10}">{yetq}</text>'
        return s

    def curva(self, f, a, b, n, clase):
        return polilinea([(self.px(a + (b - a) * i / n), self.py(f(a + (b - a) * i / n))) for i in range(n + 1)], clase)


def coma(v, dec=1):
    return f"{v:.{dec}f}".replace(".", ",")


def piezo_senal():
    g = Grafica(70, 40, 640, 180, 0, 30, -2.5, 3.5)
    c = g.ejes(range(0, 31, 5), [-2, -1, 0, 1, 2, 3], "tiempo desde el impacto (ms)", "tensión (V)",
               fmt_y=lambda v: str(v).replace("-", "−"))
    c += f'<line class="ls" x1="{g.x}" y1="{g.py(0):.1f}" x2="{g.x + g.w}" y2="{g.py(0):.1f}"/>'

    def bruta(t):  # oscilación amortiguada del disco tras el golpe
        return 0 if t < 2 else 3.2 * math.exp(-(t - 2) / 2.5) * math.sin(2 * math.pi * (t - 2) / 1.6)

    def pico(t):  # detector: sube con la primera cresta y se vacía con τ = 100 ms
        if t < 2.4:
            return max(0, bruta(t) - 0.3)
        return (3.2 * math.exp(-0.4 / 2.5) - 0.3) * math.exp(-(t - 2.4) / 100)

    c += g.curva(bruta, 0, 30, 900, "s2")
    c += g.curva(pico, 0, 30, 300, "s1")
    # lecturas del ADC cada milisegundo
    for t in range(3, 31, 3):
        c += f'<circle class="f1" cx="{g.px(t):.1f}" cy="{g.py(pico(t)):.1f}" r="4" style="stroke:var(--papel,#fff);stroke-width:2"><title>{t} ms: {coma(pico(t), 2)} V</title></circle>'
    c += f'<text class="t" x="{g.px(13)}" y="{g.py(2.85):.1f}">salida del detector de pico (lo que lee el ESP32)</text>'
    c += f'<text class="t" x="{g.px(7)}" y="{g.py(-1.2):.1f}">tensión del piezo: oscila y se apaga en pocos ms</text>'
    c += f'<text class="ts" x="{g.x}" y="275">Ilustrativo, no medido. Un golpe fuerte puede dar decenas de voltios en el piezo; el zener lo limita a 3,3 V.</text>'
    c += f'<text class="ts" x="{g.x}" y="291">El ESP32 no necesita ver la oscilación: lee el pico cada milisegundo (puntos) y se queda con el máximo.</text>'
    svg("piezo-senal", 760, 300, "Señal del piezo y salida del detector de pico (ilustrativo)", c)


def piezo_ventana():
    g = Grafica(70, 40, 640, 150, 0, 2, 0, 3.3)
    c = g.ejes([0, 0.5, 1, 1.5, 2], [0, 1, 2, 3], "tiempo (s)", "pico (V)", fmt_x=lambda v: coma(v))
    gol, ventana = 1.6, 1.0
    c += f'<rect class="sombra1" x="{g.px(gol - ventana):.1f}" y="{g.y}" width="{g.px(gol) - g.px(gol - ventana):.1f}" height="{g.h}"/>'
    c += f'<text class="ts tc" x="{g.px(gol - ventana / 2):.1f}" y="{g.y + 14}">ventana: 1 s antes del gol</text>'
    golpes = [(0.12, 0.5, "barra"), (0.3, 2.4, "golpe a la mesa"), (0.55, 0.4, "barra"), (0.85, 0.6, "barra"),
              (1.22, 2.0, "impacto en el fondo"), (1.4, 0.35, "barra"), (1.8, 0.7, "barra")]
    for t, v, que in golpes:
        elegido = que.startswith("impacto")
        clase = "f2" if elegido else "f1"
        c += f'<line class="{"s2" if elegido else "s1"}" x1="{g.px(t):.1f}" y1="{g.py(0):.1f}" x2="{g.px(t):.1f}" y2="{g.py(v):.1f}"/>'
        c += f'<circle class="{clase}" cx="{g.px(t):.1f}" cy="{g.py(v):.1f}" r="5" style="stroke:var(--papel,#fff);stroke-width:2"><title>{coma(t, 2)} s: {coma(v)} V ({que})</title></circle>'
    c += f'<text class="t" x="{g.px(0.32):.1f}" y="{g.py(2.55):.1f}">golpe fuerte a la mesa: fuera de la ventana, se ignora</text>'
    c += f'<text class="t tb" x="{g.px(1.24):.1f}" y="{g.py(2.15):.1f}">máximo en la ventana = impacto</text>'
    c += f'<line class="srojo" x1="{g.px(gol):.1f}" y1="{g.y}" x2="{g.px(gol):.1f}" y2="{g.y + g.h}"/>'
    c += f'<text class="t tb" x="{g.px(gol) + 6:.1f}" y="{g.y + 14}" style="fill:var(--rojo,#c0392b)">GOL (barrera IR)</text>'
    c += f'<text class="ts" x="{g.x}" y="252">Ilustrativo. El ancho real de la ventana es lo que tarda la bola del fondo a la barrera: hay que medirlo.</text>'
    svg("piezo-ventana", 760, 260, "Cómo se separa el impacto del gol de los golpes a la mesa", c)


def piezo_calibracion():
    g = Grafica(70, 40, 620, 200, 0, 120, 0, 3.3)
    c = g.ejes(range(0, 121, 20), [0, 1, 2, 3], "velocidad de la bola (km/h)", "pico (V)")
    k = 3.0 / 120 ** 1.2  # pico ∝ v^1,2 (contacto de Hertz), 3 V a 120 km/h

    def media(v):
        return k * v ** 1.2

    banda = [(g.px(v), g.py(media(v) * 1.25)) for v in range(0, 121, 4)]
    banda += [(g.px(v), g.py(media(v) * 0.75)) for v in range(120, -1, -4)]
    c += '<polygon class="sombra1" points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in banda) + '"/>'
    c += g.curva(media, 0, 120, 120, "s1")
    random.seed(7)
    for _ in range(28):
        v = random.uniform(15, 110)
        p = media(v) * random.uniform(0.78, 1.22)
        c += f'<circle class="f1" cx="{g.px(v):.1f}" cy="{g.py(p):.1f}" r="4" style="stroke:var(--papel,#fff);stroke-width:2;opacity:.8"><title>{coma(v, 0)} km/h → {coma(p, 2)} V</title></circle>'
    # lectura de ejemplo: 1,5 V → rango de velocidades
    p = 1.5
    vmin, vmax = (p / (k * 1.25)) ** (1 / 1.2), (p / (k * 0.75)) ** (1 / 1.2)
    c += f'<line class="s2 punteada" x1="{g.px(0)}" y1="{g.py(p):.1f}" x2="{g.px(vmax):.1f}" y2="{g.py(p):.1f}"/>'
    c += f'<rect class="sombra2" x="{g.px(vmin):.1f}" y="{g.y}" width="{g.px(vmax) - g.px(vmin):.1f}" height="{g.h}"/>'
    c += f'<text class="t" x="{g.px(vmax) + 6:.1f}" y="{g.py(p) - 8:.1f}">lectura de 1,5 V → entre {coma(vmin, 0)} y {coma(vmax, 0)} km/h</text>'
    c += f'<text class="t" x="{g.px(78)}" y="{g.py(3.15):.1f}">curva de calibración ± 25 %</text>'
    c += f'<text class="ts" x="{g.x}" y="300">Ilustrativo: puntos inventados para mostrar la idea. Cada punto real sería un disparo medido a cámara lenta con el móvil.</text>'
    svg("piezo-calibracion", 760, 310, "Calibración del piezo: pico frente a velocidad (ilustrativo)", c)


# ---------------------------------------------------------------- conexiones del ESP32
def banco_conexiones():
    c = ""
    pines = [("3V3", 60), ("GND", 90), ("5V / VIN", 120), ("GPIO 32", 160), ("GPIO 33", 210),
             ("GPIO 14 / 27", 300)]
    c += caja(20, 30, 170, 300, ["ESP32 DevKit"])
    for etq, y in pines:
        c += f'<text class="t te" x="182" y="{y + 4}">{etq}</text><circle style="fill:var(--tinta,#1d1d1b)" cx="190" cy="{y}" r="3"/>'
    # raíl de 3,3 V y GND
    c += '<line class="l" x1="190" y1="60" x2="205" y2="60"/><line class="l" x1="205" y1="60" x2="205" y2="24"/>'
    c += '<line class="l" x1="205" y1="24" x2="420" y2="24"/><text class="ts" x="214" y="18">3,3 V</text>'
    c += '<line class="l" x1="190" y1="90" x2="215" y2="90"/><line class="l" x1="215" y1="90" x2="215" y2="364"/>'
    c += '<line class="l" x1="215" y1="364" x2="745" y2="364"/><text class="ts" x="224" y="358">GND común</text>'

    def pullup(x, y):
        return (f'<line class="l" x1="{x}" y1="24" x2="{x}" y2="62"/>'
                f'<rect class="caja" x="{x - 7}" y="62" width="14" height="34"/>'
                f'<text class="ts" x="{x + 10}" y="84">5,1 kΩ</text>'
                f'<line class="l" x1="{x}" y1="96" x2="{x}" y2="{y}"/>'
                f'<circle style="fill:var(--tinta,#1d1d1b)" cx="{x}" cy="{y}" r="3"/>')

    c += '<line class="s1" x1="190" y1="160" x2="538" y2="160"/>' + pullup(330, 160)
    c += caja(540, 138, 205, 44, ["Receptor barrera A", "rojo 3,3 V · negro GND"])
    c += '<text class="ts" x="400" y="154">señal</text>'
    c += '<line class="s1" x1="190" y1="210" x2="538" y2="210"/>' + pullup(390, 210)
    c += caja(540, 188, 205, 44, ["Receptor barrera B", "rojo 3,3 V · negro GND"])
    # emisores alimentados directamente por su pin
    c += '<line class="l" x1="190" y1="300" x2="538" y2="300"/>'
    c += caja(540, 278, 205, 44, ["Emisores A y B", "rojo → GPIO 14 / 27 · negro GND"])
    c += '<text class="ts" x="230" y="294">un pin por emisor, ~10 mA a 3,3 V</text>'
    c += '<text class="ts" x="20" y="384">Alimentación por el USB del ordenador. Pull-ups a 3,3 V, nunca a 5 V.</text>'
    svg("banco-conexiones", 760, 392, "Banco de pruebas: conexiones en la protoboard", c)


# ---------------------------------------------------------------- cableado definitivo
def cableado_general():
    c = '<rect class="zona" x="380" y="128" width="375" height="270" rx="8"/>'
    c += '<text class="ts" x="525" y="146">Panel de electrónica (contrachapado)</text>'
    # baterías: + al fusible por arriba, − al raíl de GND por abajo
    for y, n in ((30, 1), (110, 2)):
        c += caja(10, y, 110, 48, [f"Batería {n}", "plomo 12 V 7 Ah"])
        c += f'<line class="srojo" x1="120" y1="{y + 14}" x2="150" y2="{y + 14}"/>'
        c += caja(150, y, 84, 30, ["Fusible 5 A"])
        c += f'<line class="l" x1="120" y1="{y + 38}" x2="135" y2="{y + 38}"/>'
        c += f'<polyline class="srojo" points="234,{y + 15} 300,{y + 15} 300,92 360,92"/>'
    c += '<text class="ts" x="150" y="174">faston · fusible a &lt;10 cm del borne</text>'
    c += '<text class="ts" x="150" y="155">los dos + a la misma borna</text>'
    c += caja(360, 70, 100, 44, ["Interruptor", "bajo el mueble"])
    c += '<line class="srojo" x1="410" y1="114" x2="410" y2="160"/>'
    c += caja(400, 160, 120, 54, ["Bus 12 V", "regleta de 3 clemas"])
    # GND de las baterías
    c += '<polyline class="l" points="135,68 135,252 430,252 430,214"/>'
    c += '<text class="ts" x="145" y="246">GND de las baterías (1 mm²)</text>'
    # salidas del bus
    c += '<polyline class="srojo" points="500,160 500,48 600,48"/>'
    c += caja(600, 20, 150, 56, ["Gledopto · WLED", "par 1 mm² · tiras a G D V"])
    c += '<text class="ts" x="508" y="40">par 1 mm²</text>'
    c += '<line class="srojo" x1="520" y1="182" x2="620" y2="182"/>'
    c += caja(620, 160, 130, 44, ["Buck 12→5 V", "HW-319 a 5,0 V"])
    c += '<line class="s2" x1="490" y1="214" x2="490" y2="280"/>'
    c += '<text class="ts" x="496" y="240">12 V al divisor</text>'
    c += '<line class="l" x1="685" y1="204" x2="685" y2="280"/><text class="ts" x="692" y="246">5 V y GND</text>'
    c += caja(395, 280, 200, 100, ["Interfaz", "pull-up y 1 kΩ soldadas al cable", "divisor 100k / 22k en línea",
                                   "3 clemas: 3,3 V y GND"])
    c += caja(620, 280, 130, 100, ["ESP32 DevKit", "placa de bornas", "antena hacia fuera"])
    c += '<line class="l" x1="595" y1="330" x2="620" y2="330"/><text class="ts tc" x="607" y="322">7</text>'
    # un cable de 5 hilos por carril, con dos JST-SM junto al carril
    for y, clase, carril in ((300, "s1", "Carril A · Real Madrid"), (350, "s2", "Carril B · Barcelona")):
        c += f'<line class="{clase}" x1="210" y1="{y + 20}" x2="395" y2="{y + 20}"/>'
        c += f'<rect class="caja" x="214" y="{y + 12}" width="22" height="16" rx="2"/>'
        c += caja(10, y, 200, 40, [carril, "receptor + emisor"])
    c += '<text class="ts" x="214" y="300">cable de 5 hilos, uno por carril</text>'
    c += '<text class="ts" x="214" y="406">↑ 2 × JST-SM junto al carril</text>'
    c += ('<text class="ts" x="10" y="430">Rojo: +12 V. Los cables de señal van separados ≥ 5 cm de los de 12 V; '
          'si se cruzan, en ángulo recto.</text>')
    svg("cableado-general", 760, 440, "Cableado definitivo del futbolín", c)


def placa_interfaz():
    c = caja(10, 30, 110, 290, ["ESP32"])
    pines = [("3V3", 60), ("GND", 100), ("GPIO 32", 150), ("GPIO 14", 210), ("GPIO 34", 290)]
    for etq, y in pines:
        c += f'<text class="t te" x="112" y="{y + 4}">{etq}</text><circle style="fill:var(--tinta,#1d1d1b)" cx="120" cy="{y}" r="3"/>'
    c += '<rect class="zona" x="150" y="20" width="290" height="330" rx="8"/>'
    c += '<text class="ts" x="160" y="38">Junto al ESP32: carril A (el B, igual con 33 y 27)</text>'
    punto = '<circle style="fill:var(--tinta,#1d1d1b)" cx="{}" cy="{}" r="3"/>'
    # raíles de 3,3 V y GND hacia el cable, repartidos en dos clemas
    c += '<line class="l" x1="120" y1="60" x2="540" y2="60"/>'
    c += '<line class="l" x1="120" y1="100" x2="540" y2="100"/>'
    for y, txt in ((60, "clema 3,3 V"), (100, "clema GND")):
        c += f'<rect class="caja" x="180" y="{y - 10}" width="24" height="20" rx="3"/><circle class="caja" cx="192" cy="{y}" r="5"/>'
        c += f'<line class="ls" x1="188" y1="{y}" x2="196" y2="{y}"/><text class="ts" x="170" y="{y + 24}">{txt}</text>'
    c += '<rect class="sombra2" x="240" y="48" width="170" height="114" rx="6"/>'
    c += '<text class="ts" x="250" y="176">soldadas en el cable</text>'
    # señal: pull-up de 5,1 kΩ en el lado del cable y 1 kΩ en serie hasta el GPIO
    c += '<line class="s1" x1="120" y1="150" x2="250" y2="150"/>'
    c += '<rect class="caja" x="250" y="143" width="44" height="14"/><text class="ts tc" x="272" y="138">1 kΩ</text>'
    c += '<line class="s1" x1="294" y1="150" x2="540" y2="150"/>'
    # salta por encima de la GND (semicírculo): no hay conexión en el cruce
    c += '<path class="l" d="M330,60 L330,92 A8,8 0 0 1 330,108 L330,112"/>' + punto.format(330, 60)
    c += '<rect class="caja" x="323" y="112" width="14" height="30"/><text class="ts" x="342" y="132">5,1 kΩ</text>'
    c += '<line class="l" x1="330" y1="142" x2="330" y2="150"/>' + punto.format(330, 150)
    # emisor: directo del pin
    c += '<line class="l" x1="120" y1="210" x2="540" y2="210"/>'
    c += '<text class="ts" x="160" y="204">emisor, directo a la borna (~10 mA)</text>'
    # segundo GND del cable (retorno del emisor)
    c += ('<path class="l" d="M420,100 L420,142 A8,8 0 0 1 420,158 L420,202 A8,8 0 0 1 420,218 '
          'L420,250 L540,250"/>') + punto.format(420, 100)
    # divisor de batería
    c += '<line class="s2" x1="120" y1="290" x2="340" y2="290"/>'
    c += '<rect class="caja" x="340" y="283" width="50" height="14"/><text class="ts tc" x="365" y="278">100 kΩ</text>'
    c += '<line class="s2" x1="390" y1="290" x2="430" y2="290"/><text class="ts" x="372" y="312">← 12 V (C2)</text>'
    c += '<line class="l" x1="260" y1="290" x2="260" y2="300"/>' + punto.format(260, 290)
    c += '<rect class="caja" x="253" y="300" width="14" height="22"/><text class="ts" x="196" y="316">22 kΩ</text>'
    c += '<line class="l" x1="260" y1="322" x2="260" y2="330"/>'
    c += '<line class="l" x1="250" y1="330" x2="270" y2="330"/><line class="l" x1="254" y1="335" x2="266" y2="335"/>'
    # cable de 5 hilos
    c += '<text class="t tb tc" x="495" y="38">5 hilos</text>'
    for h, y in (("H1", 60), ("H2", 100), ("H3", 150), ("H4", 210), ("H5", 250)):
        c += f'<text class="ts tc" x="495" y="{y - 6}">{h}</text>'
    # conectores JST-SM junto al carril
    c += '<rect class="caja" x="540" y="40" width="210" height="130" rx="6"/>'
    c += '<text class="t tb" x="552" y="30">JST receptor</text>'
    for y, txt in ((60, "1 · 3,3 V → rojo"), (100, "2 · GND → negro"), (150, "3 · señal → blanco")):
        c += punto.format(540, y) + f'<text class="t" x="552" y="{y + 4}">{txt}</text>'
    c += '<rect class="caja" x="540" y="190" width="210" height="110" rx="6"/>'
    c += '<text class="t tb" x="552" y="184">JST emisor</text>'
    for y, txt in ((210, "1 · emisor → rojo"), (250, "2 · GND → negro"), (285, "3 · libre")):
        c += (punto.format(540, y) if y < 285 else "") + f'<text class="t" x="552" y="{y + 4}">{txt}</text>'
    c += ('<text class="ts" x="10" y="374">GND siempre en el centro del conector. Si se cruzan los dos conectores '
          'de un carril no se rompe nada: el autotest falla.</text>')
    c += ('<text class="ts" x="10" y="390">Resistencias y divisor soldados en el cable, cada empalme con su termorretráctil '
          'y uno grueso por encima de todo.</text>')
    svg("placa-interfaz", 760, 400, "Interfaz junto al ESP32 y conectores de una barrera", c)


# ---------------------------------------------------------------- tiras
def tiras_conexion():
    c = ""
    c += caja(10, 96, 110, 50, ["Bus 12 V", "tras interruptor"])
    c += flecha(120, 121, 178, 121)
    c += '<line class="l" x1="150" y1="121" x2="150" y2="150"/><line class="l" x1="138" y1="150" x2="162" y2="150"/>'
    c += '<line class="l" x1="138" y1="157" x2="162" y2="157"/><line class="l" x1="150" y1="157" x2="150" y2="176"/>'
    c += '<text class="ts tc" x="150" y="192">1000 µF</text>'
    c += caja(180, 86, 150, 70, ["Gledopto · WLED", "2 salidas G D V", "GPIO 16 y GPIO 2"])
    c += '<polyline class="l" points="330,106 380,106 400,60 428,60" FLECHA/>'
    c += '<polyline class="l" points="330,136 380,136 400,182 428,182" FLECHA/>'
    c += '<text class="ts tc" x="352" y="98">salida 1</text><text class="ts tc" x="352" y="152">salida 2</text>'
    for y, lado in ((30, "Tira A · GPIO 16 · píxeles 0–27"), (152, "Tira B · GPIO 2 · píxeles 28–55")):
        c += f'<rect class="caja" x="430" y="{y}" width="320" height="60" rx="6"/>'
        c += f'<text class="t tb" x="444" y="{y + 20}">{lado}</text>'
        for i, (pad, x) in enumerate((("+12 V", 450), ("DI", 520), ("GND", 590))):
            c += f'<rect x="{x - 2}" y="{y + 32}" width="40" height="18" rx="3" style="fill:var(--chip,#efede8);stroke:var(--suave,#6b6a65)"/>'
            c += f'<text class="ts tc" x="{x + 18}" y="{y + 45}">{pad}</text>'
    c += '<text class="ts" x="10" y="232">Cada tira a su salida: dos segmentos en WLED, se manejan por separado.</text>'
    svg("tiras-conexion", 760, 242, "Conexión de las tiras al Gledopto", c)


# ---------------------------------------------------------------- máquina de estados
def maquina_estados():
    c = ""
    c += caja(10, 120, 110, 50, ["Reposo", "al encender"])
    c += caja(180, 120, 120, 50, ["Normal", "contando goles"])
    c += caja(370, 40, 150, 50, ["Bola de partido", "un equipo con 5"])
    c += caja(370, 200, 150, 50, ["LA BUENA", "5 – 5"], clase="caja")
    c += caja(600, 120, 150, 50, ["Fin", "ganador · ignora goles"])
    c += flecha(120, 145, 178, 145)
    c += '<text class="ts tc" x="149" y="137">nueva</text>'
    c += flecha(300, 135, 368, 70)
    c += '<text class="ts" x="300" y="92">alguien llega a 5</text>'
    c += flecha(445, 90, 445, 198)
    c += '<text class="ts" x="452" y="150">el otro llega a 5</text>'
    c += flecha(520, 65, 598, 132)
    c += '<text class="ts" x="560" y="86">6 goles</text>'
    c += flecha(520, 225, 598, 160)
    c += '<text class="ts" x="560" y="212">gol decisivo</text>'
    c += '<path class="l" d="M675,170 C675,290 240,290 240,172" FLECHA/>'
    c += '<text class="ts tc" x="460" y="285">nueva partida (desde HA)</text>'
    c += '<text class="ts" x="10" y="26">Correcciones (+1 / −1) recalculan el estado desde el marcador. «Anular» vuelve a Reposo.</text>'
    c += '<text class="ts" x="10" y="42">Cada cambio de estado activa su preset de WLED y se publica en HA.</text>'
    svg("maquina-estados", 760, 300, "Estados de la partida que lleva el ESP32", c)


# ---------------------------------------------------------------- embudo con cuñas en el carril
def carril_embudo():
    c = '<text class="t tb" x="20" y="22">Carril visto desde arriba: sensores detrás de dos cuñas en ángulo recto</text>'
    # paredes del carril
    c += '<rect class="madera" x="20" y="40" width="720" height="12"/>'
    c += '<rect class="madera" x="20" y="198" width="720" height="12"/>'
    c += '<text class="ts" x="30" y="232">paredes del carril (no se tocan)</text>'
    # cuñas en ángulo recto: rampa larga de entrada y cara recta a la salida
    c += '<polygon class="madera" points="300,52 450,80 450,52"/>'
    c += '<polygon class="madera" points="300,198 450,170 450,198"/>'
    # sensores pegados a la pared, en la sombra de la cara recta
    c += '<rect class="rojo" x="452" y="54" width="18" height="20" rx="2"/>'
    c += '<rect style="fill:var(--tinta,#1d1d1b)" x="452" y="176" width="18" height="20" rx="2"/>'
    c += '<line class="srojo punteada" x1="461" y1="74" x2="461" y2="176"/>'
    # bola
    c += '<circle class="bola" cx="190" cy="125" r="42"/>'
    c += '<line class="l" x1="240" y1="125" x2="300" y2="125" FLECHA/>'
    c += '<text class="ts tc" x="190" y="129">bola</text>'
    c += '<circle class="bola" cx="600" cy="125" r="42" style="opacity:.35"/>'
    # cotas y notas
    c += '<line class="l" x1="430" y1="82" x2="430" y2="168" FLECHA FLECHA2/>'
    c += '<text class="t" x="300" y="150">paso:</text>'
    c += '<text class="t" x="300" y="166">≥ bola + 3–5 mm</text>'
    c += '<text class="ts" x="300" y="100">rampa suave</text>'
    c += '<text class="ts" x="300" y="114">(≤ 25–30°)</text>'
    c += '<text class="ts" x="480" y="34">emisor pegado a la pared, tras la cara recta</text>'
    c += '<text class="ts" x="480" y="232">receptor enfrente, igual</text>'
    c += '<text class="ts" x="20" y="252">La bola baja de izquierda a derecha. Cada cuña sobresale el sensor + 2–3 mm; el haz cruza de pared a pared.</text>'
    svg("carril-embudo", 760, 262, "Dos cuñas en ángulo recto en el carril y la barrera IR pegada a las paredes justo detrás", c)


# ---------------------------------------------------------------- banco en la protoboard
def protoboard_banco():
    """Vista de arriba del banco: ESP32 en su placa de bornas y la protoboard con los sensores."""
    c = ""
    rojo, negro = "var(--rojo,#c0392b)", "var(--tinta,#1d1d1b)"
    colores = {"3V3": rojo, "GND": negro, "32": "var(--serie1,#2563a8)", "33": "var(--serie2,#b8860b)",
               "27": "var(--verde,#2e8b57)", "14": "var(--morado,#7b4fb0)"}
    col = lambda n: 290 + (n - 1) * 15            # x de la columna n (1–30)
    fila = {"-": 160, "+": 174, "a": 200, "b": 214, "c": 228, "d": 242, "e": 256,
            "f": 286, "g": 300, "h": 314, "i": 328, "j": 342, "-2": 368, "+2": 382}

    # ESP32 en la placa de bornas: la columna de pines del lado de 3V3, en su orden
    c += '<rect class="zona" x="20" y="40" width="190" height="420" rx="8"/>'
    c += '<rect class="caja" x="36" y="70" width="80" height="330" rx="4"/>'
    c += '<text class="t tc tb" x="76" y="200">ESP32</text><text class="ts tc" x="76" y="216">DevKitC</text>'
    c += '<rect class="caja" x="59" y="400" width="34" height="22" rx="3"/><text class="ts tc" x="76" y="440">USB</text>'
    c += '<text class="ts" x="28" y="58">placa de bornas</text>'
    pines = ["3V3", "EN", "VP", "VN", "34", "35", "32", "33", "25", "26", "27", "14", "12", "GND",
             "13", "D2", "D3", "CMD", "5V"]
    ypin = {}
    for i, pin in enumerate(pines):
        y = 66 + i * 19
        ypin[pin] = y
        usado = pin in colores
        c += (f'<rect x="186" y="{y - 7}" width="18" height="14" rx="2" '
              f'style="fill:var(--papel,#fff);stroke:var(--suave,#6b6a65)"/>')
        etq = pin if not pin.isdigit() else "GPIO " + pin
        clase = "t te tb" if usado else "ts te"
        c += f'<text class="{clase}" x="180" y="{y + 4}" style="font-size:11px">{etq}</text>'
        if usado:
            c += f'<circle cx="195" cy="{y}" r="3.5" style="fill:{colores[pin]}"/>'

    # protoboard: raíles arriba (− y +), filas a–e, canal central, f–j y raíles de abajo
    c += '<rect class="zona" x="270" y="145" width="470" height="252" rx="6"/>'
    c += f'<line x1="282" y1="{fila["-"] - 8}" x2="728" y2="{fila["-"] - 8}" style="stroke:var(--serie1,#2563a8);stroke-width:1.5"/>'
    c += f'<line x1="282" y1="{fila["+"] + 8}" x2="728" y2="{fila["+"] + 8}" style="stroke:{rojo};stroke-width:1.5"/>'
    c += f'<text class="t tb" x="276" y="{fila["-"] + 4}" style="fill:var(--serie1,#2563a8)">−</text>'
    c += f'<text class="t tb" x="276" y="{fila["+"] + 4}" style="fill:{rojo}">+</text>'
    c += '<rect x="270" y="268" width="470" height="6" style="fill:var(--linea,#e3e1db)"/>'
    for f_, y in fila.items():
        for n in range(1, 31):
            opaco = "" if f_ in "-+abcde" and len(f_) == 1 else "opacity:.45;"
            c += f'<rect x="{col(n) - 2.5}" y="{y - 2.5}" width="5" height="5" style="fill:var(--suave,#6b6a65);{opaco}"/>'
        if len(f_) == 1 and f_.isalpha():
            c += f'<text class="ts tc" x="279" y="{y + 4}" style="font-size:10px">{f_}</text>'
    for n in (1, 5, 10, 15, 20, 25, 30):
        c += f'<text class="ts tc" x="{col(n)}" y="192" style="font-size:9px">{n}</text>'
    c += '<text class="ts" x="500" y="392" style="font-size:11px">la mitad de abajo no se usa</text>'

    def punta(x, y, color):
        return f'<circle cx="{x}" cy="{y}" r="3.5" style="fill:{color};stroke:var(--papel,#fff);stroke-width:1"/>'

    def hilo(x1, y1, x2, y2, color, blanco=False):
        if blanco:  # el hilo blanco del receptor, con borde para que se vea sobre fondo claro
            return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke:{negro};stroke-width:4.5"/>'
                    f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke:#f5f5f2;stroke-width:2.5"/>'
                    + f'<circle cx="{x2}" cy="{y2}" r="3.5" style="fill:#f5f5f2;stroke:{negro};stroke-width:1.2"/>')
        return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke:{color};stroke-width:2.5"/>'
                + punta(x2, y2, color))

    # sensores encima de la protoboard, con sus cables directos a los agujeros
    sensores = [("Receptor A", 4, 6, True), ("Receptor B", 12, 14, True),
                ("Emisor B", 19, 20, False), ("Emisor A", 25, 26, False)]
    for nombre, c0, cs, receptor in sensores:
        x0 = col(c0) - 22
        c += caja(x0, 40, 86 if receptor else 70, 44, [nombre, "3 cables" if receptor else "2 cables"])
        if receptor:
            c += hilo(col(c0), 84, col(c0), fila["+"], rojo)
            c += hilo(col(c0 + 1), 84, col(c0 + 1), fila["-"], negro)
            c += hilo(col(cs), 84, col(cs), fila["a"], None, blanco=True)
            # pull-up de 5,1 kΩ: del raíl + a la fila c de la misma columna que la señal
            xr = col(cs) + 22
            c += f'<line class="l" x1="{xr}" y1="{fila["+"]}" x2="{col(cs)}" y2="{fila["c"]}"/>'
            c += (f'<rect x="-4" y="-11" width="8" height="22" rx="2" '
                  f'transform="translate({(xr + col(cs)) / 2},{(fila["+"] + fila["c"]) / 2}) rotate(19)" '
                  f'style="fill:var(--madera,#c9a77c);stroke:var(--madera-borde,#9c7a50)"/>')
            c += punta(xr, fila["+"], negro) + punta(col(cs), fila["c"], negro)
        else:
            c += hilo(col(c0), 84, col(c0), fila["-"], negro)
            c += hilo(col(cs), 84, col(cs), fila["a"], rojo)
    for n in (6, 14):
        c += (f'<rect x="{col(n) + 27}" y="{fila["b"] - 6}" width="40" height="15" rx="3" '
              f'style="fill:var(--papel,#fff);opacity:.9"/>'
              f'<text class="ts" x="{col(n) + 30}" y="{fila["b"] + 5}" style="font-size:11px">5,1 kΩ</text>')

    # duponts del ESP32: alimentación a los raíles y una señal a la fila e de cada columna
    def dupont(pin, x2, y2, desde_abajo):
        y1 = ypin[pin]
        cy = y2 + 90 if desde_abajo else y2
        return (f'<path d="M204,{y1} C250,{y1} {x2 - (0 if desde_abajo else 50)},{cy} {x2},{y2}" '
                f'style="stroke:{colores[pin]};stroke-width:2.5;fill:none"/>' + punta(x2, y2, colores[pin]))
    c += dupont("3V3", col(1), fila["+"], False)
    c += dupont("GND", col(2), fila["-"], False)
    for pin, n in (("32", 6), ("33", 14), ("27", 20), ("14", 26)):
        c += dupont(pin, col(n), fila["e"], True)

    for i, linea in enumerate(["Cada señal: cable del sensor en la fila a, pull-up en la c y dupont al ESP32 en la e,",
                               "todo en la misma columna. Raíl + = 3,3 V (nunca 5 V), raíl − = GND.",
                               "Si los raíles están cortados a media placa, usa solo la mitad izquierda."]):
        c += f'<text class="ts" x="270" y="{420 + i * 16}">{linea}</text>'
    svg("banco-protoboard", 760, 470, "Banco de pruebas: montaje en la protoboard, visto desde arriba", c)


if __name__ == "__main__":
    for f in (arquitectura, secuencia, barrera, alimentacion, haces,
              piezo_montaje, piezo_circuito, piezo_senal, piezo_ventana, piezo_calibracion,
              tiras_conexion, maquina_estados, carril_embudo, protoboard_banco,
              banco_conexiones, cableado_general, placa_interfaz,
              alimentacion_cableado, alimentacion_montaje, modo_enchufado):
        f()
    print("Diagramas generados en", DIR)
