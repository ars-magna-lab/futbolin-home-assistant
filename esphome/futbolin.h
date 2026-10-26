// Barreras IR del futbolín: lectura por interrupción directa en el ESP32.
//
// La ISR apunta en microsegundos cuándo se tapa el haz y cuánto ha durado el corte al
// liberarse. El resto (validar, contar, publicar) lo hace futbolin.yaml desde
// un intervalo: aunque el bucle de ESPHome se retrase por la WiFi, el corte ya
// está medido y no se pierde.
//
//   GPIO 32 / 33  receptores A (Madrid) / B (Barcelona) (LOW = haz tapado), pull-up externo de 5,1 kΩ
//   GPIO 14 / 27  emisores A (Madrid) / B (Barcelona), alimentados por el propio pin (autotest)

#pragma once
#include <Arduino.h>

namespace futbolin {

struct Barrera {
  uint8_t pin_receptor;
  uint8_t pin_emisor;
  // escritos desde la ISR
  volatile uint32_t inicio_us;
  volatile uint32_t duracion_us;
  volatile bool tapado;
  volatile bool evento;
  volatile uint32_t solapados;  // cortes que llegan antes de leer el anterior
};

static Barrera barreras[2] = {
  {32, 14, 0, 0, false, false, 0},
  {33, 27, 0, 0, false, false, 0},
};

static void IRAM_ATTR isr_barrera(void *arg) {
  Barrera *b = static_cast<Barrera *>(arg);
  const bool tapado_ahora = digitalRead(b->pin_receptor) == LOW;
  const uint32_t ahora = micros();
  if (tapado_ahora && !b->tapado) {
    b->inicio_us = ahora;
    b->tapado = true;
  } else if (!tapado_ahora && b->tapado) {
    if (b->evento) b->solapados++;
    b->duracion_us = ahora - b->inicio_us;
    b->tapado = false;
    b->evento = true;
  }
}

static void emisores(bool encendidos) {
  for (auto &b : barreras) digitalWrite(b.pin_emisor, encendidos ? HIGH : LOW);
}

static bool ve_tapado(int i) { return digitalRead(barreras[i].pin_receptor) == LOW; }

// Pone el estado de la ISR al día con lo que se ve ahora y olvida el evento
// pendiente (tras el autotest, que apaga los emisores a propósito).
static void sincronizar() {
  for (auto &b : barreras) {
    noInterrupts();
    b.tapado = digitalRead(b.pin_receptor) == LOW;
    b.inicio_us = micros();
    b.evento = false;
    interrupts();
  }
}

static void iniciar() {
  for (auto &b : barreras) {
    pinMode(b.pin_emisor, OUTPUT);
    digitalWrite(b.pin_emisor, HIGH);
    pinMode(b.pin_receptor, INPUT_PULLUP);
  }
  delay(20);
  sincronizar();
  for (auto &b : barreras)
    attachInterruptArg(digitalPinToInterrupt(b.pin_receptor), isr_barrera, &b, CHANGE);
}

// Devuelve true y la duración si hay un corte terminado sin leer.
static bool leer_corte(int i, uint32_t &duracion_us) {
  Barrera &b = barreras[i];
  if (!b.evento) return false;
  noInterrupts();
  duracion_us = b.duracion_us;
  b.evento = false;
  interrupts();
  return true;
}

// Milisegundos que lleva tapado el haz (0 si está libre).
static uint32_t tapado_ms(int i) {
  Barrera &b = barreras[i];
  if (!b.tapado) return 0;
  return (micros() - b.inicio_us) / 1000;
}

}  // namespace futbolin

// ---------- partida, diagnóstico y presets (sin entidades de ESPHome: eso va en el YAML) ----------
namespace futbolin {

enum Fase { REPOSO = 0, NORMAL, BOLA_PARTIDO_A, BOLA_PARTIDO_B, LA_BUENA, FIN_A, FIN_B };

static const char *nombre_fase(int f) {
  static const char *nombres[] = {"reposo", "normal", "bola_partido_a", "bola_partido_b",
                                  "la_buena", "fin_a", "fin_b"};
  return (f >= 0 && f <= FIN_B) ? nombres[f] : "reposo";
}

// La fase que corresponde a un marcador (las reglas de casa: a 6, 5-5 = la buena)
static int calcular_fase(int a, int b) {
  if (a >= 6) return FIN_A;
  if (b >= 6) return FIN_B;
  if (a == 5 && b == 5) return LA_BUENA;
  if (a == 5) return BOLA_PARTIDO_A;
  if (b == 5) return BOLA_PARTIDO_B;
  return NORMAL;
}

static bool cuenta_goles(int f) { return f != REPOSO && f != FIN_A && f != FIN_B; }

// Diagnóstico desde el arranque, por barrera
static uint32_t ultimo_valido_ms[2] = {0, 0};
static uint32_t ruido[2] = {0, 0};
static uint32_t rebotes[2] = {0, 0};
static uint32_t cortes = 0;  // número de corte, para el registro

}  // namespace futbolin

// ---------- presets de WLED (las tiras) ----------
// Los IDs son el contrato con wled/presets.json y docs/README.md.
namespace futbolin {

enum Preset {
  PRESET_REPOSO = 1,
  PRESET_JUEGO = 2,
  PRESET_GOL_A = 3,  // playlist: efecto de gol unos segundos y vuelve a juego
  PRESET_GOL_B = 4,
  PRESET_BOLA_PARTIDO_A = 5,
  PRESET_LA_BUENA = 6,
  PRESET_FIN_A = 7,  // playlist: gol, fiesta y vuelve a reposo (piloto)
  PRESET_FIN_B = 8,
  PRESET_AVISO = 9,
  PRESET_BOLA_PARTIDO_B = 10,
};

// El preset de una fase. Las tiras solo hacen efectos puntuales: juego las
// apaga, y bola de partido y la buena son playlists de unos segundos que acaban
// en juego. Con la partida terminada, reposo: la fiesta solo sale con el gol
// que la gana (preset_gol).
static int preset_fase(int f) {
  switch (f) {
    case NORMAL: return PRESET_JUEGO;
    case BOLA_PARTIDO_A: return PRESET_BOLA_PARTIDO_A;
    case BOLA_PARTIDO_B: return PRESET_BOLA_PARTIDO_B;
    case LA_BUENA: return PRESET_LA_BUENA;
    default: return PRESET_REPOSO;  // reposo y partida terminada
  }
}

// El preset del gol de `equipo` (0 = A, 1 = B) que deja la fase `f`: si el gol
// gana la partida, la fiesta; si no, el efecto de gol.
static int preset_gol(int equipo, int f) {
  if (f == FIN_A) return PRESET_FIN_A;
  if (f == FIN_B) return PRESET_FIN_B;
  return equipo == 0 ? PRESET_GOL_A : PRESET_GOL_B;
}

}  // namespace futbolin
