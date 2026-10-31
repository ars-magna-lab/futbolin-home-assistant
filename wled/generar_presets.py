#!/usr/bin/env python3
"""Genera wled/presets.json, los presets de WLED del futbolín.

Los presets no se editan a mano: se cambian aquí y se regenera con

    python3 wled/generar_presets.py
    python3 wled/generar_presets.py --tira-a 28 --tira-b 28

Las tiras solo hacen efectos de luz (el marcador está en la tablet): cada preset
lleva 2 segmentos, uno por tira, que normalmente hacen lo mismo.

Montaje (aquí, en «Montaje»):
- El píxel 0 de las tiras está en la portería del Madrid (PORTERIA_A_EN_PIXEL_0):
  da la dirección de las olas (la del gol va hacia la portería contraria).
- Las dos tiras tienen el píxel 0 en el mismo extremo del campo. Si una se
  remonta al revés, se corrige con «Reverse» en su salida (Config → LED
  Preferences de WLED), no aquí.
El orden de color (BRG) va en la configuración de LED de WLED y los presets no lo
tocan: aquí los colores son RGB normales.

Contrato de IDs con el ESP32 (esphome/futbolin.h) y con HA: docs/README.md.
"""

import argparse
import json
from pathlib import Path

# ---------------------------------------------------------------- montaje
# Píxeles de cada tira (WS2811 de 12 V: 1 píxel = 3 LEDs). La tira A va
# primero en WLED y la B empieza en el píxel LONGITUD["A"]; tienen que cuadrar
# con las salidas de Config → LED Preferences.
LONGITUD = {"A": 28, "B": 28}
# True: el píxel 0 de las tiras está en el extremo de la portería que defiende el
# equipo A (Madrid). Si la ola del gol va hacia el lado
# que no es (tiras remontadas), poner False.
PORTERIA_A_EN_PIXEL_0 = True

# El efecto Running de WLED avanza hacia los píxeles altos (FX.cpp, running_base);
# con «rev» en el segmento, hacia el píxel 0. En Running Dual el color 1 avanza
# hacia los altos y el color 3 hacia el píxel 0.

# ---------------------------------------------------------------- colores (RGB)
# Los del dashboard (docs/maqueta/marcador.html), ajustados
# a LED: el blanco del Madrid algo cálido (gasta menos que el blanco puro) y el oro
# tira a ámbar, que en LED se ve dorado.
MADRID = [255, 225, 170]        # --madrid #f6f3ea
MADRID_2 = [255, 140, 0]        # --madrid-oro #d8b45a
BARCA = [0, 60, 255]            # --barcelona #3d8bff
BARCA_2 = [200, 0, 40]          # --barcelona-grana #e0174f
COLORES = {"a": (MADRID, MADRID_2), "b": (BARCA, BARCA_2)}
PILOTO = [255, 120, 30]         # blanco muy cálido, el piloto de encendido
ORO = [255, 160, 0]             # «la buena»
ROJO = [255, 0, 0]              # aviso
NEGRO = [0, 0, 0]

# ---------------------------------------------------------------- tiempos (décimas de segundo)
# OLA + FUEGOS (lo que dura el gol) tiene que cuadrar con gol_luz_ms de
# esphome/futbolin.yaml: el ESP32 manda bola de partido o la buena un
# poco después de que acabe el gol.
OLA = 20
FUEGOS = 10
FIESTA = 100
TENSION = 80                    # bola de partido
SUBIDA = 100                    # la buena: cada paso del latido, hasta el último

# ---------------------------------------------------------------- IDs (contrato)
REPOSO, JUEGO, GOL_A, GOL_B, BOLA_PARTIDO_A, LA_BUENA, FIN_A, FIN_B, AVISO, BOLA_PARTIDO_B = range(1, 11)
# Pasos de las playlists (el ESP32 no los manda directamente)
(OLA_A, OLA_B, FUEGOS_A, FUEGOS_B, FIESTA_A, FIESTA_B,
 TENSION_A, TENSION_B) = range(11, 19)
# El latido de la buena: en Heartbeat el ritmo es 40 + sx / 8 pulsaciones por minuto.
# De 48 a 68 en un minuto y se queda en 71, el máximo del efecto.
BRILLO_BUENA = 60
LATIDOS = {19 + i: sx for i, sx in enumerate((64, 96, 128, 160, 192, 224, 255))}

# ---------------------------------------------------------------- efectos de WLED 16.0.1 (/json/effects)
SOLID, BREATHE, RUNNING, FIREWORKS, SOLID_PATTERN, HEARTBEAT = 0, 2, 15, 42, 83, 100
PALETA_COLORES_1_2 = 3          # /json/palettes: «* Colors 1&2»


def tiras():
    return [("A", 0, LONGITUD["A"]), ("B", LONGITUD["A"], LONGITUD["A"] + LONGITUD["B"])]


def hacia_porteria(equipo):
    """`rev` para que Running avance hacia la portería que defiende `equipo`."""
    return (equipo == "a") == PORTERIA_A_EN_PIXEL_0  # hacia el píxel 0 hay que invertir


def segmento(i, tira, inicio, fin, fx=SOLID, col=(NEGRO,), bri=255, sx=128, ix=128, pal=0, rev=False):
    col = [list(c) for c in col] + [NEGRO] * (3 - len(col))
    return {
        "id": i, "start": inicio, "stop": fin, "grp": 1, "spc": 0, "of": 0,
        "on": True, "frz": False, "bri": bri, "n": f"Tira {tira}",
        "col": col, "fx": fx, "sx": sx, "ix": ix, "pal": pal,
        "sel": True, "rev": rev, "mi": False,
    }


def preset(nombre, bri, transicion=0, **efecto):
    """Las dos tiras con el mismo efecto."""
    return {
        "n": nombre, "on": True, "bri": bri, "transition": transicion, "mainseg": 0,
        "seg": [segmento(i, *t, **efecto) for i, t in enumerate(tiras())],
    }


def playlist(nombre, pasos, final):
    """Lista de (preset, décimas) que acaba en el preset `final`.

    Lleva `on` porque WLED no arranca una playlist con las tiras apagadas.
    """
    return {
        "n": nombre, "on": True,
        "playlist": {
            "ps": [p for p, _ in pasos], "dur": [d for _, d in pasos],
            "transition": [0] * len(pasos), "repeat": 1, "end": final, "r": False,
        },
    }


def contrario(equipo):
    return "b" if equipo == "a" else "a"


def presets():
    p = {
        # Piloto de encendido: un solo píxel tenue por tira, el primero (Solid
        # Pattern: 1 píxel encendido y 256 apagados)
        REPOSO: preset("reposo", 60, transicion=7, fx=SOLID_PATTERN, col=(PILOTO, NEGRO), sx=0, ix=255),
        # Partida en curso: apagadas (el marcador está en la tablet)
        JUEGO: {"n": "juego", "on": False, "transition": 7},
        GOL_A: playlist("gol_a", [(OLA_A, OLA), (FUEGOS_A, FUEGOS)], JUEGO),
        GOL_B: playlist("gol_b", [(OLA_B, OLA), (FUEGOS_B, FUEGOS)], JUEGO),
        BOLA_PARTIDO_A: playlist("bola_partido_a", [(TENSION_A, TENSION)], JUEGO),
        BOLA_PARTIDO_B: playlist("bola_partido_b", [(TENSION_B, TENSION)], JUEGO),
        # La buena: el latido se acelera y se queda en el último paso hasta que el
        # gol que decide lance la fiesta (o una corrección cambie la fase)
        LA_BUENA: playlist("la_buena", [(p, SUBIDA) for p in list(LATIDOS)[:-1]], list(LATIDOS)[-1]),
        FIN_A: playlist("fin_a", [(OLA_A, OLA), (FUEGOS_A, FUEGOS), (FIESTA_A, FIESTA)], REPOSO),
        FIN_B: playlist("fin_b", [(OLA_B, OLA), (FUEGOS_B, FUEGOS), (FIESTA_B, FIESTA)], REPOSO),
        # Atasco o autotest fallido: rojo fijo hasta que se resuelve
        AVISO: preset("aviso", 50, fx=SOLID, col=(ROJO,)),
    }
    for n, (latido, sx) in enumerate(LATIDOS.items(), 1):
        p[latido] = preset(f"la_buena_latido_{n}", BRILLO_BUENA, fx=HEARTBEAT, col=(ORO, NEGRO), sx=sx)
    for e, ola, fuegos, fiesta, tension in (("a", OLA_A, FUEGOS_A, FIESTA_A, TENSION_A),
                                            ("b", OLA_B, FUEGOS_B, FIESTA_B, TENSION_B)):
        principal, segundo = COLORES[e]
        nombre = e
        # Gol: ola del color de quien marca que cruza el campo hacia la portería
        # donde ha entrado la bola (la del contrario), y luego estalla
        p[ola] = preset(f"gol_{nombre}_ola", 150, fx=RUNNING, col=(principal, NEGRO), sx=230, ix=60,
                        rev=hacia_porteria(contrario(e)))
        p[fuegos] = preset(f"gol_{nombre}_fuegos", 150, fx=FIREWORKS, col=(principal, segundo),
                           ix=230, pal=PALETA_COLORES_1_2)
        # Victoria: fuegos artificiales con los dos colores del ganador
        p[fiesta] = preset(f"fiesta_{nombre}", 130, fx=FIREWORKS, col=(principal, segundo),
                           ix=200, pal=PALETA_COLORES_1_2)
        # Bola de partido: las tiras respiran en el color del equipo que tiene 5
        p[tension] = preset(f"bola_partido_{nombre}_efecto", 60, fx=BREATHE, col=(principal, NEGRO), sx=110)
    return {"0": {}, **{str(k): v for k, v in sorted(p.items())}}


def comprobar(datos):
    """Coherencia mínima: IDs, playlists que apuntan a presets que existen, segmentos."""
    ids = {int(k) for k in datos if k != "0"}
    assert all(1 <= i <= 250 for i in ids)
    nombres = [v["n"] for k, v in datos.items() if k != "0"]
    assert len(nombres) == len(set(nombres)), "nombres repetidos"
    for k, v in datos.items():
        if "playlist" in v:
            pl = v["playlist"]
            assert len(pl["ps"]) == len(pl["dur"]) == len(pl["transition"]), k
            assert all(p in ids and "playlist" not in datos[str(p)] for p in pl["ps"]), k
            assert pl["end"] in ids and all(d > 0 for d in pl["dur"]), k
        elif "seg" in v:
            assert [(s["id"], s["start"], s["stop"]) for s in v["seg"]] == \
                [(i, a, b) for i, (_, a, b) in enumerate(tiras())], k


if __name__ == "__main__":
    opciones = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    opciones.add_argument("--tira-a", type=int, default=LONGITUD["A"], help="píxeles de la tira A")
    opciones.add_argument("--tira-b", type=int, default=LONGITUD["B"], help="píxeles de la tira B")
    args = opciones.parse_args()
    LONGITUD = {"A": args.tira_a, "B": args.tira_b}
    datos = presets()
    comprobar(datos)
    destino = Path(__file__).with_name("presets.json")
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{destino}: {len(datos) - 1} presets")
