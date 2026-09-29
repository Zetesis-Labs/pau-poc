# Auditoría de los resultados de PAU — 29 de septiembre de 2026

**El banco todavía no puede darse por validado. Hay errores de extracción que cambian respuestas matemáticas, preguntas completas que desaparecen, rúbricas mal representadas y figuras que no corresponden al ejercicio. También hay errores anteriores y posteriores a Luna: catálogo, selección de páginas, publicación y presentación.** Cambiar de modelo o volver a extraer todo, sin corregir esas etapas, no resolvería el conjunto.

Se auditó el estado local de `main`, commit `2ceef10b24ea13410d1a17ffa3ff45e18d78432e`. No se modificó código, corpus ni publicación, no se volvió a ejecutar la extracción contra la API y no se creó commit. Este informe registra problemas pendientes, no correcciones aplicadas.

## Qué se ha revisado y con qué profundidad

| Área | Universo existente revisado | Comprobación realizada | Lo que no demuestra |
| --- | ---: | --- | --- |
| Preguntas | 266 p5 actuales + 58 p4 anteriores; 6.490 + 1.593 nodos | Inventario y estructura completos, comparación entre versiones, criba léxica contra PDF, triage de los 19 avisos graves p5 y contraste de anomalías con páginas originales | No es cotejo frase por frase de cada enunciado, idioma y estímulo |
| Rúbricas | 76 r2 + 6 r1; 1.186 + 96 entradas | Nodos, páginas, puntos, desgloses, idiomas, generales, respuestas y cotejo léxico; revisión semántica de anomalías; SHA-256 de los 82 PDF originales frente a sus copias publicadas | Cobertura jerárquica y similitud léxica no certifican contenido correcto |
| Soluciones | 25 registros s1: 19 oficiales según catálogo y 6 de academia; 218 entradas, 227 textos por idioma | Inspección por documento, correspondencia de preguntas y respuestas, cotejo léxico íntegro de Historia y lectura visual detallada de Matemáticas/Química y casos gráficos; seguimiento hasta publicación | No es validación histórica independiente de todas las afirmaciones del solucionario ni revisión docente |
| Figuras | 311 planes p5; 292 imágenes publicadas | Reconstrucción geométrica completa, inspección de todas las miniaturas en 15 hojas, contraste de páginas completas en casos señalados | Una miniatura no permite validar todos los símbolos, cotas o compases |
| Identidad de exámenes | 266 cabeceras en 14 hojas | Inspección visual de cabecera junto a metadatos; ampliación de contradicciones | No valida las 4.633 fichas del catálogo ni datos ausentes de la portada |
| Publicación | 266 exámenes, 2.697 preguntas, 5.492 nodos mapeados | Correspondencia con extracción, referencias, reglas omitidas, correcciones y soluciones, fórmulas | Un archivo existente y un texto idéntico a la extracción pueden seguir siendo incorrectos |

En total: **431 registros de extracción**, **326 PDF fuente por ruta**, **1.691 páginas** inventariadas y **29.129 apariciones de fórmulas** comprobadas con KaTeX. No se han leído visualmente las 1.691 páginas completas. Las lecturas y contrastes fueron realizados por agentes; no hubo revisión docente humana. Los recuentos incluyen ejecuciones históricas, no solo contenido distinto publicado.

Los estados sin alerta significan **«no se detectó una anomalía con ese método»**, no «correcto». No hay base para dar un porcentaje de precisión de Luna ni una tasa de error del corpus: la revisión semántica es dirigida y no una muestra aleatoria exhaustivamente etiquetada.

## Hallazgos que deben bloquear la confianza en el contenido afectado

| Prioridad / área | Caso y diferencia demostrada | Responsable principal | Referencia |
| --- | --- | --- | --- |
| P1 · Soluciones | `184bfaad518f:n31`: desaparece la barra de complemento de M en una probabilidad. Además, la incidencia acusa falsamente al PDF de contener esa igualdad errónea. | Extracción s1 | S01 |
| P1 · Soluciones | `25fcf7208b8f:n7`: una **raíz cuarta** se transcribe como cuadrada; `n15`: **69,5 → 67,5**, manteniendo el z y resultado anteriores. Ambos errores llegan a la publicación. | Extracción s1 manuscrita | S02–S03 |
| P1 · Preguntas | `0b7e227a5499`: falta por completo **4.2 y sus dos apartados**, una alternativa de 2 puntos. S1 tampoco conserva sus respuestas ni registra falta de correspondencia. | Árbol p5 incompleto + silencio s1 | PREG-01, S05 |
| P1 · Preguntas | `fda5ea13b6c5`: **24 apartados** bien anidados en p4 pasan a depender de la opción en p5; las seis preguntas se publican sin apartados. `a25ae1a53c4f` pierde la alternativa B.2. | Jerarquía p5 + publicación | PREG-02, PREG-07 |
| P1 · Elección | `ed03ea4e6cf8` reparte mal las cuatro alternativas; `42576f6f84fc` deja cuatro preguntas fuera de la regla de elegir cinco de diez. | Jerarquía p5 | PREG-03–04 |
| P1 · Rúbrica | `070c3795d83c:n5/n13`: bandas alternativas de una escala 0–5 se transforman en tramos con valores 0, 1,5, 3,5 y 5. Interpretados como reparto suman **10 para un máximo de 5**. | Extracción r2 + esquema que no distingue escala y reparto | RUB-001 |
| P1 · Entrada al modelo | `184bfaad518f`: el pipeline envía el anexo desde p. 6 y excluye las **12 soluciones A de p. 5**; los criterios están en p. 4. | Detección y combinación de páginas del pipeline | S04, general/metadatos.md |
| P1 · Figuras | Gráfica sustituida por texto (`184…`), pieza de Dibujo por casilla del alumno (`fdd…`), tabla siderúrgica por otra de electrodomésticos (`61e…`), foto de jóvenes por un conejo (`9c4…`); otras figuras pierden ejes o contornos. | Cajas del modelo y ajuste geométrico, según caso | FIG-01–07 |
| P1 · Partituras | **12 páginas** descartadas por ocupar casi toda la hoja. Otras tres páginas de Mahler sí se publican, pero el fallback de idioma muestra solo la primera. | Validador geométrico + web | FIG-08–09 |
| P1 · Catálogo | `09fa045004f2` y `61e34b1b42fa` son de **Galicia**, clasificados como CV. `cb9d8c2c12d7` es **Literatura Universal**, clasificado como Lengua. | Metadatos de origen; anteriores a Luna | META-01–03 |
| P1 · Correspondencia | `e880b6f47a91` enlaza una solución de otro texto/examen. En `5091bd5d23ad` una pregunta del anexo trata otra obra; en `ab690a84e30c` cambian baremo e ítems. | Vinculación/fuente; r2 avisa correctamente en los dos últimos | PAU-REV-03, RUB-003–004 |

Hay además errores de páginas de referencia, texto francés del enunciado presentado como criterio, pérdida de relaciones en árboles sintácticos y paráfrasis donde el contrato pedía literalidad. Los informes de área conservan nodos, páginas, original, salida e impacto de cada caso. No se equipara una errata tipográfica con una respuesta matemáticamente distinta.

## Pérdidas y limitaciones al construir el banco

Son tres grupos distintos; sus cifras no deben sumarse como si fueran preguntas diferentes:

1. **80 apartados mal situados en 14 exámenes** quedan fuera de los subárboles de pregunta que publica el banco. Los 24 de Ciencias de la Tierra son parte de esos 80, no adicionales. En 78 casos su texto no aparece literalmente en el examen publicado; las otras dos coincidencias son términos breves presentes en otros lugares. Las pérdidas contra el original están confirmadas individualmente en los casos detallados en preguntas.
2. **80 preguntas con regla propia de elección** pierden esa regla al publicar, aunque Luna la extrajo. Es una población distinta de los 80 apartados. **225 exámenes** tienen instrucciones generales extraídas que el banco tampoco transporta; el impacto depende de si contienen reglas necesarias que no se recuperan en otro campo. El PDF original sigue accesible, pero la ficha no es autónoma.
3. **86 entradas de corrección** pertenecen a nodos no publicados: 82 r2 y cuatro s1 de academia. Esas cuatro son las definiciones de `334e3227bf82`, correctamente extraídas pero invisibles en las preguntas publicadas.

Por otra parte, r2 contiene **652 entradas con respuesta**: 10 están en nodos no publicados, 55 en nodos que ya tienen solución y **587 en nodos publicados sin solución**. El contrato actual reserva `solucion` a s1; no se trata de 587 omisiones de Luna. Hay contenido aprovechable que no se utiliza por el diseño de etapas, pero no debe volcarse automáticamente: algunas fuentes no corresponden o tienen procedencia pendiente de acreditar, y la fidelidad de cada respuesta r2 no está certificada.

**223 de los 227 textos s1 llegan byte a byte al banco**, incluidos los tres errores matemáticos anteriores; cuatro se pierden. En 5.492 nodos mapeados no hubo diferencias de etiqueta/enunciado entre extracción y publicación. Esto localiza la causa, no avala la extracción original.

## Rúbricas: qué significa realmente que «cuadren»

Los 1.186 registros de entrada r2 apuntan a nodos existentes y páginas dentro del PDF; no hay duplicados de nodo. Sin embargo, un criterio en un ancestro o descendiente puede hacer aparecer como «cubierto» un nodo sin criterio específico. La cobertura jerárquica es solo un indicador formal.

Se revisaron **14 diferencias de máximo** frente al árbol y **22 desgloses no sumables** en siete documentos. No todos son errores: unos son tarifas por ítem, otros contradicciones impresas, y dos son las bandas mal representadas de `070…`. Un validador que sume indiscriminadamente `desglose[].puntos` genera conclusiones falsas. El contrato necesita distinguir reparto fijo, tarifa por ítem y escala de niveles.

Los criterios generales suman 188 elementos en 52 registros r2; se contrastaron léxicamente todos y se inspeccionó el caso escaneado. Eso no acredita que no falte ninguna penalización o condición. En r1→r2 no desaparecen nodos previamente cubiertos ni se observan grandes reducciones de longitud combinada, pero esos indicadores tampoco demuestran literalidad.

## Evidencia favorable y alertas descartadas

- Los diez s1 oficiales con `contiene_soluciones=false` se contrastaron: contienen criterios, no respuestas concretas. La abstención es correcta. Tres r2 con solo criterios generales tampoco deben inventar una corrección por pregunta.
- R2 detecta la pregunta distinta de `5091bd5d23ad`, los puntos incompatibles de `ab690a84e30c` y contradicciones numéricas reales del original. No se atribuyen esos defectos de fuente a Luna.
- Varios avisos de puntuación en Historia suman todas las alternativas, cuando el estudiante solo responde algunas. Un total aparente de 13/14 no prueba una extracción errónea. El triage de los 19 avisos graves p5 está documentado.
- Una bajada de número de estímulos entre p4 y p5 puede ser una agrupación correcta, no una omisión. La capa de texto rota y el LaTeX también producen baja similitud sin invención.
- No se detectaron archivos de referencia rotos ni páginas fuera de rango en los checks generales. Aun así, hay páginas semánticamente equivocadas y figuras de otra pregunta.
- KaTeX rechaza dos fórmulas entre las 29.129 apariciones comprobadas: una está en p4 histórico; la otra pertenece a la solución publicada de Matemáticas manuscritas. La sintaxis válida de las restantes no acredita su corrección matemática.

## Orden de reparación recomendado

1. **Identidad y correspondencia:** corregir los tres metadatos probados, las variantes y anexos incompatibles, y el comienzo del anexo de Matemáticas 2019. Acreditar autoría antes de presentar una fuente como oficial.
2. **Exhaustividad del árbol:** restaurar las preguntas/alternativas y apartados perdidos; validar tipos de padre, cardinalidad de elección y conservación al publicar. La presencia de soluciones sin nodo debe producir una incidencia visible.
3. **Fidelidad de respuestas:** corregir los tres errores matemáticos contra la imagen original y revisar el resto del manuscrito con especial atención a índices, barras, signos, decimales y pasos omitidos. Preservar el antes/después y la página de evidencia.
4. **Figuras y contrato visual:** rehacer los recortes confirmados, permitir partituras completas y conservar todas las páginas al cambiar de idioma. Extender el contrato para las figuras de soluciones: el marcador «ver figura original» cumple s1, pero no conserva la solución gráfica.
5. **Semántica de rúbrica y publicación:** representar escalas/tarifas/repartos explícitamente, mantener reglas e instrucciones, decidir el uso de respuestas r2 validadas y corregir páginas de criterio/solución.
6. **Cierre por evidencia:** contrastar fuente→salida→banco→vista para cada corrección. Repetir solo los controles afectados y mantener una lista de contenido pendiente; pasar JSON, tests o KaTeX no debe equivaler a aprobación editorial.

Esta auditoría no autoriza a borrar los registros problemáticos ni ha ocultado contenido en producción. La propuesta es retirarles la condición de contenido validado hasta cerrar sus hallazgos, preservando originales y trazabilidad.

## Informes y artefactos para continuar

- [Preguntas: informe y diez casos concretos](preguntas/README.md).
- [Rúbricas: informe, las 82 filas y detalle de entradas](rubricas/informe.md).
- [Soluciones: informe de los 25 registros y 19 observaciones](soluciones/informe.md).
- [Figuras: nueve casos, geometría y alcance visual](figuras/informe.md).
- [Metadatos y selección de fuentes](general/metadatos.md).
- [Índice JSON de observaciones](hallazgos.json). Sus 55 entradas incluyen solapamientos, limitaciones y procedencias pendientes: **no son 55 fallos independientes de Luna**.
- [Estado por examen, 266 filas](estado-examenes.csv). Ninguna fila sin hallazgo se marca como semánticamente certificada.
- [Inventario de los 431 registros](general/inventario.csv), [cobertura publicada](general/cobertura.csv), [pérdidas y limitaciones](general/perdidas-publicacion.csv), [mapeo de respuestas r2](general/respuestas-r2-publicacion.json).
- [Revisión anterior del código: XSS, visor PDF, variantes y elección](../revision-2026-09-29.md). Sus cuatro pendientes siguen abiertos; no se mezclan con las 55 observaciones de extracción.

Los scripts de cada área son locales, de lectura de fuentes y escritura de informes. Usan `pipeline/.venv/bin/python`; `general/auditar.py` usa además el Node 22 disponible para KaTeX. `general/publicacion.py` reproduce el mapeo; `figuras/revisar.py` reproduce geometría/hojas; `general/repro-figuras.cjs` ejecuta el cuerpo real del selector de imágenes con datos actuales; `consolidar.py` reúne observaciones y estados. Las conclusiones visuales se guardan como evidencia de la auditoría, no como resultados automáticos reproducibles sin inspección.

Los PDF fuente y JSON intermedios permanecen ignorados por Git según el diseño del repositorio. Para repetir la auditoría completa en otra máquina hace falta conservar esos archivos de `data/` y `pipeline/salida/`; los CSV registran rutas y hashes. Aquí se guardan las evidencias seleccionadas y los inventarios, no una copia integral del corpus crudo.
