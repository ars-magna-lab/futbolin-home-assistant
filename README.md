# Futbolín con Home Assistant

Un futbolín clásico (un Córdoba antiguo restaurado) que cuenta los goles solo, los canta con un locutor y celebra cada gol con luces, sin que por fuera se note nada.

> En preparación. Aquí irá la versión para compartir del proyecto: qué se ha hecho, cómo funciona y el código, sin los datos de la casa. La explicación con fotos y vídeo estará en la web.

## Qué hace

- **Cuenta los goles solo.** Una barrera infrarroja en cada carril de recogida de bolas detecta la bola al pasar. Sin taladrar la portería y sin nada que se vea por fuera.
- **Lleva la partida.** 11 bolas, gana quien llega a 6, y con 5-5 se juega «la buena». Un ESP32 con ESPHome sigue contando aunque se caigan la WiFi o Home Assistant.
- **Marcador en una tablet.** Dashboard de Home Assistant con aspecto de marcador de estadio: dígitos de matriz de puntos, la columna de las 11 bolas y animaciones de gol, «la buena» y victoria.
- **Locutor.** Cada gol se narra con una frase distinta y con jugadores reales, y cada partida empieza con una presentación del clásico. La música de fondo baja mientras habla.
- **Control por voz.** «Nueva partida», «gol del Madrid», «quita un gol al Barça»… con Assist, en local.
- **Luces.** Dos tiras LED con WLED hacen efectos puntuales: la ola del gol cruza el campo hacia la portería rival y hay fiesta al ganar. Se apagan solas si la batería baja.
- **A batería.** Sin cables mientras se juega. El aspecto exterior no cambia, salvo un interruptor discreto por debajo.

## Cómo está hecho

| Parte | Qué es |
|---|---|
| Sensores de gol | Barreras IR (break-beam) protegidas por dos cuñas de madera en cada carril |
| Cerebro | ESP32 con ESPHome: interrupciones, antirrebote, aviso de atasco y autotest al arrancar |
| Pantalla y voz | Home Assistant en una tablet, con un dashboard propio y Assist |
| Luces | Controlador Gledopto con WLED, dos tiras WS2811 de 12 V y presets lanzados por el ESP32 |
| Energía | Baterías de plomo de 12 V, convertidor a 5 V y medida de la batería en el ESP32 |

## Contenido del repositorio (en preparación)

- `esphome/`: firmware del ESP32.
- `homeassistant/`: paquete, dashboard del marcador y frases de voz.
- `wled/`: generador de los presets de luz.
- `locutor/`: generador de las locuciones.
- `docs/`: esquemas y diagramas.
