#!/usr/bin/env python3
"""Carga wled/presets.json en el WLED de las tiras.

Antes guarda una copia de los presets que tenga ahora en wled/copias/ (no se
sube al repo). Sustituye TODOS los presets del WLED. Pide confirmación salvo
con --si. La IP del WLED va en --ip o en la variable de entorno WLED_IP.

    python3 wled/cargar_presets.py --ip <ip-del-wled>              # pregunta antes de subir
    WLED_IP=<ip-del-wled> python3 wled/cargar_presets.py --si      # sin preguntar
    python3 wled/cargar_presets.py --ip <ip-del-wled> --solo-copia # solo la copia

Para volver atrás: --fichero wled/copias/presets-<fecha>.json.
Usa la misma subida que la página /edit de WLED (POST /upload con el fichero
/presets.json). Solo la biblioteca estándar de Python.
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import uuid
from pathlib import Path

CARPETA = Path(__file__).resolve().parent


def leer(url):
    with urllib.request.urlopen(url, timeout=10) as respuesta:
        return respuesta.read()


def subir(ip, contenido):
    frontera = uuid.uuid4().hex
    cuerpo = (
        f"--{frontera}\r\n"
        'Content-Disposition: form-data; name="data"; filename="/presets.json"\r\n'
        "Content-Type: application/json\r\n\r\n"
    ).encode() + contenido + f"\r\n--{frontera}--\r\n".encode()
    peticion = urllib.request.Request(
        f"http://{ip}/upload", data=cuerpo, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={frontera}"})
    with urllib.request.urlopen(peticion, timeout=20) as respuesta:
        return respuesta.status


def main():
    opciones = argparse.ArgumentParser(description="Carga los presets del futbolín en WLED")
    opciones.add_argument("--ip", default=os.environ.get("WLED_IP"),
                          help="IP del WLED (o la variable de entorno WLED_IP)")
    opciones.add_argument("--fichero", type=Path, default=CARPETA / "presets.json", help="presets a subir")
    opciones.add_argument("--si", action="store_true", help="no pedir confirmación")
    opciones.add_argument("--solo-copia", action="store_true", help="solo guardar la copia de los actuales")
    args = opciones.parse_args()
    if not args.ip:
        opciones.error("falta la IP del WLED: --ip <ip> o la variable de entorno WLED_IP")

    # 1. Comprobar el fichero antes de tocar nada
    contenido = args.fichero.read_bytes()
    nuevos = json.loads(contenido)
    nombres = {k: v.get("n", "") for k, v in nuevos.items() if k != "0"}

    # 2. Qué WLED es y copia de lo que tiene
    info = json.loads(leer(f"http://{args.ip}/json/info"))
    print(f"WLED «{info.get('name')}» {info.get('ver')} en {args.ip}, {info['leds']['count']} píxeles")
    actuales = leer(f"http://{args.ip}/presets.json")
    copias = CARPETA / "copias"
    copias.mkdir(exist_ok=True)
    copia = copias / f"presets-{time.strftime('%Y%m%d-%H%M%S')}.json"
    copia.write_bytes(actuales)
    try:
        n_actuales = len([k for k in json.loads(actuales) if k != "0"])
    except ValueError:
        n_actuales = "?"
    print(f"Copia de los {n_actuales} presets actuales en {copia}")
    if args.solo_copia:
        return 0

    # 3. Confirmar y subir
    print(f"Se van a sustituir por los {len(nombres)} de {args.fichero}:")
    for k, n in nombres.items():
        print(f"  {k:>3}  {n}")
    if not args.si and input("¿Subirlos? Escribe «si»: ").strip().lower() not in ("si", "sí"):
        print("No se ha subido nada.")
        return 1
    estado = subir(args.ip, contenido)
    print(f"Subido (HTTP {estado}).")

    # 4. Comprobar que WLED tiene los nuevos
    time.sleep(1)
    cargados = json.loads(leer(f"http://{args.ip}/presets.json"))
    if {k: v.get("n", "") for k, v in cargados.items() if k != "0"} != nombres:
        print("AVISO: los presets del WLED no coinciden con el fichero. Revisa en la web de WLED.")
        return 2
    print("Comprobado: el WLED tiene los presets nuevos. Recarga su web para verlos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
