#!/usr/bin/env python3
"""Genera las locuciones del locutor del marcador: un MP3 por frase, solo voz.

    HA_URL=http://<ip-de-ha>:8123 HA_TOKEN=<token> python3 locutor/locutor.py
    python3 locutor/locutor.py [--solo-textos | --reparto | --prueba-nombres]

Las frases salen de las plantillas de abajo, con un jugador al azar de cada
equipo (semilla fija por equipo y momento: cada vez salen las mismas, y añadir
una plantilla al final de una lista no cambia las demás). La voz es una entidad
TTS de Home Assistant (por defecto `tts.locutor`, una integración de OpenAI TTS
con la voz «ballad» y un prompt de narrador deportivo), que se pide por la API
de HA: la URL en HA_URL y un token de larga duración en HA_TOKEN. El motor y la
voz se cambian con LOCUTOR_MOTOR y LOCUTOR_VOZ. Las voces ya descargadas se
guardan en trabajo/voz/ y no se vuelven a pedir.

Los nombres se escriben bien en el índice, pero a la voz le llega la grafía de
PRONUNCIACION (p. ej. «Tchouaméni» se manda como «Chuaméni»).

Deja en trabajo/locutor/ los MP3 y el índice locutor.json, que lista el texto
de cada fichero. Se copian a HA en /config/www/futbolin/sonidos/locutor/.

Nombre de los ficheros: <momento>_<equipo que marca>[_<goles A>-<goles B> | _<racha>]_<n>.mp3
  normal_a_7, primero_b_2, empate_a_2-2_1, remontada_b_3, bola_a_5-3_2,
  buena_b_4, fin_a_6-4_1, goleada_b_1-6_3, salva_a_2, estreno_b_1,
  escapa_a_3, racha_b_4_2, corta_a_1, recorta_b_5, desempata_a_2
El paquete de HA elige el momento con la secuencia de goles (la regla está en
momento(), abajo) y el dashboard un número al azar dentro de él (cuántos hay de
cada uno, en CUANTOS).

Al empezar cada partida suena además una presentación del clásico, sin equipo
ni marcador: inicio_<n>.mp3. Las ultracortas, también sin equipo: corto_<n>.mp3.

--reparto      cuánto sale cada momento en una partida (cálculo exacto, 50 % y 65 %)
--prueba-nombres  trabajo/prueba_nombres.mp3 y .txt: «¡Gol de X!» con cada nombre
               tal como lo dirá la voz (y las variantes de los dudosos)

Necesita ffmpeg. La carpeta de trabajo se puede cambiar con LOCUTOR_TRABAJO.
"""

import hashlib
import json
import os
import pathlib
import random
import subprocess
import sys
import urllib.request

AQUI = pathlib.Path(__file__).resolve().parent
TRABAJO = pathlib.Path(os.environ.get("LOCUTOR_TRABAJO", AQUI / "trabajo"))
SALIDA = TRABAJO / "locutor"
CACHE = TRABAJO / "voz"
HA = os.environ.get("HA_URL", "").rstrip("/")
MOTOR = os.environ.get("LOCUTOR_MOTOR", "tts.locutor")
VOZ = os.environ.get("LOCUTOR_VOZ", "ballad")

EQUIPOS = {
    "a": {"corto": "Madrid", "largo": "Real Madrid", "portero": "Courtois"},
    "b": {"corto": "Barça", "largo": "Barcelona", "portero": "Joan García"},
}

# Plantillas de la temporada 2026/27, por peso: los delanteros marcan más a
# menudo. Para otros equipos, cambia EQUIPOS, JUGADORES y PRONUNCIACION.
JUGADORES = {
    "a": {
        3: ["Mbappé", "Vinícius", "Rodrygo", "Endrick", "Brahim"],
        2: ["Bellingham", "Valverde", "Arda Güler", "Camavinga", "Tchouaméni", "Bernardo Silva", "Carlos Espí", "Diomande"],
        1: ["Trent", "Militão", "Rüdiger", "Carreras", "Cucurella", "Asencio", "Konaté", "Mendy", "Dumfries",
            "Thiago Pitarch"],
    },
    "b": {
        3: ["Lamine Yamal", "Raphinha", "Gabriel Jesus", "Adeyemi", "Gordon"],
        2: ["Pedri", "Gavi", "Fermín", "Dani Olmo", "Frenkie de Jong", "Roony", "Rodri", "Marc Bernal"],
        1: ["Cancelo", "Balde", "Cubarsí", "Koundé", "Christensen", "Eric García", "Gerard Martín", "Xavi Espart",
            "Fariñas"],
    },
}

# Cómo se le escribe cada nombre a la voz (OpenAI lee en español: hay que
# escribirlo como suena). Los que no están se mandan tal cual. Si hay duda, la
# primera variante es la que se usa y las demás solo suenan en la prueba de
# nombres (--prueba-nombres), para elegir de oído.
PRONUNCIACION = {
    # Real Madrid
    "Courtois": ["Curtuá"],
    "Mbappé": ["Embapé"],
    "Rodrygo": ["Rodrigo"],
    "Endrick": ["Éndrik"],
    "Brahim": ["Braím"],
    "Bellingham": ["Bélingam"],
    "Arda Güler": ["Arda Gúler"],
    "Tchouaméni": ["Chuaméni"],
    "Diomande": ["Diomandé"],
    "Militão": ["Militáo"],
    "Rüdiger": ["Rúdiguer"],
    "Mendy": ["Mendi"],
    "Dumfries": ["Dúmfris"],
    "Thiago Pitarch": ["Tiago Pitarch"],
    # Barça
    "Joan García": ["Joan García"],
    "Lamine Yamal": ["Lamín Yamal"],
    "Raphinha": ["Rafiña"],
    "Gabriel Jesus": ["Gabriel Jesús"],
    "Adeyemi": ["Adeyémi"],
    "Gordon": ["Górdon"],
    "Frenkie de Jong": ["Frenki de Yong"],
    "Roony": ["Rúni"],
    "Balde": ["Baldé"],
    "Koundé": ["Kundé"],
    "Christensen": ["Cristensen"],
    "Eric García": ["Éric García"],
    "Gerard Martín": ["Yerard Martín"],
    "Xavi Espart": ["Chavi Espart"],
}


def hablado(nombre):
    """Cómo se le escribe un nombre a la voz."""
    return PRONUNCIACION.get(nombre, [nombre])[0]


NUMEROS = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis"]

# Gol normal: corto, sin marcador. {j} jugador, {e} equipo, {p} portero rival.
NORMAL = [
    "¡Gol de {j}!", "¡Golazo de {j}!", "¡Goooool! ¡{j}!", "¡Chicharrazo de {j}!", "¡Tremendo chicharrazo de {j}!",
    "¡Golazo de chilena de {j}!", "¡De tacón! ¡Gol de {j}!", "¡A la escuadra! ¡{j}!", "¡Zapatazo de {j}!",
    "¡Qué misil de {j}!", "¡Gol, gol, gol! ¡{j}!", "¡{j}, {j}! ¡Goooool!", "¡Al fondo de la red! ¡{j}!",
    "¡Ni la ha visto {p}! ¡{j}!", "¡Imparable, {j}!", "¡Qué definición de {j}!", "¡Cabezazo de {j}! ¡Gol!",
    "¡De volea! ¡Golazo de {j}!", "¡Por toda la escuadra, {j}!", "¡Gol del {e}! ¡{j}!", "¡Qué barbaridad, {j}!",
    "¡Por debajo de las piernas! ¡{j}!", "¡{j} ha roto la red!", "¡Sacad la grúa, que {j} se ha llevado la portería!",
    "¡Eso no lo para ni {p}! ¡{j}!", "¡Toma ya! ¡Gol de {j}!", "¡Pepinazo de {j}!", "¡Obra de arte de {j}!",
    "¡Gol de bandera de {j}!", "¡Qué golazo, señores! ¡{j}!",
    # cortas
    "¡Pum! ¡{j}!", "¡Toma! ¡{e}!", "¡{j} no perdona!", "¡Y otra de {j}!", "¡Sin piedad, {j}!", "¡A placer, {j}!",
    # de garaje
    "¡{p}, esa era tuya!", "¡{p} todavía la está buscando!", "¡Golazo de {j}! ¡Y sin despeinarse!",
    "¡Que avisen a los vecinos! ¡{j}!", "¡{j} se ha ganado el postre!", "¡Qué muñeca tiene {j}!",
    "¡De rebote, pero vale igual! ¡{j}!", "¡Lo de {j} debería ser ilegal!", "¡Eso deja marca en la pared! ¡{j}!",
]
# Ultracortas, sin equipo ni jugador (corto_<n>.mp3, como inicio): no las elige
# el paquete, sino el dashboard, que las mete de vez en cuando en lugar de las
# frases de los momentos menores (normal, desempata, recorta, escapa, racha y corta)
CORTO = ["¡Pum!", "¡Para casa!", "¡Dentro!", "¡Zas!", "¡Cataplum!", "¡Toma castaña!", "¡Madre mía!", "¡Ay, mamá!",
         "¡Uy, uy, uy… gol!", "¡Qué bonito!"]
PRIMERO = [
    "¡Primer gol del partido! ¡{j}!", "¡Se adelanta el {e}! ¡Gol de {j}!", "¡Abre el marcador {j}!",
    "¡El {e} golpea primero! ¡{j}!",
    "¡{j} rompe el hielo!", "¡Primer aviso del {e}!", "¡Uno a cero! ¡{j}!", "¡Estrena el marcador {j}!",
]
# {n} los goles de cada uno ({N} con mayúscula, al empezar la exclamación).
# Las dos listas, igual de largas (el dashboard usa un solo número para empate).
EMPATE = ["¡Empata el {e}! ¡{N} a {n}!", "¡Gol de {j}! ¡Tablas: {n} a {n}!",
          "¡Empate a {n}! ¡Lo iguala {j}!", "¡{N} a {n}! ¡Aquí no se rinde nadie!"]
EMPATE_4 = ["¡Empate a cuatro! ¡Esto arde! ¡{j}!", "¡Lo iguala el {e}! ¡Cuatro a cuatro! ¡Qué partido!",
            "¡Cuatro iguales! ¡Esto no es apto para cardíacos!", "¡{j} lo iguala! ¡Cuatro a cuatro y la cena en el aire!"]
# Remontada: iba perdiendo de dos o más y con este gol se pone por delante
REMONTADA = [
    "¡Remontada del {e}! ¡Iban perdiendo y ahora mandan! ¡{j}!",
    "¡No se rinde el {e}! ¡{j} completa la remontada! ¡Qué locura!",
    "¡Increíble! ¡El {e} estaba muerto y ha resucitado! ¡Gol de {j}!",
    "¡Esto es una remontada en toda regla! ¡{j}, {j}! ¡Golazo!",
    "¡Le ha dado la vuelta el {e}! ¡Quién lo iba a decir! ¡{j}!",
    "¡Épico! ¡Remontada del {e}! ¡{j} aparece cuando más falta hacía!",
    "¡Del entierro a la fiesta! ¡Remontada del {e}!",
    "¡Nunca des por muerto al {e}! ¡{j} le da la vuelta!",
]
# {r} los goles del rival
BOLA = ["¡Gol de {j}! ¡Bola de partido para el {e}! ¡Cinco a {r}!",
        "¡Cinco a {r}! ¡El {e} acaricia la victoria! ¡Bola de partido!",
        "¡Bola de partido! ¡Al {e} le falta una! ¡Cinco a {r}!",
        "¡Cinco a {r}! ¡El {e} ya va eligiendo la cena!"]
BUENA = [
    "¡Gol de {j}! ¡Cinco a cinco! ¡Nos vamos a la buena!",
    "¡Lo empata el {e}! ¡Cinco a cinco! ¡La buena! ¡Que nadie respire!",
    "¡Increíble, señores! ¡Cinco a cinco! ¡Todo se decide en la última bola!",
    "¡{j} nos lleva a la buena! ¡Cinco a cinco! ¡Tensión máxima en el garaje!",
    "¡Cinco a cinco! ¡Que se pare el mundo! ¡La buena!",
    "¡A la buena! ¡El que gane elige la cena!",
]
# {l} el nombre largo del equipo. FIN y FIN_5, igual de largas.
FIN = ["¡Se acabó! ¡Gana el {l} seis a {r}! ¡{j} pone la puntilla!",
       "¡Final del partido! ¡Victoria del {e}, seis a {r}! ¡Campeones!",
       "¡Ganó el {e}! ¡Seis a {r}! ¡Los otros friegan los platos!",
       "¡Seis a {r}! ¡El clásico es del {e}!"]
FIN_5 = ["¡En la buena! ¡{j} lo decide! ¡Gana el {e} seis a cinco! ¡Qué final!",
         "¡La buena es del {e}! ¡Seis a cinco! ¡Gol de {j}! ¡Qué manera de ganar!",
         "¡Seis a cinco en la buena! ¡El {e} elige la cena!",
         "¡Infarto en el garaje! ¡{j} gana la buena!"]
GOLEADA = ["¡Goleada! ¡Seis a {r}! ¡Paseo del {e}!", "¡Seis a {r}! ¡Esto ha sido un baile! ¡{j} cierra la fiesta!",
           "¡Se acabó! ¡Goleada histórica del {l}, seis a {r}!",
           "¡Seis a {r}! ¡Que alguien consuele a {p}!", "¡Seis a {r}! ¡Esto no se cuenta fuera del garaje!"]

# Momentos con contexto de la secuencia (v2); la regla de cada uno, en momento().
# Salva: el rival tiene bola de partido (5) y este gol no le deja ganar todavía
SALVA = ["¡Sigue vivo el {e}! ¡{j}!", "¡Bola de partido salvada! ¡Gol de {j}!",
         "¡Guardad el champán, que el {e} sigue vivo!", "¡{j} se niega a fregar los platos!"]
# Estreno: primer gol de un equipo que llevaba tres o más en contra
ESTRENO = ["¡Por fin marca el {e}! ¡{j}!", "¡Ya era hora! ¡{j} estrena al {e}!", "¡Despierta el {e}! ¡{j}!",
           "¡Que alguien apunte la fecha! ¡Marca el {e}!"]
# Escapa: con este gol saca tres de ventaja (3-0 o 4-1)
ESCAPA = ["¡Tres de ventaja! ¡Se escapa el {e}!", "¡Se va el {e}! ¡{j}!", "¡Esto huele a paliza! ¡{j}!",
          "¡Que alguien pare al {e}!"]
# Racha: tercer o cuarto gol seguido del mismo equipo ({K}/{n}: cuántos seguidos)
RACHA = ["¡{K} seguidos del {e}!", "¡Y van {n} seguidos! ¡{j} no para!", "¡{K} seguidos! ¡Que alguien despierte a {p}!"]
# Corta: el rival llevaba tres o más seguidos y este gol se los corta
CORTA = ["¡Se acabó la sequía! ¡{j}!", "¡Corta la racha el {e}! ¡{j}!", "¡Respira el {e}! ¡{j}!", "¡{j} pone el freno!"]
# Recorta: marca el que va perdiendo y sigue perdiendo
RECORTA = ["¡Recorta el {e}! ¡{j}!", "¡{j} mete al {e} en el partido!", "¡Aquí hay partido! ¡{j}!", "¡Se acerca el {e}!",
           "¡Todavía hay vida! ¡{j}!", "¡Ojo, que viene el {e}!"]
# Desempata: había empate (1-1 a 4-4) y este gol lo pone por delante
DESEMPATA = ["¡Se pone por delante el {e}! ¡{j}!", "¡{j} rompe el empate!", "¡Manda el {e}!",
             "¡Desempata {j}! ¡Qué momento!", "¡El {e} toma la delantera!", "¡Y ahora, por delante! ¡{j}!"]

# Al empezar la partida: la presentación del clásico, de unos 8 a 10 segundos
INICIO = [
    "¡Buenas tardes y bienvenidos al garaje! Hoy se juega el clásico: Real Madrid contra Barcelona. "
    "Once bolas, gana quien llegue a seis. ¡Que ruede el balón!",
    "¡Señoras y señores, se juega el clásico! El estadio del garaje está a reventar, "
    "las barras engrasadas y los porteros calentando. ¡Arranca el partido!",
    "¡Atención, que esto empieza! Madrid y Barça, frente a frente una vez más. "
    "Aquí no hay VAR ni excusas: lo que entra, sube al marcador. ¡A jugar!",
    "Muy buenas, aficionados. Noche grande en el garaje: el clásico de los clásicos. "
    "Las apuestas, al cincuenta por ciento. ¡Rueda la primera bola!",
    "¡Arranca el clásico! Dicen que el que gana hoy elige la cena. "
    "Mucha tensión en las barras, las muñecas preparadas… ¡y a jugar!",
    "¡Qué ambiente, señores! Lleno absoluto en el garaje para el Madrid-Barça. "
    "Recordad: nada de darle vueltas a las barras. ¡Comienza el partido!",
    "¡Pitido inicial! Once bolas por delante y un solo campeón. "
    "¿Quién se llevará el clásico de hoy? ¡Que empiece el espectáculo!",
    "Desde la cabina de retransmisión del garaje, ¡muy buenas! Se enfrentan los eternos rivales. "
    "Los porteros ya están clavados en su sitio. ¡Empezamos!",
    "¡Ya está aquí el partido que paraliza el barrio: Real Madrid contra Barcelona! "
    "Y si llegamos al cinco a cinco… ¡la buena! ¡Arranca el clásico!",
    "¡Se abre el telón! Ni Bernabéu ni Camp Nou: el mejor estadio del mundo es este garaje. "
    "Madrid contra Barça. ¡Bola al centro!",
    "Que nadie se confunda: hoy no hay amistosos. Aquí se juega el orgullo, la honra… "
    "y quién friega los platos. ¡Empieza el clásico!",
    "¡Bienvenidos a una nueva edición del clásico! Muñecas calientes, empuñaduras listas "
    "y el árbitro, como siempre, desaparecido. ¡Que gane el mejor!",
]

assert len(EMPATE) == len(EMPATE_4) and len(FIN) == len(FIN_5)
# Cuántos ficheros hay de cada momento (lo mismo que usa el dashboard)
CUANTOS = {"normal": len(NORMAL), "primero": len(PRIMERO), "empate": len(EMPATE), "remontada": len(REMONTADA),
           "bola": len(BOLA), "buena": len(BUENA), "fin": len(FIN), "goleada": len(GOLEADA), "salva": len(SALVA),
           "estreno": len(ESTRENO), "escapa": len(ESCAPA), "racha": len(RACHA), "corta": len(CORTA),
           "recorta": len(RECORTA), "desempata": len(DESEMPATA), "corto": len(CORTO),
           "inicio": len(INICIO)}


def marcador(e, propios, rival):
    """Goles A-B para el nombre del fichero."""
    return f"{propios}-{rival}" if e == "a" else f"{rival}-{propios}"


def momento(secuencia, nuevos=True):
    """El momento del último gol de una secuencia («abba…», con ese gol al final),
    como lo calcula el atributo `locutor` del paquete de HA. Va en orden de
    prioridad: gana el primero que se cumple. Con nuevos=False, la regla de la
    v1 (sin salva, estreno, escapa, racha, corta, recorta ni desempata). Devuelve el prefijo del fichero (sin el número de frase)."""
    e = secuencia[-1]
    a, b = secuencia.count("a"), secuencia.count("b")
    propios, rival = (a, b) if e == "a" else (b, a)
    m = marcador(e, propios, rival)
    peor = diferencia = 0  # la peor diferencia de quien marca antes de este gol
    for c in secuencia[:-1]:
        diferencia += 1 if c == e else -1
        peor = min(peor, diferencia)
    seguidos = len(secuencia) - len(secuencia.rstrip(e))  # contando este
    antes = secuencia[:-1]
    del_rival = len(antes) - len(antes.rstrip("b" if e == "a" else "a"))  # seguidos del rival justo antes
    if propios >= 6 and rival <= 1:
        return f"goleada_{e}_{m}"
    if propios >= 6:
        return f"fin_{e}_{m}"
    if a == 5 and b == 5:
        return f"buena_{e}"
    if propios == 5:
        return f"bola_{e}_{m}"
    if nuevos and rival == 5:
        return f"salva_{e}"
    if peor <= -2 and propios == rival + 1:
        return f"remontada_{e}"
    if propios == rival:
        return f"empate_{e}_{m}"
    if a + b == 1:
        return f"primero_{e}"
    if not nuevos:
        return f"normal_{e}"
    if propios == 1 and rival >= 3:
        return f"estreno_{e}"
    if propios - rival == 3:
        return f"escapa_{e}"
    if seguidos >= 3:
        return f"racha_{e}_{seguidos}"
    if del_rival >= 3:
        return f"corta_{e}"
    if rival > propios:
        return f"recorta_{e}"
    if propios == rival + 1:
        return f"desempata_{e}"
    return f"normal_{e}"


def reparto(prob_a, nuevos):
    """Cuántas veces sale de media cada momento en una partida, con prob_a la
    probabilidad de que cada gol sea del Madrid (cálculo exacto)."""
    cuenta = {}

    def seguir(s, prob):
        if s.count("a") == 6 or s.count("b") == 6:
            return
        for c, q in (("a", prob_a), ("b", 1 - prob_a)):
            clave = momento(s + c, nuevos).split("_")[0]
            cuenta[clave] = cuenta.get(clave, 0) + prob * q
            seguir(s + c, prob * q)

    seguir("", 1.0)
    return cuenta


def frases():
    """(nombre, texto, hablado) de cada locución: el texto con los nombres bien
    escritos (para el índice) y lo que se le manda a la voz."""
    lista = []
    for e, eq in EQUIPOS.items():
        rival = EQUIPOS["b" if e == "a" else "a"]
        pesos = [(j, w) for w, js in JUGADORES[e].items() for j in js]
        bolsas = {}

        def jugador(mom):
            # sin repetir hasta agotar la bolsa, para que salgan muchos distintos;
            # una bolsa por momento, para que añadir frases no cambie las demás
            azar, bolsa = bolsas.setdefault(mom, (random.Random(f"2026-{e}-{mom}"), []))
            if not bolsa:
                bolsa.extend(j for j, w in pesos for _ in range(w))
                azar.shuffle(bolsa)
            return bolsa.pop()

        def poner(mom, nombre, plantilla, **extra):
            j = jugador(mom)
            datos = dict(e=eq["corto"], l=eq["largo"], **extra)
            lista.append((nombre, plantilla.format(j=j, p=rival["portero"], **datos),
                          plantilla.format(j=hablado(j), p=hablado(rival["portero"]), **datos)))

        for mom, plantillas in (("normal", NORMAL), ("primero", PRIMERO), ("remontada", REMONTADA), ("buena", BUENA),
                                ("salva", SALVA), ("estreno", ESTRENO), ("escapa", ESCAPA), ("corta", CORTA),
                                ("recorta", RECORTA), ("desempata", DESEMPATA)):
            for i, t in enumerate(plantillas, 1):
                poner(mom, f"{mom}_{e}_{i}", t)
        for n in range(1, 5):
            for i, t in enumerate(EMPATE_4 if n == 4 else EMPATE, 1):
                poner("empate", f"empate_{e}_{marcador(e, n, n)}_{i}", t, n=NUMEROS[n], N=NUMEROS[n].capitalize())
        for r in range(0, 5):
            for i, t in enumerate(BOLA, 1):
                poner("bola", f"bola_{e}_{marcador(e, 5, r)}_{i}", t, r=NUMEROS[r])
        for r in range(2, 6):
            for i, t in enumerate(FIN_5 if r == 5 else FIN, 1):
                poner("fin", f"fin_{e}_{marcador(e, 6, r)}_{i}", t, r=NUMEROS[r])
        for r in (0, 1):
            for i, t in enumerate(GOLEADA, 1):
                poner("goleada", f"goleada_{e}_{marcador(e, 6, r)}_{i}", t, r=NUMEROS[r])
        for k in (3, 4):  # cinco seguidos ya es bola de partido
            for i, t in enumerate(RACHA, 1):
                poner("racha", f"racha_{e}_{k}_{i}", t, n=NUMEROS[k], K=NUMEROS[k].capitalize())
    for i, t in enumerate(CORTO, 1):
        lista.append((f"corto_{i}", t, t))
    for i, t in enumerate(INICIO, 1):
        lista.append((f"inicio_{i}", t, t))
    return lista


def voz(texto, token):
    """MP3 de la voz para un texto, de la caché o pedido a HA."""
    clave = hashlib.sha1(f"{MOTOR}|{VOZ}|{texto}".encode()).hexdigest()[:16]
    f = CACHE / f"{clave}.mp3"
    if not f.exists():
        cuerpo = json.dumps({"engine_id": MOTOR, "message": texto, "options": {"voice": VOZ}}).encode()
        cab = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
        for intento in range(3):  # OpenAI a veces tarda: se reintenta
            try:
                ruta = json.load(urllib.request.urlopen(urllib.request.Request(f"{HA}/api/tts_get_url", cuerpo, cab),
                                                        timeout=60))["path"]
                datos = urllib.request.urlopen(urllib.request.Request(HA + ruta, headers=cab), timeout=120).read()
                break
            except OSError as e:
                if intento == 2:
                    raise
                print("  reintento:", e, flush=True)
        f.write_bytes(datos)
    return f


def preparar(origen, destino, pausa=0.4):
    """Solo voz: sin los silencios de los extremos, un respiro al principio y
    `pausa` segundos al final, y el volumen igualado."""
    recorte = "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(origen), "-af",
                    f"{recorte},areverse,{recorte},areverse,adelay=150,apad=pad_dur={pausa},loudnorm=I=-14:TP=-1.5",
                    "-ar", "44100", "-ac", "1", "-b:a", "64k", str(destino)], check=True)


def token_ha():
    """El token de larga duración de HA (perfil de usuario → Seguridad), de HA_TOKEN."""
    token = os.environ.get("HA_TOKEN", "").strip()
    if not HA or not token:
        sys.exit("Faltan HA_URL (p. ej. http://<ip-de-ha>:8123) y HA_TOKEN (token de larga duración de HA)")
    return token


def prueba_nombres():
    """trabajo/prueba_nombres.mp3: «¡Gol de X!» (o «¡Paradón de X!» para los
    porteros) con cada nombre como lo dirá la voz, y las variantes de los
    dudosos seguidas; el orden, en prueba_nombres.txt."""
    porteros = [eq["portero"] for eq in EQUIPOS.values()]
    nombres = porteros + [j for e in JUGADORES for w in sorted(JUGADORES[e], reverse=True) for j in JUGADORES[e][w]]
    pruebas = [("Barça", "", "¡Gol del Barça!")]
    for n in nombres:
        variantes = PRONUNCIACION.get(n, [n])
        for i, v in enumerate(variantes):
            marca = "" if len(variantes) == 1 else f"variante {i + 1} de {len(variantes)}"
            pruebas.append((n, marca, f"¡Paradón de {v}!" if n in porteros else f"¡Gol de {v}!"))
    token = token_ha()
    CACHE.mkdir(parents=True, exist_ok=True)
    tmp = TRABAJO / "prueba_nombres"
    tmp.mkdir(parents=True, exist_ok=True)
    trozos, lineas = [], []
    for i, (n, marca, texto) in enumerate(pruebas, 1):
        destino = tmp / f"{i:03}.mp3"
        preparar(voz(texto, token), destino, pausa=0.8)
        trozos.append(destino)
        lineas.append(f"{i:3}. {n:16} {texto:28} {marca}".rstrip())
        print(lineas[-1], flush=True)
    (tmp / "lista.txt").write_text("".join(f"file '{t}'\n" for t in trozos))
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i",
                    str(tmp / "lista.txt"), "-ar", "44100", "-ac", "1", "-b:a", "64k",
                    str(TRABAJO / "prueba_nombres.mp3")], check=True)
    (TRABAJO / "prueba_nombres.txt").write_text(
        "Prueba de nombres del locutor: orden de las frases en prueba_nombres.mp3\n"
        "(nombre real, lo que se le manda a la voz y, si hay duda, qué variante es)\n\n" + "\n".join(lineas) + "\n")
    print(len(pruebas), "frases en", TRABAJO / "prueba_nombres.mp3")


def main():
    if "--reparto" in sys.argv:
        for prob in (0.5, 0.65):
            for nuevos in (False, True):
                c = reparto(prob, nuevos)
                total = sum(c.values())
                print(f"Madrid {prob:.0%}, {'con' if nuevos else 'sin'} los nuevos: {total:.1f} goles por partida")
                print("   ", ", ".join(f"{k} {v / total:.0%}" for k, v in sorted(c.items(), key=lambda x: -x[1])))
        return
    if "--prueba-nombres" in sys.argv:
        prueba_nombres()
        return
    lista = frases()
    if "--solo-textos" in sys.argv:
        for n, t, h in lista:
            print(f"{n:28} {t}" + (f"   [voz: {h}]" if h != t else ""))
        print(len(lista), "frases,", len({h for _, _, h in lista}), "voces distintas")
        return
    token = token_ha()
    CACHE.mkdir(parents=True, exist_ok=True)
    SALIDA.mkdir(parents=True, exist_ok=True)
    for i, (nombre, texto, dicho) in enumerate(lista, 1):
        preparar(voz(dicho, token), SALIDA / f"{nombre}.mp3")
        print(f"[{i}/{len(lista)}] {nombre}: {texto}", flush=True)
    (SALIDA / "locutor.json").write_text(json.dumps({"cuantos": CUANTOS, "frases": {n: t for n, t, _ in lista}},
                                                    ensure_ascii=False, indent=1))
    print(len(lista), "locuciones en", SALIDA)


if __name__ == "__main__":
    main()
