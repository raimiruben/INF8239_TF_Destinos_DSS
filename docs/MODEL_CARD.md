# Model Card · M2 Híbrido contenido + contexto (motor del DSS)

## Detalles

- **Tipo:** recomendador por puntaje lineal interpretable, sin aprendizaje profundo.
  `puntaje = 0,7 · contexto + 0,3 · contenido + 0,0 · calidad` (pesos elegidos en validación 2018 por NDCG@3).
  - *Contexto:* proporción suavizada de visitas a la atracción entre viajeros con el mismo modo de viaje (60 %) y
    continente de origen (40 %), con 50 pseudo-conteos hacia la popularidad de la ciudad.
  - *Contenido:* afinidad del perfil del viajero (intereses declarados o tipos visitados antes) con el tipo (70 %) y
    la familia temática (30 %) de la atracción.
  - *Calidad:* calificación media bayesiana (20 pseudo-conteos). Su peso óptimo en validación fue 0; se mantiene en
    la explicación.
- **Código:** `src/tourism_dss/models.py` · **Configuración:** `configs/dss.yml` · **Versión:** v1.0 (oct 2026).
- **Entrenamiento final:** visitas 2013–2018 (46.206).

## Uso previsto

Apoyar a un **planificador de viajes** a priorizar atracciones dentro de Bali, Malang o Yogyakarta, con explicación.
La decisión final es humana.

**Usos fuera de alcance:** decidir automáticamente sin revisión, ciudades distintas de las tres cubiertas, inferir
precio, seguridad, accesibilidad o clima, uso comercial de los datos, perfilar a personas por su origen.

## Evaluación (prueba temporal 2019–2022, 4.731 viajes)

| Métrica | Baseline | M1 contexto | M2 híbrido |
|---|---|---|---|
| Precision@3 | **0,270** | 0,266 | 0,266 |
| Hit@3 | **0,732** | 0,720 | 0,721 |
| NDCG@3 | 0,553 | 0,590 | **0,590** |
| Cobertura@3 | 0,57 | 0,67 | **0,80** |
| Precision@5 / Hit@5 | 0,178 / 0,791 | 0,182 / 0,806 | **0,182 / 0,809** |
| Cobertura@5 | 0,70 | 0,83 | **0,97** |
| Sesgo de popularidad (percentil medio, k = 3) | 0,939 | 0,926 | **0,922** |

Diferencia M2 − baseline (bootstrap pareado, 1.000 réplicas): NDCG@3 +0,037 [0,032; 0,043];
Hit@3 −0,011 [−0,018; −0,004]; Precision@3 −0,003 [−0,006; −0,001].

## Subgrupos (Hit@3, k = 3)

| Subgrupo | n | Baseline | M2 |
|---|---|---|---|
| Con historial | 639 | 0,654 | **0,673** |
| Sin historial | 4.092 | **0,744** | 0,728 |
| Familia | 1.605 | 0,823 | 0,825 |
| Negocios | 42 | 0,476 | 0,524 |
| África (origen) | 120 | **0,775** | 0,658 |
| Australia y Oceanía | 1.544 | 0,771 | **0,780** |
| Yogyakarta | 220 | 0,555 | 0,550 |
| Malang | 74 | **0,703** | 0,676 |

Los subgrupos con menos de 30 viajes no se interpretan. **Hallazgo principal: viajeros de África (n = 120).**
El diagnóstico (`scripts/diagnose_subgroup.py` → `reports/subgroup_diagnostic.json`) muestra que la caída **no se
debe al uso del continente**: sin ese componente África sigue en 0,658. Se concentra en 66 viajes de parejas en Bali
(0,742 → 0,530), donde el contexto "parejas" cambia Waterbom Bali por Tanah Lot Temple. Las preferencias de las
parejas son inestables entre años (Tanah Lot: 16 % en 2015 → 1,7 % en 2019; Waterbom: 14 % en 2013 → 0,5 % en 2018
→ 8 % en 2019). Entrenar solo con 2016–2018 mejora poco a África (0,675) y empeora NDCG@3 (0,554). Ninguna
mitigación de modelo probada mejora sin costo; la mitigación vigente es del DSS (alternativas visibles y revisión).

## Green AI

| Modelo | Entrenamiento | Memoria pico | Tamaño | Latencia |
|---|---|---|---|---|
| Baseline | 0,9 s | 10,9 MB | 340 KB | 0,3 ms |
| M1 | 0,8 s | 13,0 MB | 346 KB | 0,1 ms |
| M2 | 1,4 s | 23,9 MB | 1.067 KB | 1,1 ms |

CPU, sin GPU. Con 30 atracciones y 86 % de viajeros sin historial, un modelo más pesado (factorización o redes)
no se justifica: su costo crece y el problema dominante (arranque en frío) no se resuelve con más capacidad.

## Limitaciones y condiciones de uso

- El DSS se **abstiene de personalizar** si no hay historial ni intereses declarados.
- Pasa a **REVISIÓN** si el modo de viaje tiene menos de 30 visitas en la ciudad, si una atracción tiene menos de
  30 visitas o si hay empate técnico.
- **Retiro o reentrenamiento:** si se incorporan datos posteriores a 2022 y NDCG@3 del híbrido cae por debajo del
  baseline, o si algún subgrupo con 30 o más viajes queda más de 10 puntos de Hit@3 por debajo del baseline sin
  explicación. Trabajo futuro: ponderación temporal con decaimiento, ajustada en validación.
