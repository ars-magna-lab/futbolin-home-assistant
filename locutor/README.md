# Locutor y sonidos del marcador

Cada gol lo canta un locutor con una frase distinta y con jugadores reales, y al empezar cada partida presenta el clásico. Los sonidos los reproduce **el propio dashboard** en la tablet (solo suenan con el marcador abierto), así que no hace falta ningún altavoz conectado a Home Assistant.

Este directorio tiene los scripts que generan los MP3. **Los MP3 no están en el repo**: se generan con tu instalación de HA y tu motor de voz.

- `locutor.py`: genera las 348 locuciones del locutor (solo voz) y su índice.
- `mezcla.py`: genera los 8 sonidos de reserva (público, redoble y voz), que suenan si falta el locutor.

## Momentos

El paquete de HA calcula el momento de cada gol (atributo `locutor` de `sensor.futbolin_ultimo_gol`, con la secuencia de goles) y el dashboard elige una de sus frases al azar, sin repetir hasta gastarlas todas. Gana el primer momento que se cumple, en este orden:

| Momento | Cuándo | Frases |
|---|---|---|
| `goleada` | Gana 6-0 o 6-1 | 5 por marcador y equipo |
| `fin` | Gol que gana (6-2 a 6-5) | 4 por marcador y equipo |
| `buena` | 5-5 | 6 por equipo |
| `bola` | Bola de partido para quien marca (5-0 a 5-4) | 4 por marcador y equipo |
| `salva` | El rival tiene 5 y quien marca no gana todavía | 4 por equipo |
| `remontada` | Iba perdiendo de dos o más y este gol lo pone por delante | 8 por equipo |
| `empate` | Empata (1-1 a 4-4), con el marcador | 4 por marcador y equipo |
| `primero` | Primer gol del partido | 8 por equipo |
| `estreno` | Primer gol de quien llevaba 3 o más en contra | 4 por equipo |
| `escapa` | Se pone 3 por delante | 4 por equipo |
| `racha` | 3 o 4 goles seguidos (`racha_<e>_<3\|4>`) | 3 por número y equipo |
| `corta` | Corta una racha de 3 o más del rival | 4 por equipo |
| `recorta` | Marca quien pierde y sigue perdiendo | 6 por equipo |
| `desempata` | Rompe un empate (1-1 a 4-4) | 6 por equipo |
| `normal` | Cualquier otro gol; corto, sin marcador | 45 por equipo |
| `corto` | Ultracortas sin equipo («¡Pum!», «¡Para casa!»): sustituyen a la frase en 1 de cada 4 goles de `normal`, `desempata`, `recorta`, `escapa`, `racha` y `corta` | 10 |
| `inicio` | Al empezar la partida (de 9 a 12 s): presentación del clásico | 12 |

Las reglas exactas están en `momento()` de `locutor.py`, que es la misma lógica que la plantilla del paquete de HA. La presentación suena con cada «nueva partida» (dashboard, voz o al encender el futbolín): `script.futbolin_accion` lanza el evento `futbolin_partida_nueva`, que actualiza `sensor.futbolin_inicio`.

## Generar las locuciones

Necesitas Python 3, `ffmpeg` y una entidad TTS en Home Assistant. El original usa una integración de **OpenAI TTS** (entidad `tts.locutor`, voz «ballad») con un prompt de narrador deportivo español; vale cualquier otra que hable bien en español, aunque los nombres de la tabla `PRONUNCIACION` están pensados para esa voz.

1. Crea un token de larga duración en HA (tu perfil → Seguridad).
2. Revisa los textos sin gastar nada:

   ```
   python3 locutor/locutor.py --solo-textos
   ```

3. Genera:

   ```
   export HA_URL=http://<ip-de-ha>:8123
   export HA_TOKEN=<token>
   # opcional: LOCUTOR_MOTOR=tts.otra_voz LOCUTOR_VOZ=<voz>
   python3 locutor/locutor.py
   ```

   Deja los MP3 y el índice `locutor.json` en `locutor/trabajo/locutor/` (no se sube al repo). Las voces ya pedidas se guardan en `locutor/trabajo/voz/` y no se vuelven a pedir, así que repetirlo tras cambiar unas frases solo cuesta las nuevas.
4. Copia el contenido de `locutor/trabajo/locutor/` a `/config/www/futbolin/sonidos/locutor/` de Home Assistant (en el dashboard, `/local/futbolin/sonidos/locutor/`).

Otras opciones:

- `--prueba-nombres`: deja `trabajo/prueba_nombres.mp3` y `.txt` con «¡Gol de X!» por cada jugador tal como lo dirá la voz, para corregir `PRONUNCIACION`.
- `--reparto`: cuánto sale de media cada momento en una partida.

Para cambiar frases, equipos o jugadores, edita las listas de `locutor.py` (`EQUIPOS`, `JUGADORES`, `PRONUNCIACION` y las plantillas). **Si cambia cuántas frases hay de un momento, cambia también `CUANTOS` en el campo `sonido` del dashboard** (`homeassistant/dashboards/futbolin.yaml`), y el número de presentaciones (`inicio`). Si regeneras con los mismos nombres de fichero, sube el `?v=2` del dashboard para que la tablet no siga con los de la caché.

## Con música: el locutor la baja

Con música sonando en la tablet (por ejemplo Spotify), Android baja la música mientras habla el locutor y la sube al acabar. Lo hace solo si el sonido pide el foco de audio «temporal, se puede bajar», y Chromium (el WebView del navegador de la tablet) solo lo pide así para medios de **menos de 5 s**: con uno más largo pide el foco entero y la música **se pausa** y no vuelve.

El truco que usa el dashboard (`window.futbolinLocutor`, en el campo `sonido`):

1. Al empezar una locución suena `silencio.mp3` (1 s de silencio, incluido en `homeassistant/www/futbolin/sonidos/`) en bucle con un `<audio>`: dura menos de 5 s, así que Android baja la música.
2. La voz va por **Web Audio** (`AudioContext`), que no pide foco: su duración no importa.
3. Al acabar la voz, el `<audio>` del silencio se deshace (quitar `src` y `load()`). Con `pause()` solo, Chromium no suelta el foco y la música se queda baja.

## Sonidos de reserva

Suenan si falta el atributo `locutor` (por ejemplo, con un paquete antiguo). Van en `/config/www/futbolin/sonidos/`:

| Fichero | Cuándo | Contenido |
|---|---|---|
| `gol_a.mp3`, `gol_b.mp3` | Gol normal | Público y «¡Gooool del Madrid/Barça!» (3,6 s) |
| `gol_a_bola.mp3`, `gol_b_bola.mp3` | Gol que da bola de partido a quien marca | Lo anterior, redoble y «¡Bola de partido!» (7 s) |
| `gol_a_buena.mp3`, `gol_b_buena.mp3` | Gol que lleva al 5-5 | Gol, redoble en crescendo, «¡La buena!» y ovación (10 s) |
| `fin_a.mp3`, `fin_b.mp3` | Gol que gana | Ovación, gol y «¡Gana el Real Madrid/Barça!» (8 s) |

Cómo se generan:

1. Baja las fuentes de Wikimedia Commons a `<directorio>/fuentes/` como `publico.wav` y `redoble_largo.mp3` (ver créditos).
2. Genera las voces con cualquier TTS de HA (`POST /api/tts_get_url`) como `voz_gol_a.mp3`, `voz_gol_b.mp3`, `voz_bola.mp3`, `voz_buena.mp3`, `voz_fin_a.mp3` y `voz_fin_b.mp3` en `<directorio>/`. Textos: «¡Gooool del Madrid!», «¡Gooool del Barça!», «¡Bola de partido!», «¡La buena!», «¡Gana el Real Madrid!», «¡Gana el Barça!».
3. `python3 locutor/mezcla.py <directorio>`: deja los 8 MP3 en `<directorio>/salida/`.

### Créditos de las fuentes

- Público: [Arrowhead Stadium crowd noise](https://commons.wikimedia.org/wiki/File:Arrowhead_Stadium_crowd_noise.wav), de Kj1595, licencia CC BY-SA 4.0.
- Redoble: [Drum Roll – Concert Band – United States Air Force Band](https://commons.wikimedia.org/wiki/File:Drum_Roll_-_Concert_Band_-_United_States_Air_Force_Band.mp3), dominio público.
