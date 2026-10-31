# Informe técnico · DSS de priorización de atracciones turísticas

**INF-8239 Ciencia de Datos II · UASD · Trabajo final · Tema 31 (Destinos turísticos) · Modalidad B (DSS)**
Equipo: Raimi De Jesús, Mario, Victoria y Alexis · Octubre 2026

## 1. Problema, decisor y alcance

Un **planificador de viajes** debe decidir qué atracciones priorizar para un viajero en Bali, Malang o Yogyakarta,
según el contexto del viaje (modo: pareja, familia, amigos, solo o negocios; origen) y sus intereses. El DSS
entrega una lista priorizada con explicación, reglas explícitas, alternativas visibles y un estado
(GO, REVISIÓN, ABSTENCIÓN o DETENIDO) que indica cuándo debe intervenir el humano. No decide por el planificador.

Alcance comprometido para 4 integrantes: baseline + 2 modelos, ≥ 8 pruebas (se entregan 17), documentación,
demostración y RACI (`docs/RACI.md`).

## 2. Datos (responsable: Raimi)

Tourism Dataset (Huda, 2023; Mendeley Data, DOI 10.17632/h58s544674.1): 52.930 visitas de 33.530 usuarios a 30
atracciones (17 tipos) de TripAdvisor, 2013–2022. Se comparó antes con el dataset *Travel & Tourism* de Kaggle, que
se descartó por tener un solo viaje por cliente, ningún atributo de contenido y señales de ser sintético.

- **Contrato de datos** (`data.py`): columnas, rangos, llaves foráneas y nulos. Hallazgo: `Item.AttractionCityId` no
  es llave de `City` (apunta a Douala, Camerún); se mapea por nombres a Bali, Malang y Yogyakarta.
- **Auditoría** (`reports/data_audit.json`): popularidad muy concentrada (28 a 13.198 visitas por atracción), Bali
  domina, calificaciones sesgadas al alza (79 % son 4 o 5), muy pocos datos desde 2020.
- **Partición sin fuga:** temporal global. Entrenamiento ≤ dic-2017, validación 2018 (ajuste de pesos), prueba
  ≥ ene-2019. El modelo final se reentrena con 2013–2018 y se evalúa una sola vez en prueba.
- **Unidad de evaluación:** "viaje" = visitas de un usuario a una ciudad con un modo de viaje en el periodo. Objetivo:
  atracciones del viaje que no estaban en su historial. 4.731 viajes de prueba; solo 639 (14 %) de usuarios con
  historial.

## 3. Modelos (responsable: Mario)

| Modelo | Idea | Contenido | Contexto |
|---|---|---|---|
| Baseline | Atracciones más visitadas de la ciudad | No | No |
| M1 · Contexto | Popularidad suavizada por modo de viaje (60 %) y continente (40 %) | No | Sí |
| M2 · Híbrido | 0,7 · contexto + 0,3 · afinidad de tipo y familia temática + 0,0 · calidad | Sí | Sí |

Los pesos de M2 se eligieron en validación 2018 entre 7 combinaciones por NDCG@3 (`reports/tuning_validation.csv`).
Dar más peso a contenido o calidad aumenta la cobertura (hasta 0,87) pero baja NDCG; se priorizó la calidad del
orden.

## 4. Evaluación (responsable: Victoria)

### 4.1 Resultados en prueba (4.731 viajes)

| Modelo | P@3 | Hit@3 | NDCG@3 | Cob@3 | P@5 | Hit@5 | NDCG@5 | Cob@5 | Sesgo pop. |
|---|---|---|---|---|---|---|---|---|---|
| Baseline | **0,270** | **0,732** | 0,553 | 0,57 | 0,178 | 0,791 | 0,580 | 0,70 | 0,939 |
| M1 | 0,266 | 0,720 | 0,590 | 0,67 | 0,182 | 0,806 | 0,629 | 0,83 | 0,926 |
| M2 | 0,266 | 0,721 | **0,590** | **0,80** | **0,182** | **0,809** | **0,630** | **0,97** | **0,922** |

Diferencias M2 − baseline con IC 95 % (bootstrap pareado): NDCG@3 **+0,037 [0,032; 0,043]**; Hit@3 **−0,011
[−0,018; −0,004]**; Precision@3 −0,003 [−0,006; −0,001].

**Lectura:** el baseline **gana** en acierto con k = 3 por ~1 punto (diferencia real, pero pequeña). El híbrido pone
antes la atracción correcta (NDCG), cubre 24 de 30 atracciones en vez de 17 y gana en todas las métricas con k = 5.
Con un catálogo de 10 atracciones por ciudad y una popularidad tan concentrada, recomendar "lo famoso" es difícil de
superar: es un hallazgo, no un error.

### 4.2 Subgrupos y errores

- **Con historial (n = 639):** M2 mejora Hit@3 de 0,654 a 0,673. El contenido aporta cuando existe perfil.
- **Sin historial (n = 4.092):** el contenido no aplica y el baseline es mejor (0,744 frente a 0,728). Por eso el DSS
  se abstiene de personalizar y pide intereses.
- **Ciudades:** Yogyakarta (0,55) y Malang (0,68–0,70) rinden menos que Bali (0,73–0,74): menos evidencia.
- **Equidad (África, n = 120):** Hit@3 baja de 0,775 a 0,658. Diagnóstico por hipótesis
  (`scripts/diagnose_subgroup.py`): quitar el continente no cambia nada (0,658); la caída está en 66 viajes de
  parejas en Bali, donde el contexto cambia Waterbom por Tanah Lot, cuyas cuotas entre parejas varían mucho entre años
  (Tanah Lot 16 % en 2015 → 1,7 % en 2019). Una ventana reciente (2016–2018) apenas ayuda (0,675) y empeora NDCG
  (0,554). Conclusión: inestabilidad temporal del contexto, no estereotipo por origen; se documenta y se mitiga con
  revisión humana.
- **Errores más frecuentes** (`reports/errors_missed_attractions.csv`): Tegenungan Waterfall y las playas de Bali
  (Seminyak, Sanur, Nusa Dua, Kuta). Compiten entre sí por el mismo tipo; la regla de diversidad del DSS deja entrar
  solo una por lista.

### 4.3 Green AI

Los tres modelos entrenan en menos de 1,5 s en CPU, con menos de 24 MB de memoria pico, menos de 1,1 MB serializados
y menos de 1,1 ms por recomendación. No se justifica un modelo más pesado (factorización o redes): el catálogo es de
30 ítems y el 86 % de los viajes de prueba no tiene historial, problema que más capacidad no resuelve.

## 5. Reglas del DSS (responsable: Alexis)

| Regla | Umbral (`configs/dss.yml`) | Efecto |
|---|---|---|
| Cobertura | Ciudad ∈ {Bali, Malang, Yogyakarta} | Si no, **DETENIDO** y escalar |
| Filtros duros | Atracciones visitadas y tipos excluidos | Si no queda nada, **DETENIDO** |
| Diversidad | Máx. 1 atracción por tipo | Se relaja antes de entregar menos de k (con aviso) |
| Abstención | Sin historial ni intereses declarados | **ABSTENCIÓN**: lista general marcada |
| Evidencia del contexto | ≥ 30 visitas del modo en la ciudad | Si no, **REVISIÓN** |
| Evidencia de la atracción | ≥ 30 visitas | Si no, advertencia "evidencia limitada" y **REVISIÓN** |
| Empate | Diferencia < 0,02 entre el último elegido y el siguiente | **REVISIÓN**: decide el planificador |

Cada atracción se explica con sus componentes ("tipo «Waterfalls» (Naturaleza), que te interesa", "34 % de las
visitas de viajeros en familia en Malang", "calificación media 4,52/5 con 261 visitas"). Sobre los 4.731 viajes de
prueba: 100 % de las recomendaciones con explicación; estados ABSTENCIÓN 86 %, REVISIÓN 10 %, GO 4 %
(porque en la evaluación offline nadie declara intereses; en uso real el planificador los ingresa).

## 6. Aplicación (responsable: Alexis)

`uv run streamlit run app.py`: el planificador elige ciudad, modo, origen, intereses, tipos excluidos y k. La app
muestra el estado y su significado, las prioridades con su explicación, las advertencias, las alternativas no
priorizadas con sus componentes, la sección "qué representa y qué no permite concluir" y la evidencia del modelo.

## 7. Ética, riesgos y reproducibilidad

- Registro de 10 riesgos con control, responsable y evidencia (`docs/RISK_REGISTER.md`).
- Privacidad: usuarios anonimizados; el origen se usa solo a nivel continente, de forma opcional, y se audita.
- Licencia: uso académico, crudos no versionados, DOI citado.
- Reproducibilidad: `uv.lock`, configuración versionada, huellas SHA-256 de los datos, 17 pruebas y CI.

## 8. Conclusión accionable

Se recomienda **usar el DSS como apoyo** con M2 como motor de priorización, **siempre con revisión humana**, porque
ordena mejor, diversifica el catálogo y explica cada recomendación. A cambio, pierde ~1 punto de Hit@3 frente a la
popularidad. Para viajeros sin perfil, el DSS se abstiene de personalizar. No debe usarse fuera de las tres ciudades
ni para inferir precio, seguridad o accesibilidad.

## 9. Pregunta de defensa

> ¿Qué evidencia justifica priorizar opciones explicables según contexto y restricciones y qué condición obligaría a
> detener, abstener o escalar la recomendación?

**Evidencia:** en una prueba temporal no vista (2019–2022), el híbrido mejora NDCG@3 en +0,037 (IC 95 % que no
incluye 0), sube la cobertura de 57 % a 80 %, reduce el sesgo de popularidad y explica el 100 % de sus
recomendaciones. Es trazable desde los datos (huellas SHA-256) y la configuración versionada hasta cada explicación.
El baseline sigue siendo competitivo en Hit@3 y se muestra al lado.

**Detener o escalar:** ciudad fuera de cobertura; restricciones que eliminan todas las opciones; preguntas sobre
precio, seguridad o accesibilidad (no están en los datos). **Abstenerse:** viajero sin historial ni intereses.
**Revisión humana:** modo de viaje con menos de 30 visitas en la ciudad, atracciones con menos de 30 visitas,
empates o subgrupos con desempeño inferior al baseline (como parejas de África en Bali).
