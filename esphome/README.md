# Firmware del ESP32 (ESPHome)

- `futbolin.yaml`: la partida, las entidades para Home Assistant y los efectos de luz en WLED.
- `futbolin.h`: lectura de las barreras por interrupción, reglas de juego y presets de WLED.
- `secrets.example.yaml`: las claves que necesita. Cópialo como `secrets.yaml` (no se sube al repo) y pon las tuyas.

## Grabar

La primera vez, por USB, desde esta carpeta:

```
cp secrets.example.yaml secrets.yaml   # y edítalo
esphome run futbolin.yaml --device /dev/ttyUSB0
```

Después, por WiFi (OTA) con `esphome run futbolin.yaml` o desde el ESPHome Device Builder de Home Assistant (copia los dos ficheros a `/config/esphome/`).

Para comprobar la configuración sin grabar: `esphome config futbolin.yaml`.

## Ajustes

Arriba de `futbolin.yaml`, en `substitutions`:

| Ajuste | Por defecto | Qué es |
|---|---|---|
| `duracion_minima_us` | 500 | Cortes más breves = ruido |
| `bloqueo_ms` | 400 | Tiempo mínimo entre dos goles del mismo carril |
| `atasco_ms` | 2000 | Haz tapado más de esto = atasco |
| `wled_timeout` | 500ms | Lo más que espera a WLED (los cortes no se pierden: los mide la interrupción) |
| `gol_luz_ms` | 3500 | Lo que dura el efecto de gol en WLED, con margen |
| `luces_bateria_ms` | 60000 | Tiempo por debajo del mínimo de batería antes de cortar las luces |
| `luces_histeresis` | 20 | % por encima del mínimo para que vuelvan |

La medida de la batería (`multiply` del sensor `bateria_voltios`) depende del divisor y del ADC de cada placa: ajústala comparando con un multímetro. La tabla de % es la del plomo en reposo y su 0 % son 12,2 V, la media carga de donde no conviene bajar; para otra química, cambia `tension[]` en el sensor `bateria`.

El ESP32 sirve también una web propia (`http://<ip-del-esp32>`) con las entidades y el log en directo, útil para depurar desde el móvil mientras se juega.

Pines, reglas y entidades: `docs/README.md`.
