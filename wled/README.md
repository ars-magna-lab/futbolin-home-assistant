# Presets de WLED de las tiras

Presets del controlador WLED (probado con WLED 16.0.1 en un Gledopto GL-C-015WL-M) que activa el ESP32 en cada momento de la partida (`esphome/futbolin.yaml`, scripts `luz*`).

- `generar_presets.py`: genera `presets.json`. **Los presets se cambian ahí, no a mano.**
- `presets.json`: el fichero que se carga en WLED.
- `cargar_presets.py`: lo sube a WLED, con copia previa de los presets que haya. Solo usa la biblioteca estándar de Python.

## Solo efectos de luz

- **No hay marcador en las tiras**: está en la tablet.
- **Solo efectos puntuales**: las tiras gastan demasiado para ir encendidas con batería. Durante la partida van **apagadas**. Se encienden unos segundos con cada gol, al llegar a bola de partido y en la victoria, y vuelven solas a apagarse. **La buena** es la excepción: su efecto sigue hasta el gol que decide.
- **Piloto**: en reposo solo queda un píxel tenue por tira, para ver que el interruptor general está encendido.
- **Fallos**: lo único que se queda encendido es el aviso rojo, mientras dura el fallo.
- **Consumo**: pon el limitador de corriente de WLED (Config → LED Preferences) a unos 1500 mA como red de seguridad.

Cada preset lleva **2 segmentos, uno por tira** («Tira A» 0–28 y «Tira B» 28–56), con el mismo efecto en las dos. HA ve 2 segmentos.

## Presets

Colores del dashboard: Madrid blanco cálido y oro, Barça azul y grana. «Brillo» es el general del preset (0–255).

| ID | Nombre | Qué hace | Brillo |
|---|---|---|---|
| 1 | `reposo` | Piloto: un píxel blanco muy cálido en el extremo del píxel 0 de cada tira | 60 |
| 2 | `juego` | Apagadas | — |
| 3 | `gol_a` | Playlist: `gol_a_ola` 2 s, `gol_a_fuegos` 1 s, y vuelve a `juego` | — |
| 4 | `gol_b` | Igual con el Barça | — |
| 5 | `bola_partido_a` | Playlist: `bola_partido_a_efecto` 8 s y vuelve a `juego` | — |
| 6 | `la_buena` | Playlist: `la_buena_latido_1` a `_6`, 10 s cada uno, y se queda en `la_buena_latido_7` hasta el siguiente preset | — |
| 7 | `fin_a` | Playlist: ola y fuegos del gol (3 s), `fiesta_a` 10 s, y vuelve a `reposo` | — |
| 8 | `fin_b` | Igual con el Barça | — |
| 9 | `aviso` | Rojo fijo (atasco con la partida en juego o autotest fallido), hasta que se resuelve | 50 |
| 10 | `bola_partido_b` | Como el 5, con el Barça | — |
| 11 | `gol_a_ola` | Ola blanca (*Running*) que cruza el campo hacia la portería del Barça | 150 |
| 12 | `gol_b_ola` | Ola azul hacia la portería del Madrid | 150 |
| 13 | `gol_a_fuegos` | Fuegos artificiales blanco y oro | 150 |
| 14 | `gol_b_fuegos` | Fuegos azul y grana | 150 |
| 15 | `fiesta_a` | Fuegos blanco y oro, más tranquilos | 130 |
| 16 | `fiesta_b` | Fuegos azul y grana | 130 |
| 17 | `bola_partido_a_efecto` | Las tiras respiran en blanco | 60 |
| 18 | `bola_partido_b_efecto` | Las tiras respiran en azul | 60 |
| 19–24 | `la_buena_latido_1` a `_6` | Latido en oro (*Heartbeat*): 48, 52, 56, 60, 64 y 68 pulsaciones por minuto | 60 |
| 25 | `la_buena_latido_7` | Igual, 71 pulsaciones por minuto (el máximo del efecto) | 60 |

Del 11 al 25 son pasos de las playlists: el ESP32 no los manda directamente.

Qué manda el ESP32 (`esphome/futbolin.h`, `preset_fase` y `preset_gol`):

| Momento | Preset |
|---|---|
| Arranque, vuelta de la WiFi, anular partida, partida terminada (tras la fiesta) | 1 `reposo` |
| Nueva partida | 2 `juego` |
| Gol (de las barreras o +1 de HA) | 3 / 4; si deja bola de partido o la buena, 3,5 s después el 5, 10 o 6 |
| Gol que gana | 7 / 8 |
| −1 que cambia la fase | El de la nueva fase |
| Atasco con partida en juego, autotest fallido | 9 hasta que se resuelve |
| `switch.futbolin_efectos_luz` apagado (el interruptor de luces del dashboard) | `{"on": false}` al apagarlo, y después nada (las tiras quedan para HA) |
| Batería por debajo de `number.futbolin_luces_bateria_minima` (20 % por defecto) 60 s seguidos | `{"on": false}` y nada más hasta que el % sube al mínimo + 20; entonces, el de la fase. `binary_sensor.futbolin_luces_cortadas_por_bateria` encendido mientras tanto. No se aplica en modo enchufado ni sin lectura de batería |

Si WLED no responde, el gol se cuenta igual y solo queda un aviso en el log del ESP32.

## Ajustar al montaje

Se cambia en `generar_presets.py` (arriba, «Montaje») y se regenera con `python3 wled/generar_presets.py`:

1. **Píxeles de cada tira** (`LONGITUD`, o `--tira-a` / `--tira-b`): en el original, 28 + 28 (WS2811 de 12 V, 60 LED/m: un píxel cada 3 LEDs). Tienen que cuadrar con las salidas de WLED.
2. **Qué extremo da a qué portería**: `PORTERIA_A_EN_PIXEL_0 = True` si el píxel 0 de las tiras está en el extremo de la portería del Madrid. Solo afecta a la dirección de las olas: la del gol tiene que ir hacia la portería contraria a la de quien marca.
3. **Sentido de cada tira**: las dos tienen que tener el píxel 0 en el mismo extremo del campo. Si una está montada al revés, se corrige con **Reverse** en la salida de esa tira (Config → LED Preferences), no en los presets. Los presets solo usan `rev` en la ola del gol, para dirigirla.

El orden de color (en el original, BRG) va en la configuración de LED de WLED; los presets no lo tocan y usan colores RGB normales. En el original, cada tira va a una salida del controlador (GPIO 16 y GPIO 2), con dos segmentos (0–28 y 28–56).

## Cargar y probar

1. Carga:

   ```
   python3 wled/cargar_presets.py --ip <ip-del-wled>
   ```

   (o con la variable de entorno `WLED_IP`). Guarda antes los presets actuales en `wled/copias/` (no se sube al repo), enseña lo que va a subir y pide confirmación (`--si` para no preguntar). Sustituye **todos** los presets del WLED. Para volver atrás: `--fichero wled/copias/presets-<fecha>.json`. Si WLED tiene puesto un PIN de ajustes, quítalo antes o la subida falla.
2. Prueba cada uno desde el ordenador, como hará el ESP32:

   ```
   curl -X POST http://<ip-del-wled>/json/state -H 'Content-Type: application/json' -d '{"ps":3}'
   ```

   - Con el 3 y el 4, comprueba que la ola va hacia la portería contraria a la de quien marca y que a los 3 s se apagan.
   - Con el 6, que cada color sale de la portería de su equipo (si no, revisa `PORTERIA_A_EN_PIXEL_0`).
   - Con el 7 y el 8, que acaban en el piloto.
3. En **Config → LED Preferences**, pon como preset de arranque el 1 (`reposo`), para que el piloto salga aunque el ESP32 tarde.
4. Mide el consumo (corriente en el bus de 12 V) en `reposo`, `gol_a_ola`, `gol_a_fuegos`, `la_buena_duelo` y `fiesta_a`, y ajusta los brillos si hace falta.
