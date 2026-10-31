# Home Assistant: paquete, dashboard y voz

Home Assistant **no lleva la partida**: la lleva el ESP32 (`esphome/`). HA la muestra en un dashboard pensado para una tablet junto al futbolín, la controla con botones y por voz, y pone la música y el locutor. Si HA se cae, el futbolín sigue contando y al volver el marcador sale bien.

| Qué | Fichero | En HA |
|---|---|---|
| Orden de los goles, último gol (animación y locutor), latido del futbolín, frases de voz, música y tablet | `packages/futbolin.yaml` | `/config/packages/` |
| Simulación y sensores «Futbolín marcador» que leen el dashboard y la voz | `packages/futbolin_simulacion.yaml` | `/config/packages/` |
| Dashboard del marcador (vistas «Marcador» y «Depuración») | `dashboards/futbolin.yaml` | `/futbolin-marcador` |
| Escudos, tipografía y sonidos | `www/futbolin/` | `/config/www/futbolin/` → `/local/futbolin/` |

## Requisitos

- Home Assistant reciente (2025 o posterior: usa la sintaxis `triggers:` / `actions:` y plantillas con disparadores).
- El ESP32 del futbolín dado de alta con la integración de **ESPHome** (dispositivo `futbolin`; las entidades quedan como `*.futbolin_*`, ver `docs/README.md`). Si el ESP32 está en otra red o VLAN y el mDNS no llega, añádelo a mano por `IP:6053`.
- **button-card** (HACS, frontend): todo el marcador es una `button-card` con HTML propio.
- Opcional: **kiosk-mode** (HACS) para quitar la cabecera en la tablet.
- Opcional: la integración de **WLED** con el controlador de las tiras. El dashboard espera `light.futbolin_tiras` (y los segmentos `light.futbolin_tiras_tira_a` / `_b`): pon «Futbolín tiras» como nombre del dispositivo en HA o cambia las entidades en el dashboard.
- Opcional: **Assist** con una pipeline en español para la voz.

## Instalación

1. **Paquetes**: activa los paquetes en `configuration.yaml` si no lo están:

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

   y copia los dos ficheros de `packages/` a `/config/packages/`. Reinicia HA (o recarga plantillas, scripts, `input_boolean`, `input_number` y automatizaciones).
2. **Ficheros estáticos**: copia `www/futbolin/` a `/config/www/futbolin/` y añade la tipografía, que no va en el repo (Big Shoulders Display, licencia SIL OFL):

   ```
   curl -L -o /config/www/futbolin/big-shoulders-display.woff2 \
     "https://cdn.jsdelivr.net/fontsource/fonts/big-shoulders-display:vf@latest/latin-wght-normal.woff2"
   ```

3. **Recurso CSS**: en Ajustes → Paneles → Recursos, añade `/local/futbolin/fuentes.css` como hoja de estilos (un `@font-face` dentro de la tarjeta no funciona por el shadow DOM).
4. **Sonidos**: genera las locuciones con `locutor/` y cópialas a `/config/www/futbolin/sonidos/locutor/`. `silencio.mp3` ya va en `www/futbolin/sonidos/`. Los sonidos de reserva (`gol_a.mp3`…) son opcionales; ver `locutor/README.md`.
5. **Dashboard**: crea un panel nuevo («Desde cero») con la URL `futbolin-marcador`, ábrelo, edítalo → «Editor de configuración en bruto» y pega `dashboards/futbolin.yaml`. También vale en modo YAML:

   ```yaml
   lovelace:
     dashboards:
       futbolin-marcador:
         mode: yaml
         title: Futbolín
         icon: mdi:soccer
         filename: dashboards/futbolin.yaml
   ```

## Qué hay que adaptar

Los nombres de equipo, escudos y colores (Real Madrid y Barcelona) están en el dashboard, en las frases de voz y en el locutor. Además, el paquete usa entidades de ejemplo de la tablet y de la música:

| Entidad de ejemplo | Qué es | Dónde |
|---|---|---|
| `sensor.tablet_current_page`, `select.tablet_dashboard_view`, `switch.tablet_screensaver`, `light.tablet_screen`, `button.tablet_bring_to_front`, `esphome.ks_tablet_launch_app` | La tablet con Kiosk Satellite (app Android que se integra con ESPHome) o similar: página actual, dashboard que enseña, salvapantallas, pantalla, traerla al frente y abrir una app | `packages/futbolin.yaml` |
| `lovelace/0` | La página «de siempre» a la que vuelve la tablet al cerrar el marcador | `script.futbolin_cerrar_marcador` |
| `media_player.spotify` | La integración de Spotify | Paquete y dashboard |
| `Tablet` | El nombre de la tablet en Spotify Connect, como expresión regular | Variable `tablet` del paquete y `musica` del dashboard |
| `spotify:playlist:CAMBIA_POR_EL_ID_DE_TU_LISTA` | La lista de las partidas | `script.futbolin_musica` |
| `tablet` (usuario) | El usuario de HA de la tablet, para kiosk-mode | Cabecera del dashboard |

Si no usas tablet con control remoto o música, quita las automatizaciones `futbolin_pantalla` y `futbolin_musica_partida`, los scripts `futbolin_musica` y `futbolin_cerrar_marcador`, las acciones de la tablet de `futbolin_encendido` y `futbolin_voz`, y los botones `musica` y `salir` del dashboard.

## Cómo funciona

- **Marcador**: dígitos de matriz de puntos 8 × 13, la columna de las 11 bolas con el orden de los goles, animación de «¡GOL!» con cualquier gol que sume (barreras, +1 del dashboard o voz), cartel de «la buena» y pantalla del ganador. Todo es una sola `button-card` de 1280 × 800 que se escala a la ventana; cada parte que cambia por su cuenta va en su propio campo para que las animaciones no se reinicien.
- **«Nueva» y «Anular»** piden confirmación para no borrar la partida sin querer.
- **Simulación**: el botón «Simular» de la barra superior prueba el marcador, el locutor y la voz con el futbolín apagado (`futbolin_simulacion.yaml`). Todo lo que pinta el dashboard sale de los sensores `sensor.futbolin_marcador_a` / `_b` / `_fase`, que son los del ESP32 o los simulados, y todas las acciones pasan por `script.futbolin_accion`.
- **Apagado**: al cortar la corriente, la API de ESPHome tarda unos 90 s en dar el ESP32 por perdido. El ESP32 publica su tiempo encendido cada 5 s y `binary_sensor.futbolin_vivo` lo usa de latido: el dashboard enseña «Futbolín apagado» en unos 15 s.
- **Al encender el futbolín** (`futbolin_encendido`), el marcador sale solo en la tablet y, si no hay partida, empieza una (con la presentación del locutor).
- **Pantalla**: con el marcador abierto la tablet no se apaga (`futbolin_pantalla`).
- **Recordatorios** (`notify.notify`): apagar el futbolín si lleva 30 min encendido sin goles ni cortes de haz (se repite cada 30 min; no en modo enchufado). Cargar las baterías: al entrar en ahorro (por debajo del 20 % el ESP32 apaga las tiras y se sigue jugando; también sale en el marcador), al llegar al 0 %, al apagarlo por debajo del 40 %, y a los 14 días sin encenderlo (60 si quedó por encima del 80 %), repetido cada semana.
- **Música**: suena al empezar cada partida (si no se ha quitado), en aleatorio y sin empezar siempre por la misma canción, sigue entre partidas y se para al apagar el futbolín o al cerrar el marcador. Mientras habla el locutor, Android la baja; el truco está explicado en `locutor/README.md`.
- **Sonidos y locutor**: los reproduce el propio dashboard (`<audio>` y Web Audio), así que solo suenan con el marcador abierto. El momento de cada gol lo calcula la plantilla `sensor.futbolin_ultimo_gol` (atributo `locutor`).

## Voz

Las frases están en el propio paquete, como **disparadores de conversación** de la automatización `futbolin_voz` (no hace falta un fichero de `custom_sentences`). Con «Preferir el control local» activado en la pipeline de Assist se resuelven en local antes de llamar a un LLM, y no hace falta exponer ninguna entidad del futbolín a Assist.

| Frase | Acción |
|---|---|
| «nueva partida», «empezamos», «otra partida», «echamos una» | Nueva partida y pone el marcador en la tablet |
| «gol del Madrid», «suma uno al Real Madrid», «gol de los blancos» | +1 al equipo A |
| «gol del Barça», «suma uno al Barcelona», «gol de los culés» | +1 al equipo B |
| «quita un gol al Madrid», «ese no vale el del Madrid», «resta uno al Madrid» | −1 al equipo A |
| (lo mismo con el Barça) | −1 al equipo B |
| «anula la partida», «cancela la partida» | Anula la partida |
| «¿cómo vamos?», «¿cómo va la partida?», «¿cuál es el marcador?» | Responde con el marcador y la fase |
| «abre el marcador», «cierra el marcador» | Pone el marcador como página de la tablet, o vuelve a la de siempre |
| «pon la música», «quita la música» | Música de las partidas |

Con el futbolín apagado (y sin simulación), las frases de partida responden «El futbolín está apagado».

## Entidades propias de HA

| Entidad | Valores | Notas |
|---|---|---|
| `sensor.futbolin_marcador_a` / `_b` / `_fase` | Como los del ESP32 | Los del ESP32 o los simulados; no disponibles con el futbolín apagado |
| `sensor.futbolin_secuencia` | `-`, `a`, `ab`, `abba`… | Orden de los goles, para la columna de las 11 bolas. Se deduce de cómo cambian los totales; si no cuadra, se rehace con ellos |
| `sensor.futbolin_ultimo_gol` | `a`, `b` | Último gol que ha sumado uno. Atributos: `momento` (lanza la animación), `fase` (la que deja ese gol, elige el sonido de reserva) y `locutor` (la locución) |
| `sensor.futbolin_inicio` | fecha y hora | Inicio de la última partida, para la presentación del locutor (evento `futbolin_partida_nueva`) |
| `binary_sensor.futbolin_vivo` | on/off | Latido del ESP32 |
| `input_boolean.futbolin_simulacion`, `futbolin_sim_partida`, `input_number.futbolin_sim_goles_a` / `_b` | | Simulación |
| `input_boolean.futbolin_musica` | on/off | Si suena música en las partidas |
| `input_button.futbolin_musica_boton` | | El botón de la música del marcador: recargar Spotify requiere administrador y lo hace una automatización |
| `input_number.futbolin_bateria_recordada`, `input_datetime.futbolin_visto`, `input_datetime.futbolin_ultima_actividad` | | Último %, última vez encendido y última actividad, para los recordatorios |
| `script.futbolin_accion` | | `nueva`, `anular`, `gol_a_mas`, `gol_a_menos`, `gol_b_mas`, `gol_b_menos` |
| `script.futbolin_musica`, `script.futbolin_cerrar_marcador` | | Música y botón «Salir» |
