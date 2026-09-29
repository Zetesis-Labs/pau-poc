# Auditoría de extracción de preguntas p4/p5 — 2026-09-29

## Alcance y método

Se revisaron los prompts `pipeline/prompts/p4.md` y `p5.md`, los 58 resultados p4 y los 266 resultados p5 por examen, sus PDF originales en `data/`, y el banco **publicado** `datos/preguntas.json` (266 exámenes, 2697 preguntas). El agregado `pipeline/salida/gpt-6-luna__p5/preguntas.json` tiene solo 58 exámenes y 549 preguntas; está desactualizado y no se usa para estimar el impacto publicado.

`inventariar.py` comprueba todos los nodos p4/p5, referencias padre, tipos, órdenes, páginas, estímulos textuales y similitud léxica contra el texto de las páginas PDF. Los resultados reproducibles son `inventario.json` y `candidatos.json`. El agente contrastó directamente los 19 hallazgos graves p5 registrados por el validador en 14 documentos, las pérdidas p4→p5 destacadas y páginas PDF seleccionadas; se renderizaron visualmente la p. 2 de `0b7e227a5499` y la p. 3 de `42576f6f84fc`. `hallazgos-confirmados.json` separa los diez casos con comparación concreta entre original y salida.

**Límite de cobertura:** la comprobación estructural cubre los 6490 nodos p5 y 1593 p4; la semántica de cada pregunta no se ha cotejado individualmente con las 266 fuentes. Cuatro PDF p5 carecen prácticamente de capa de texto (`17445f0ab770`, `1f06fc98f001`, `3c134e1125e6`, `6a2a804ce68f`), por lo que la similitud léxica no sirve en ellos y requerirían lectura visual completa. En varios PDF de 2010 el texto sale sin espacios; las alertas de baja similitud de esos documentos tampoco prueban errores. No se llamó a modelos ni se regeneraron datos.

## Fallos confirmados prioritarios

| ID | Documento, nodo y página del PDF | Original frente a p5 | Efecto |
| --- | --- | --- | --- |
| PREG-01 · P1 | `0b7e227a5499`, n13, p. 2 | El PDF imprime **Pregunta 4.2**, sistema de ecuaciones, y «a) ... Discutir el sistema ...; b) ... Resolver el sistema si λ = −1» (1 punto cada uno). El bloque n13 dice elegir 1 de 2, pero solo conserva 4.1 (n14). | Desaparece una alternativa completa de 2 puntos del banco publicado. Verificación visual y textual. |
| PREG-02 · P1 | `fda5ea13b6c5`, n3–n32, pp. 1–4 | Cada PREGUNTA A1–A3/B1–B3 imprime «Qüestió a)–d)». p4 las colgaba de su pregunta; p5 cuelga las 24 directamente de EXERCICI A/B (n1/n2). | Las seis preguntas de `datos/preguntas.json` tienen `apartados: []`: se pierden las 24 cuestiones. Regresión p4→p5. |
| PREG-03 · P1 | `ed03ea4e6cf8`, n4/n11, p. 1 | El PDF manda «responda dos preguntas de 3 puntos a elegir indistintamente entre ... A.1, B.1, A.3, B.3». n4 guarda `de=4` pero solo contiene A.1; las otras tres cuelgan de n11, sin regla. | Elección y pertenencia de tres alternativas erróneas. |
| PREG-04 · P1 | `42576f6f84fc`, n6/n28–n32, pp. 2–3 | El PDF pide elegir cinco de diez preguntas; la p. 3 prosigue con 7), 8), 9), 10) bajo el mero epígrafe «Educación literaria». p5 mete estas cuatro preguntas bajo un bloque n28 sin elección, mientras n6 conserva `de=10` pero solo tiene seis preguntas directas. | La regla de elección deja de abarcar cuatro preguntas. La p. 3 se comprobó visualmente. |
| PREG-05 · P1 | `41fdc1fe038d`, n6–n8, pp. 1/3 | El impreso dice «4. a) Exposeu ... b) Relacioneu ...» (y versión castellana). n6, pregunta 4 de la primera opción, queda vacío; a)/b) cuelgan de la opción n1. La segunda opción sí tiene a)/b) bajo su pregunta 4. | En `datos/` la pregunta 4 de la primera opción no contiene sus dos apartados. |
| PREG-06 · P2 | `2422938d704e`, n30/n40, p. 2 | «PREGUNTA 4 (10 punts) ... 4.3. És indispensable el centrosoma ... (2 punts)». n40 aparece como **pregunta** hija de n30, otra pregunta, en lugar de apartado 4.3. | El esquema p5 es inválido; el aplanado actual sí publica 4.3 como apartado, por lo que no hay pérdida visible en `datos/`. |
| PREG-07 · P1 | `a25ae1a53c4f`, n16–n17/n26–n29, pp. 1–2 | El PDF presenta A.2 y B.2 como las dos fuentes entre las que se elige una. p5 ya contiene A.2 en n17, pero la duplica como bloque raíz n26 y desplaza B.2 a bloque raíz n27. | La regla `de=2` queda con un solo hijo y B.2 falta por completo en las preguntas de ese examen en `datos/`. |
| PREG-08 · P2 | `d54d5d841933`, n16, p. 2 | El PDF imprime «II.3. Luces de bohemia en el contexto histórico y literario de su época». p5 deja `enunciado=[]` y pone toda la frase como etiqueta, omitiendo la marca «II.3.». | Tarjeta con título equivocado y separación marca/contenido rota. |
| PREG-09 · P2 | `2787fc4d640f`, n31, p. 2 | El PDF imprime «b) Ácido metanoico + propan-2-ol →». p5 usa la reacción como etiqueta y deja el enunciado vacío. | Se pierde la marca b) y se presenta el contenido como título. |
| PREG-10 · P2 | `9c4cbc92103b`, metadato, p. 5 | «Puntuación máxima de la prueba: 10 puntos» solo aparece en los **criterios específicos de corrección** de la p. 5; el propio resultado declara `paginas_enunciado=[1,2,3,4]` y reconoce el origen en una incidencia. Aun así fija `puntuacion_total=10`. | Usa criterios para un dato que p5 restringe al enunciado/instrucciones del examen. |

Las rutas PDF exactas por documento están en `inventario.json`, campo `pdf`; las salidas están en `pipeline/salida/gpt-6-luna__p5/<id>.json`.

## Hijos de tipo `apartado` fuera de preguntas

La regla p5 dice que los apartados son subdivisiones de una pregunta. El chequeo estructural encuentra **80** apartados p5 cuyo padre es `bloque` u `opcion`, repartidos en 14 documentos. `pipeline/src/pau/dominio/banco.py` construye los apartados recorriendo solo los hijos de cada pregunta: estos 80 nodos quedan fuera del árbol publicado. En una búsqueda exacta del texto de esos incisos dentro de las preguntas publicadas del mismo examen, **78 de 80 no aparecen**; los dos coincidentes son los términos breves «Guerra Civil» y «Monarquía», que también aparecen en otro lugar. La tabla inventaría todos los casos estructurales; no implica que el agente haya cotejado visualmente cada inciso del PDF. En `fda5ea13b6c5` y `41fdc1fe038d` se verificó además la pérdida contra el original.

| Documento | Apartados fuera de pregunta | Padres/efecto observado |
| --- | ---: | --- |
| `fda5ea13b6c5` | 24 | Opciones A/B; 24 incisos de seis preguntas publicados sin hijos. |
| `b996e7795739` | 9 | Bloques bajo preguntas de Lengua; revisar pertenencia de a)/b)/c). |
| `90a0459332b9` | 7 | Opciones de Historia; las cuestiones quedan fuera de una pregunta. |
| `053608cf06ee` | 4 | Bloques I de Lengua. |
| `0fedaac3fe5f` | 4 | Bloques I de Lengua. |
| `28f5e820a133` | 4 | Opciones de fuentes históricas. |
| `334e3227bf82` | 4 | Bloque de definiciones de Historia. |
| `389c79bb683d` | 4 | Bloque de definiciones de Historia. |
| `838c30ae94d8` | 4 | Bloques I de Lengua. |
| `93dc23ff9203` | 4 | Bloque de definiciones de Historia. |
| `cc4ce021beb2` | 4 | Bloques de fuentes históricas. |
| `d54d5d841933` | 4 | Bloques I de Lengua; se suma al error de n16. |
| `41fdc1fe038d` | 2 | Opción primera; pérdida publicada confirmada. |
| `a25ae1a53c4f` | 2 | Bloque duplicado B.2. |

En los 58 documentos comparables, p4 tenía 110 apartados con padre bloque/opción (11 documentos) y p5 tiene 80 en toda la colección ampliada. No es una regresión global: p5 corrigió muchos casos p4. `fda5ea13b6c5` sí es una regresión inequívoca: sus 24 apartados estaban bien anidados en p4.

## Triage de los 19 avisos graves p5 previos

| Documento | Avisos | Conclusión frente al PDF |
| --- | --- | --- |
| `d487a226ab90`, `cc4ce021beb2` | `puntos-no-cuadran` y `total-distinto` | **Falsos positivos aritméticos**: el impreso manda elegir 3 de 8 cuestiones, de 1 punto cada una, más una fuente de 2,5 y un tema de 4,5: 3+2,5+4,5=10. Sumar todas las alternativas da 13. `cc4...` tiene además apartados mal anidados, hallazgo separado. |
| `215c4577b13a`, `5a168e605053`, `6426459db740`, `aac3495c1069` | `total-distinto` (14 frente a 10) | **Falsos positivos aritméticos**: el PDF permite hasta 4 de 12 cuestiones (4 puntos), una fuente (1,5) y un tema/texto (4,5); 4+1,5+4,5=10. |
| `a25ae1a53c4f` | `total-distinto` (17 frente a 10) | Sumar alternativas explica el aviso numérico; hay además duplicación real de A.2 y B.2 desplazada (PREG-07). |
| `ac1e68a880cb` | `puntos-no-cuadran` (4 frente a 2) | **Falso positivo**: n1 vale 4 y sus preguntas 1.1/1.2/1.3 valen 2+0,6+1,4=4; la elección de uno de dos **textos** es independiente de esas tres preguntas. |
| `42576f6f84fc` | `puntos-no-cuadran` | Para n24 el PDF se contradice: cabecera dice 0,4 por inciso, cada inciso imprime 1,2. p5 conserva ambos e incluye incidencia. El otro aviso refleja la jerarquía incorrecta PREG-04. |
| `d54d5d841933`, `41fdc1fe038d`, `2787fc4d640f`, `2422938d704e` | `enunciado-vacio` o `pregunta-dentro-de-pregunta` | Confirmados como PREG-08, PREG-05, PREG-09 y PREG-06. |
| `ed03ea4e6cf8` | `total-distinto` (16 frente a 10) | El PDF ordena 4 + 2×3 = 10; el cálculo del validador suma alternativas. La estructura de elección sí está rota (PREG-03). |

## Comprobaciones negativas y pendientes

- La comparación p4/p5 produce 41 documentos con algún cambio de conteo, idioma, páginas o estímulos. Muchos son mejoras taxonómicas p5: por ejemplo `fda5ea13b6c5` p4 creaba tres estímulos «figura» aunque las figuras A2/A3/B1 no vienen en el PDF; p5 lo explica en incidencias y no inventa recortes. En `03364198c8fb`, p4 separaba cuatro dibujos de una niña/caja y p5 los agrupa como un conjunto: el descenso de 8 a 5 estímulos no prueba pérdida. No se clasifica ningún mero cambio de conteo como error sin leer la página.
- El barrido de etiquetas «Pregunta 4.2» detectó PREG-01. Otros aparentes faltantes se deben a etiquetas que ya incluyen «Pregunta», a bloques de elección o a numeración de otro nivel; `c85cd1758e28` declara opciones A/B pero su PDF de una página solo contiene A y la incidencia lo explica. No se inventa B.
- Los 22 avisos léxicos p5 de PDF con capa de texto se concentran en diez documentos: cuatro de Lengua/Historia (`a1bdfb201724` 2, `cb9d8c2c12d7` 5, `42e04e11e8ed` 3, `cab36a516c34` 4), donde el texto de extracción del PDF concatena muchas palabras o columnas, y seis de Matemáticas (`423dd33e007e`, `570fa053e73a`, `64e2509df555`, `81564bef5faa`, `9c6c1758e986`, `e28ef720b913`, ocho avisos), donde la fórmula LaTeX no es comparable léxicamente con los glifos del PDF. El agente inspeccionó los nodos señalados y muestras de sus PDF; ninguna puntuación baja, por sí sola, acredita paráfrasis o invención. Esta criba no equivale a cotejo literal completo.
- Hay 265 resultados p5 con `normalizaciones=0` y uno (`4e703d87e493`) con valor 1. El registro solo guarda el resultado normalizado y un contador; sin la salida previa a la normalización no se puede certificar si cambió algún significado. La única transformación aplicada no se considera un hallazgo semántico sin evidencia de antes/después.
- `candidatos.json` incluye alertas léxicas para orientar una revisión semántica posterior por agente; no son fallos confirmados. Entre 140 alertas p5 de baja similitud, 118 corresponden a PDF sin capa de texto y 22 a PDF con texto. La literalidad de la colección completa sigue **sin certificar**. También siguen sin certificar individualmente exhaustividad de estímulos textuales, cada traducción/idioma y cada página de inicio.

## Reproducción

Desde la raíz del repositorio:

```bash
pipeline/.venv/bin/python docs/auditoria-2026-09-29/preguntas/inventariar.py
```

El script solo lee `pipeline/salida`, `data/pdfs` y escribe su inventario/candidatos dentro de este directorio. Las comparaciones directas se pueden repetir abriendo el PDF indicado en `inventario.json` y el `resultado.nodos` del JSON p5 correspondiente.
