# Registro de riesgos (hito 1)

Probabilidad e impacto en escala 1–4; prioridad = probabilidad × impacto.

| Id | Riesgo / escenario | Afectado | P | I | Prioridad | Control | Responsable | Evidencia |
|---|---|---|---|---|---|---|---|---|
| R01 | Sesgo de popularidad: siempre se recomiendan las mismas atracciones famosas de Bali | Viajeros, atracciones pequeñas | 4 | 3 | 12 | Métrica de cobertura y sesgo de popularidad; regla de diversidad (1 por tipo); componente de contenido | Victoria | `reports/comparison_test.csv` (cobertura 0,57 → 0,80) |
| R02 | Fuga temporal: usar visitas futuras para entrenar o ajustar | Validez de la evaluación | 3 | 4 | 12 | Partición global train ≤ 2017 / val 2018 / test ≥ 2019; ajuste solo en val | Raimi | `test_temporal_split_has_no_future_leakage` |
| R03 | Viajero sin perfil recibe una lista "personalizada" que no lo es | Viajero, planificador | 4 | 3 | 12 | Estado ABSTAIN y aviso; la app pide intereses | Alexis | `test_abstains_without_profile_and_explains_with_interests`; 86 % de viajes de prueba sin historial |
| R04 | Personalizar por contexto perjudica a un grupo con pocos datos (estereotipo por origen o contexto inestable) | Viajeros de África (120 viajes de prueba) | 3 | 3 | 9 | Suavizado; continente opcional; diagnóstico por hipótesis; alternativas no priorizadas visibles en la app | Victoria / Mario | `reports/subgroup_diagnostic.json` (África 0,775 → 0,658; causa: deriva del contexto "parejas", no el continente) |
| R05 | Llave de ciudad errónea en `Item` lleva a recomendar atracciones de otra ciudad | Planificador | 3 | 4 | 12 | Mapeo documentado y prueba de contrato | Raimi | `test_contract_accepts_valid_data_and_maps_cities` |
| R06 | Se interpreta el puntaje como probabilidad de disfrute o como información de precio, seguridad o accesibilidad | Viajero | 3 | 3 | 9 | Sección "qué no permite concluir" en la app y la Model Card | Alexis | `app.py` |
| R07 | Deriva: los datos terminan en 2022 (y casi no hay desde 2020) | Calidad futura | 3 | 3 | 9 | Advertencia en la app; condición de reentrenamiento/retiro en la Model Card | Victoria | `reports/data_audit.json` |
| R08 | Uso de los datos fuera de su licencia (comercial) | Equipo, autor | 2 | 3 | 6 | No versionar crudos; citar DOI; uso académico | Raimi | `data/README.md` |
| R09 | Contexto con poca evidencia (p. ej., negocios en Malang) produce ranking inestable | Planificador | 3 | 2 | 6 | Estado REVIEW si < 30 visitas del modo en la ciudad | Alexis | `test_low_evidence_context_requires_human_review` |
| R10 | Aporte individual no trazable (un solo integrante sube todo) | Nota individual del equipo | 3 | 4 | 12 | RACI, ramas y PR por persona, revisión cruzada | Raimi | `docs/PLAN_GIT.md`, historial de GitHub |
