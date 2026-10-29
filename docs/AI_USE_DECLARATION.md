# Declaración de uso de IA generativa

**Herramienta:** Claude (Anthropic), usada por Raimi De Jesús en octubre de 2026.

## Para qué se usó

| Fecha | Uso | Fragmentos afectados |
|---|---|---|
| 22–26 oct | Comparar temas y evaluar dos datasets candidatos (Kaggle *Travel & Tourism* frente a Mendeley *Tourism Dataset*) con análisis exploratorio y pruebas rápidas | Decisión de dataset (PDF de evaluación compartido con el equipo) |
| 28 oct | Generar el proyecto base: código de `src/tourism_dss/`, scripts, `app.py`, pruebas, `configs/dss.yml` y borradores de la documentación | Todo el repositorio inicial |
| 28 oct | Diagnóstico de la caída del subgrupo África | `scripts/diagnose_subgroup.py`, Model Card, informe |

## Prompts relevantes (resumen)

- "Analiza ese dataset y dime si cumple con los requisitos" (dataset de Kaggle propuesto por un integrante).
- "Nos decidimos por el Tourism Dataset de Mendeley; los integrantes son Mario, Victoria, Alexis y yo" (generación
  del proyecto base con reparto por módulos).

## Errores detectados y correcciones durante la generación

1. La tabla `City` no corresponde a `Item.AttractionCityId`: se detectó al auditar y se documentó el mapeo.
2. La primera explicación de la caída en África ("el componente de continente perjudica al grupo") **era incorrecta**:
   al probar la hipótesis (sin continente, África sigue en 0,658) se descartó y se reemplazó por el diagnóstico de
   deriva del contexto "parejas".
3. Una prueba de integración suponía que la primera recomendación coincidiría con los intereses declarados; con datos
   reales domina Bromo Tengger Semeru (Parques nacionales, misma familia temática). Se corrigió la prueba para
   exigir que al menos una de las tres coincida.
4. La primera versión de la evaluación tardaba ~7 min; se optimizó con caché de contexto (mismos resultados).

## Verificaciones humanas (cada integrante completa la suya antes de la entrega)

| Integrante | Módulo | Qué ejecutó, revisó o cambió | Errores encontrados |
|---|---|---|---|
| Raimi | Datos | _completar_ | _completar_ |
| Mario | Modelos | _completar_ | _completar_ |
| Victoria | Evaluación | _completar_ | _completar_ |
| Alexis | DSS y app | _completar_ | _completar_ |

Cada integrante declara que entiende, ejecutó y puede defender el código de su módulo.
