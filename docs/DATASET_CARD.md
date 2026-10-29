# Dataset Card · Tourism Dataset (TripAdvisor Indonesia)

| Campo | Valor |
|---|---|
| Fuente | Huda, C. (2023). *Tourism Dataset*, Mendeley Data, V1, DOI 10.17632/h58s544674.1 |
| Origen | Experiencias publicadas en TripAdvisor, recolectadas por *crawling* (oct 2022 – ene 2023) y validadas con Google Maps por el autor |
| Licencia / uso | Investigación, no comercial; no se redistribuyen los crudos |
| Tablas | 9: Transaction, Item, Type, Mode, User, Continent, Region, Country, City |
| Volumen | 52.930 visitas · 33.530 usuarios · 30 atracciones (10 por ciudad) · 17 tipos |
| Periodo | ene-2013 a oct-2022 |
| Calificación | 1–5 (45 % son 5; 34 % son 4: escala sesgada al alza) |
| Contexto | Modo de viaje (Couples 41 %, Family 29 %, Friends 21 %, Solo 9 %, Business 1 %) y continente del usuario |

## Composición y cobertura

- **Ciudades:** Bali concentra la gran mayoría de visitas; Malang y Yogyakarta tienen mucha menos evidencia.
- **Popularidad muy concentrada:** de 28 a 13.198 visitas por atracción (mediana 379).
- **Usuarios:** 10.618 con 2 o más visitas; la mayoría tiene una sola (arranque en frío).
- **Visitas por año:** 2016 es el pico (12.823); 2020: 529, 2021: 35, 2022: 247 (efecto COVID).
- **Repeticiones:** 7.655 visitas repiten el par usuario–atracción. Cuentan para la popularidad; no se
  recomiendan atracciones ya visitadas.

## Preparación

- Contrato de datos (`validate_raw`, `validate_processed`): columnas, rangos (Rating 1–5, mes 1–12), llaves foráneas,
  nulos tras las uniones y ausencia de identificadores directos.
- **Corrección documentada:** `Item.AttractionCityId` no es llave de `City`; se mapea 1 = Bali, 2 = Malang,
  3 = Yogyakarta.
- Continente "-" o faltante → "Desconocido".
- Partición temporal global: entrenamiento ≤ dic-2017 (38.745), validación 2018 (7.461), prueba ≥ ene-2019 (6.724).

## Privacidad

Los usuarios están anonimizados (Id numérico). No hay nombres, correos ni teléfonos. El país y el continente de
origen son atributos potencialmente sensibles (proxy de nacionalidad): solo se usa el continente, de forma opcional,
y se audita por subgrupos.

## Limitaciones

Sesgo de selección (solo quien reseña en TripAdvisor, mayoritariamente en inglés), sin precios, horarios, clima,
accesibilidad ni seguridad; catálogo pequeño; datos de antes de 2020 en su mayoría.
