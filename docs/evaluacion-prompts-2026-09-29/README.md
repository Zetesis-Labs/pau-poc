# Evaluación acotada de prompts · 29 de septiembre de 2026

## Alcance y método

Se compararon **cinco casos dirigidos** por fallos conocidos: dos preguntas `p6`, una rúbrica `r3` y dos solucionarios `s2`. Las cinco respuestas están en estado `completed`. Se usó `gpt-6-luna`, esfuerzo `high` y `ExtractorOpenAI(reintentos=0)`; `r3` y `s2` recibieron el mismo árbol `p5` que sus versiones anteriores. Cada llamada usó el PDF y la página inicial del registro anterior, identificados por ruta y SHA-256 en `fuentes.json`. El esquema siguió siendo `v3` para preguntas, `r1` para rúbrica y `s1` para soluciones.

La comparación se hizo contra las salidas `p4`/`p5`, `r2`/`s1`, los PDF completos en las páginas pertinentes y el constructor de banco en memoria para las preguntas. Se inspeccionaron visualmente las escalas de la rúbrica, las páginas manuscritas de la academia y los dos folios de soluciones del control positivo. Los cinco JSON nuevos se copiaron byte a byte a `evidencias/`, con huellas SHA-256 y uso en `evidencias/manifest.json`, porque `pipeline/salida/` está ignorado por Git. No se reescribieron salidas antiguas, fuentes ni `datos/`.

Los prompts usados fueron `p6` SHA-256 `aa8d0b2304c3ca48412346f968bce2a4fd8d3660ecadafbbc96b9a40911a5e6f`, `r3` `5992c80711a130d4e6de516500b1a63d7bc1621195ccefd760b5ae754ad51444` y `s2` `d86ac9b5ae0bf19bf63e1a2df87ca6dc2f72ea620252c30881dbc299f9089515`. El script `ejecutar.py` restringe los casos, desactiva reintentos y abre cada destino de forma exclusiva. Hubo un intento inicial desde el sandbox que falló con `APIConnectionError` sin respuesta ni uso; su archivo de error se retiró. Las cinco respuestas `completed` se obtuvieron fuera del sandbox. No se calcula precio monetario sin una tarifa comprobada.

| Caso | Entrada | Salida | Total | Segundos |
| --- | ---: | ---: | ---: | ---: |
| `p6` · `fda5ea13b6c5` | 19.432 | 12.053 | 31.485 | 89,0 |
| `p6` · `0b7e227a5499` | 16.195 | 13.931 | 30.126 | 89,7 |
| `r3` · `070c3795d83c` | 16.202 | 8.474 | 24.676 | 55,9 |
| `s2` · academia `25fcf7208b8f` | 26.463 | 14.074 | 40.537 | 115,7 |
| `s2` · oficial `1bc800a06e3b` | 5.669 | 7.142 | 12.811 | 56,4 |
| **Total** | **83.961** | **55.674** | **139.635** | |

## Preguntas `p6`

El PDF original imprime seis preguntas, cada una con cuatro cuestiones, en valenciano (pp. 1–2) y castellano (pp. 3–4). El baremo también declara tres preguntas y cuatro cuestiones por ejercicio. El resultado `p6` tiene dos opciones, seis preguntas y 24 apartados, todos hijos directos de su pregunta correspondiente; cada pregunta tiene cuatro. `p4` también tenía esa jerarquía, mientras que `p5` colocaba los 24 apartados bajo las opciones. El validador actual da cero hallazgos para `p6` y el constructor de banco retiene seis preguntas con cuatro apartados cada una; por tanto, **corrige la pérdida estructural concreta de `p5` en este caso**.

`p6` conserva incidencias sobre las figuras A2, A3 y B1 citadas pero ausentes del PDF, y sobre la falta de tilde en «cual sería» del impreso castellano. No generó recortes. Se cotejaron las cuatro páginas para comprobar las 24 marcas de cuestión y su relación con las preguntas.

En `0b7e227a5499`, `p5` había perdido la pregunta 4.2 entera. El PDF, página 2, contiene 4.1 y 4.2 con dos apartados cada una y ordena elegir una de las dos preguntas. `p6` conserva esa regla en un bloque padre, representa 4.2 con su sistema de tres ecuaciones y sus apartados a/b, y mantiene también 4.1 y 5.1/5.2. El constructor de banco en memoria da siete preguntas y 16 apartados contando niveles anidados; publica 4.2 con a/b. La página 7 de orientaciones se clasifica fuera del enunciado. Queda un aviso leve de formato LaTeX (`coma-decimal-sin-llaves` en `[0,2\pi]`) sin efecto sobre esta recuperación.

## Rúbrica `r3`

El PDF oficial de `070c3795d83c`, páginas 2 y 4, ofrece para las imágenes 2.2 y 2.3 **una de cuatro bandas**: 0, 0–1,5, 1,5–3,5 o 3,5–5 puntos. `r2` convertía cada escala en cuatro elementos de `desglose` cuyos valores sumaban 10, aunque el máximo es 5. `r3` conserva las cuatro bandas completas en `criterios`, fija 5 puntos y deja `desglose=[]` en ambos nodos `n5` y `n13`. También conserva las tablas graduadas de `n4` y `n12` como tablas en criterios, sin convertirlas en partidas acumulables. Hay nueve entradas, igual que en `r2`, y cero hallazgos automáticos. Los PNG de lectura `rubrica-070c3795d83c-p2.png` y `rubrica-070c3795d83c-p4.png` muestran las dos escalas originales.

## Soluciones `s2`

En el manuscrito de academia `25fcf7208b8f`, `s2` mantiene los 21 nodos y sus páginas de `s1`. **Corrige los dos errores matemáticos confirmados**: `n7` representa $1/(2\sqrt[4]{e})-1/(2e)$, con el paso $e^{-1/4}$, y `n15` conserva $69{,}5$ en las dos apariciones, con $0{,}0129$ como resultado. El original de la página 3 sí imprime la derivada sospechosa de `n5`; la incidencia de `s2` la atribuye correctamente al manuscrito. En `n2`, `s2` corrige otra lectura de `s1`: la cuarta columna de la matriz ampliada coincide con la primera, visible en la página 1. Sigue habiendo pérdidas de detalle: `n13` conserva $0{,}0811$ pero omite el paso factorial manuscrito, y `n19` conserva el máximo/mínimo sin señalar el pequeño gráfico de signos de la página 7. Las incidencias sí marcan otros esquemas que requieren consultar el original. El PDF tiene nueve páginas manuscritas; estas observaciones no avalan la literalidad de cada paso de las 21 respuestas.

El control positivo oficial `1bc800a06e3b` mantiene los mismos 20 nodos, las mismas páginas 6–7, los resultados comprobados y las barras de complemento de B.4. No aparecen hallazgos automáticos. `n12` reproduce la forma ambigua «$a\ne1$ o $26/3$» que figura en la fuente; `s1` la expresaba con claridad como exclusión de ambos valores. Es una ambigüedad de la fuente preservada, no una errata nueva atribuible al modelo. `n26` conserva el resultado $0{,}1218$ y la fórmula, pero omite la sustitución numérica intermedia del PDF que `s1` sí mostraba. Por ello, conservar resultados no equivale a transcripción íntegra.

## Decisión que permiten estos cinco casos

Los nuevos prompts resuelven los cuatro fallos seleccionados de jerarquía, omisión de 4.2, escalas sumadas y dos cifras matemáticas alteradas, sin perder los resultados del control positivo. También aparecen las omisiones de pasos descritas arriba. La muestra está elegida por fallos conocidos, no es representativa; **no se infiere una mejora global ni se cambian los valores por defecto**. La comparación de la cadena completa exige extraer rúbricas y soluciones sobre los árboles `p6` y ampliar con controles correctos de otros tipos de documento.
