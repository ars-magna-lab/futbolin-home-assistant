#!/usr/bin/env python3
# Mezcla los sonidos de reserva del marcador: público, redoble y locuciones.
#
#   python3 locutor/mezcla.py <directorio>
#
# <directorio> tiene que tener fuentes/publico.wav, fuentes/redoble_largo.mp3 y
# las voces voz_*.mp3 (ver locutor/README.md). Deja los 8 MP3 en
# <directorio>/salida/, normalizados a −14 LUFS. Necesita ffmpeg.
import subprocess, sys, os
os.chdir(sys.argv[1])
os.makedirs("salida", exist_ok=True)
PUB, RED = "fuentes/publico.wav", "fuentes/redoble_largo.mp3"

def pista(f, desde, dur, retardo, vol, ent=0.05, sal=0.3):
    return (f, f"atrim={desde}:{desde + dur},asetpts=PTS-STARTPTS,aformat=sample_rates=44100:channel_layouts=mono,"
               f"afade=t=in:d={ent},afade=t=out:st={max(0, dur - sal)}:d={sal},volume={vol},adelay={int(retardo * 1000)}")

def voz(n, retardo, vol=2.2):
    return pista(f"voz_{n}.mp3", 0, 3, retardo, vol, 0.01, 0.05)

def gol(e, dur_publico=3.6):
    return [pista(PUB, 1, dur_publico, 0, 0.32, 0.15, 1.0), voz(f"gol_{e}", 0.3)]

SONIDOS = {}
for e in "ab":
    SONIDOS[f"gol_{e}"] = gol(e)
    SONIDOS[f"gol_{e}_bola"] = gol(e, 3.2) + [pista(RED, 1.2, 2.4, 2.8, 0.9, 0.4, 0.2), voz("bola", 4.9)]
    SONIDOS[f"gol_{e}_buena"] = gol(e, 3.2) + [pista(RED, 1.2, 4.2, 2.8, 1.0, 3.0, 0.15),
                                              voz("buena", 7.0, 2.6), pista(PUB, 4, 3.0, 7.0, 0.3, 0.05, 1.2)]
    SONIDOS[f"fin_{e}"] = [pista(PUB, 0, 8, 0, 0.32, 0.15, 2.0), voz(f"gol_{e}", 0.3), voz(f"fin_{e}", 2.5, 2.6)]

for nombre, pistas in SONIDOS.items():
    args = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    filtros = []
    for i, (f, filtro) in enumerate(pistas):
        args += ["-i", f]
        filtros.append(f"[{i}:a]{filtro}[p{i}]")
    filtros.append("".join(f"[p{i}]" for i in range(len(pistas))) +
                   f"amix=inputs={len(pistas)}:normalize=0:duration=longest,loudnorm=I=-14:TP=-1.5[s]")
    args += ["-filter_complex", ";".join(filtros), "-map", "[s]", "-ar", "44100", "-ac", "1", "-b:a", "96k", f"salida/{nombre}.mp3"]
    subprocess.run(args, check=True)
    print(nombre)
