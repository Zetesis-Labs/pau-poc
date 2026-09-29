# Auditoría de soluciones s1 · 29 de septiembre de 2026

Se revisaron los **25 registros** de `gpt-6-luna__s1` sobre `gpt-6-luna__p5`: **19 oficiales y 6 de academia**, todos completed. Hay **10 false**, **15 true**, **218 entradas por nodo** y **227 textos por idioma** (9 nodos bilingües es/va). No hay registros fallidos ni entradas de respuesta vacías. Todos los IDs existen en el árbol p5 y todas las páginas están dentro del PDF; esas dos propiedades no garantizan contenido correcto.

La auditoría encuentra errores matemáticos confirmados en s1, pérdidas anteriores al modelo y pérdidas al publicar. No se puede certificar el conjunto como correcto. Los errores en manuscritos y complementos probabilísticos se comprobaron sobre imágenes del PDF, no sobre OCR.

## Método y alcance real

Lecturas de contrato: README, docs/datos.md y prompt s1. Se abrieron las 25 fuentes locales, se inspeccionaron los textos de las secciones de corrección y se confrontaron las 218 entradas con el árbol. Para Historia, el cotejo automatizado de texto completo se combinó con revisión manual de encabezados, tema, orden, inicios/finales y divergencias. Eso verifica procedencia y correspondencia de fragmentos; **una similitud léxica alta no prueba exactitud semántica ni exactitud histórica**. No se afirma una segunda corrección académica independiente de cada frase histórica.

Para las 21 soluciones manuscritas de Matemáticas 2022 se revisaron visualmente las 9 páginas. También se inspeccionaron completas las páginas matemáticas de Madrid 2019 y 2021 y del modelo 2026, EHU 2026, Química 2019 y los dos árboles de Lengua 2023. Se revisaron visualmente además las páginas de Historia que sustentan referencias erróneas o de continuación. Se separan erratas de la fuente, errores de transcripción y limitaciones del esquema.

Los estados confirmado/dudoso/no-verificable se refieren a la evidencia de las observaciones. En este lote las 25 fuentes están disponibles y las observaciones recogidas son confirmadas; no hay fuentes no-verificables. Ello **no significa 25 documentos conformes**. Los CSV/JSON especifican el alcance por documento y por entrada. No se consultó red, API ni modelos adicionales y no se modificaron datos de producción.

## Hallazgos con evidencia

### S01 · alta · 184bfaad518f · error matemático e incidencia falsa

Nodos: n31. Páginas de fuente: 6. Estado: confirmado.

**Fuente:** P(A∩M̄)=P(A)−P(A∩M)=…=0.15; la barra sobre M está visible en el PDF.

**Salida:** P(A\cap M)=P(A)-P(A\cap M); incidencia afirma que la igualdad contradictoria está impresa y se transcribió literalmente.

Cambia varón por mujer y atribuye falsamente el error a la fuente. Se publica así.

### S02 · alta · 25fcf7208b8f · error matemático

Nodos: n7. Páginas de fuente: 3. Estado: confirmado.

**Fuente:** El recuadro manuscrito muestra 1/(2·raíz cuarta de e)−1/(2e). El paso previo también muestra e^(-1/2²).

**Salida:** 1/(2\sqrt e)-1/(2e).

Pierde el índice 4 de la raíz y cambia el resultado de la integral. Se publica así.

### S03 · alta · 25fcf7208b8f · error matemático

Nodos: n15. Páginas de fuente: 5. Estado: confirmado.

**Fuente:** Corrección de continuidad de 69,5; numerador 69,5−55,4; z>2,23; resultado 0,0129.

**Salida:** 67,5 en las dos apariciones; conserva z>2,23 y 0,0129.

La cadena numérica deja de ser consistente y la salida no avisa. Se publica así.

### S04 · alta · 184bfaad518f · recorte de fuente en pipeline

Nodos: n3, n4, n5, n6, n8, n9, n10, n12, n13, n14, n16, n17. Páginas de fuente: 5. Estado: confirmado.

**Fuente:** Página 5: SOLUCIONES OPCIÓN A, ejercicios 1a–d, 2a–c, 3a–c y 4a–b.

**Salida:** fuente.desde=6; solo 9 entradas de B.

12 soluciones no llegan al modelo s1. No es una omisión imputable al modelo sobre el PDF recibido; el banco deja A sin solución.

### S05 · alta · 0b7e227a5499 · omisión por árbol incompleto y falta de incidencia

Nodos: sin nodo en p5. Páginas de fuente: 6. Estado: confirmado.

**Fuente:** 4.2 a: matrices, casos λ∉{−1,4},λ=−1,λ=4; b: (16/5,−3/5,0)+t(1,−3,−5).

**Salida:** p5 no tiene la pregunta 4.2; s1 no incluye entradas ni elementos en sin_correspondencia.

Dos respuestas desaparecen de forma silenciosa. s1 debió registrarlas sin correspondencia aunque p5 carezca del nodo.

### S06 · alta · 334e3227bf82 · pérdida en publicación

Nodos: n8, n9, n10, n11. Páginas de fuente: 5, 6. Estado: confirmado.

**Fuente:** El solucionario define Soberanía, Absolutismo, Huelga revolucionaria, Golpe de Estado; s1 tiene las 4 respuestas.

**Salida:** datos/preguntas.json publica 8 preguntas del documento y ninguna de las 4 definiciones.

p5 clasifica conceptos como apartados del bloque n7 sin pregunta. La publicación los descarta. No es un fallo s1.

### S07 · media · 114bff1bacb1 · pérdida de estructura visual

Nodos: n17, n18. Páginas de fuente: 5, 6. Estado: confirmado.

**Fuente:** Árboles sintácticos con líneas que asocian palabras a sintagmas y funciones.

**Salida:** Listas «Etiquetas del esquema» y secuencias `\quad`, sin figura ni correspondencias.

Las etiquetas sueltas no representan el análisis sintáctico. Incumple la instrucción de sustituir figuras por marcador; un recorte sería necesario para recuperar la respuesta completa.

### S08 · media · 32384d10aa13 · página errónea

Nodos: n15, n16. Páginas de fuente: 6. Estado: confirmado.

**Fuente:** Reyes Católicos (3) y Carlos I (4) íntegramente en p6.

**Salida:** Ambas entradas indican `paginas.es=5`.

La referencia lleva a una página sin esa respuesta y se exporta sin cambios.

### S09 · baja · 09feb8541d90 · página de continuación

Nodos: n3. Páginas de fuente: 1, 2. Estado: confirmado.

**Fuente:** La respuesta de los documentos 3 y 4 empieza al final de p1 y sigue en p2.

**Salida:** paginas.es=2.

La referencia señala una parte de la respuesta, no su inicio. El esquema solo permite una página y no exige que sea la inicial; no se computa como página totalmente equivocada.

### S10 · baja · 1b0c55921d01 · página de continuación

Nodos: n16. Páginas de fuente: 6, 7. Estado: confirmado.

**Fuente:** La comparación entre absolutismo y liberalismo empieza en p6 y continúa p7.

**Salida:** paginas.es=7.

La referencia omite el inicio; el texto completo sí está transcrito.

### S11 · baja · 3c134e1125e6 · página de continuación

Nodos: n9. Páginas de fuente: 4, 5. Estado: confirmado.

**Fuente:** La segunda (2.2)… Madoz… empieza al pie de p4 y continúa p5.

**Salida:** paginas.es=5; la referencia valenciana, `va=2`, es correcta.

La referencia castellana omite el inicio; el texto completo está presente.

### S12 · media · 25fcf7208b8f · síntesis y paráfrasis

Nodos: n2, n3, n5, n9, n10, n13, n16, n19, n20, n22, n23, n24. Páginas de fuente: 1, 2, 3, 4, 5, 6, 7, 8. Estado: confirmado.

**Fuente:** Matrices A/B explícitas en A1 p1, eliminación por filas en B1 p6, desarrollos numéricos y frases manuscritas.

**Salida:** En A1 se omiten matrices; B1 salta del sistema a «De las ecuaciones se obtiene»; n13 dice «tenemos un consejero» donde la fuente dice «consejo».

No cumple la transcripción literal ni la conservación de todos los pasos aunque muchos resultados coincidan.

### S13 · media · 49e9ef3c3296 · omisión de contexto de solución

Nodos: n2, n8, n9. Páginas de fuente: 1, 2. Estado: confirmado.

**Fuente:** El primer ejercicio define x, y, z como número de recipientes de cada productor. El tercer ejercicio incluye árbol completo con eventos E, H, R, A, M y probabilidades.

**Salida:** n2 contiene solo el sistema y n8/n9, solo el cálculo de p2; no hay entrada para el árbol ni marcador.

Solución incompleta; el árbol aporta 0,5 puntos según criterios p5. El criterio de puntuación no debía ir en la respuesta, pero el paso gráfico sí debía estar indicado.

### S14 · baja · 3c134e1125e6 · regularización o traducción

Nodos: n8, n13. Páginas de fuente: 1, 2. Estado: confirmado.

**Fuente:** n8 (va): Primera Guerra Carlista; n13 (va): Amb la mort de Fernando VII; en es quals.

**Salida:** n8 (va): Primera Guerra Carlina; n13 (va): Ferran VII; en els quals.

Cambios semánticamente próximos pero prohibidos por no traduzcas/no corrijas; no equivalen a alucinación extensa.

### S15 · baja · 114bff1bacb1 · contradicción fuente/enunciado no registrada

Nodos: n20. Páginas de fuente: 1, 5. Estado: confirmado.

**Fuente:** El enunciado pregunta por «generalización», en singular; el solucionario analiza General+iz+a+cion+es, con morfema flexivo de número.

**Salida:** s1 conserva «es» y el plural, con `incidencias` vacío.

El plural no es una invención de Luna. Falta avisar de la discordancia de la fuente como exige s1.

### S16 · limitación · 0743849de2d6 · figura perdida por contrato

Nodos: n10, n11. Páginas de fuente: 5, 6. Estado: confirmado.

**Fuente:** Dos análisis sintácticos gráficos con notas explicativas.

**Salida:** Solo (ver figura en la solución original).

Cumple la regla s1, pero el alumno no ve el análisis ni un recorte. La fuente original conserva la respuesta.

### S17 · limitación · 2787fc4d640f · figura perdida por contrato

Nodos: n5. Páginas de fuente: 4. Estado: confirmado.

**Fuente:** Estructuras de Lewis de Cl2 y NH3 con electrones no enlazantes.

**Salida:** Solo (ver figura en la solución original).

Cumple s1; el esquema no guarda la figura ni los electrones.

### S18 · limitación · 49e9ef3c3296 · figura perdida por contrato

Nodos: n18. Páginas de fuente: 3. Estado: confirmado.

**Fuente:** Región sombreada entre parábola y coseno.

**Salida:** El recinto solicitado es: (ver figura en la solución original).

Cumple s1; no se conserva el dibujo pedido.

### S19 · baja · 2787fc4d640f · corrección/adición menor

Nodos: n35, n42, n44. Páginas de fuente: 5. Estado: confirmado.

**Fuente:** n35: resultado v=K[A]·[B]²; n42: 4,4×10^-3 sin unidad escrita; n44: corchete sobrante.

**Salida:** n35 cambia K a k; n42 añade mol; n44 elimina corchete, con incidencia.

Es una normalización matemáticamente razonable, pero no estrictamente literal. No se identifica cambio de resultado.

## Inventario completo de los 25 registros

| Documento | Origen | Materia/año | Entradas | Comprobación y resultado |
|---|---|---|---:|---|
| 09feb8541d90 | academia | Historia de España 2021 | 12 | **Confirmado**. 12 respuestas castellanas de academia: documentos Cádiz/franquismo, cuatro conceptos, medidas legislativas, ideología, constituciones y mujer. Cotejo léxico íntegro contra pp. 1–11 y atribución de todos los nodos por pregunta/tema. No hay versión valenciana en la fuente. n3 referencia p2 aunque comienza p1. |
| 16d0161b5c29 | academia | Historia de España 2020 | 12 | **Confirmado**. 12 respuestas castellanas de academia: Trienio, Riego, sufragio/Segunda República, cuatro conceptos y comparaciones. Cotejo léxico íntegro pp. 1–11 y atribución por encabezados/enunciados. Sin traducción valenciana añadida ni omisión textual grande detectada. |
| 1b0c55921d01 | academia | Historia de España 2022 | 12 | **Confirmado**. 12 respuestas castellanas de academia: Inquisición, Trienio, Juan Carlos, Transición y cuatro conceptos. Cotejo léxico íntegro pp. 1–8 y atribución por preguntas/temas. n16 apunta p7 aunque empieza p6. No versión valenciana inventada. |
| 25fcf7208b8f | academia | Matemáticas II 2022 | 21 | **Confirmado**. 21 entradas contrastadas con las 9 páginas manuscritas renderizadas: discusión/sistema, derivadas/integral, recta/plano, binomial-normal, edades, Bolzano/área, rectas y Bayes. Errores numéricos/léxicos visibles y síntesis sistemática de pasos; 2 errores matemáticos graves n7/n15; erratas de la fuente reconocidas en n5, n14 y n26. |
| 334e3227bf82 | academia | Historia de España 2023 | 12 | **Confirmado**. 12 respuestas castellanas de academia: Constitución de 1812/Fernando VII, huelga de 1917/Primo, cuatro conceptos y temas constitucionales/sociales. Cotejo léxico íntegro pp. 1–9 y atribución por encabezados. Cuatro conceptos n8–n11 correctos en s1 desaparecen de publicación. |
| 6426459db740 | academia | Historia de España 2021 | 20 | **Confirmado**. 20 respuestas castellanas de academia: 12 cuestiones, 2 fuentes históricas con 2 apartados cada una, 1 tema, 3 comentarios. Cotejo léxico íntegro pp. 1–12; correspondencia por A/B y enunciado. Texto con errores históricos ya presentes en fuente; la auditoría no los atribuye a Luna ni certifica exactitud histórica. |
| 01808acbd270 | oficial | Historia de España 2024 | 0 | **Confirmado**. Leídas pp. 3–7: criterios de cuestiones, fuente, tema y texto; orientaciones y temario. No dan respuestas concretas. false correcto. |
| 053608cf06ee | oficial | Lengua Castellana y Literatura II 2013 | 0 | **Confirmado**. Leídas pp. 1–2 de criterios oficiales valencianos: comentario, morfología, sintaxis, cohesión, adecuación, literatura y descuentos. No hay soluciones concretas. false correcto. |
| 070c3795d83c | oficial | Técnicas de Expresión Gráfico-Plástica 2026 | 0 | **Confirmado**. Leídas pp. 1–4: tablas y escalas de evaluación para apartados A/B; las imágenes 1/2/3 son productos a evaluar, no soluciones propuestas. false correcto. |
| 0743849de2d6 | oficial | Lengua Castellana y Literatura II 2025 | 6 | **Confirmado**. 6 entradas verificadas contra pp. 5–6: tema, tipo textual, 2 análisis sintácticos, regeneración y antónimos. Se omiten respuestas abiertas porque la fuente no las resuelve. Dos respuestas son solo marcador de figura; el esquema cumple s1, pero no conserva los análisis. |
| 0a50595f8036 | oficial | Dibujo Artístico II 2026 | 0 | **Confirmado**. Leídas pp. 2–3: criterios de boceto/dibujo final y orientaciones. La p3 lleva SOLUCIONES, pero contiene un temario, no dibujos resueltos. false correcto. |
| 0b7e227a5499 | oficial | Matemáticas II 2026 | 13 | **Confirmado**. 13 respuestas de pp. 5–6 cotejadas textual y visualmente: dron, función par, integral, binomial/normal, matrices, Bolzano y continuidad. Se conservan las fórmulas y los resultados de las 13 entradas. Solución 4.2 a/b p6 completamente perdida: no existe nodo p5 y sin_correspondencia vacío. |
| 0bed555f767c | oficial | Italiano 2018 | 0 | **Confirmado**. Leída p3: criterios de comprensión, morfosintaxis y redacción italiana, sin respuestas. false correcto; no se inventan textos italianos. |
| 0d5e5806192a | oficial | Lengua Castellana y Literatura II 2019 | 0 | **Confirmado**. Leídas pp. 3–4: estructura de Lengua y criterios generales de todas las preguntas; no hay solucionario concreto. false correcto. |
| 0fedaac3fe5f | oficial | Lengua Castellana y Literatura II 2011 | 0 | **Confirmado**. Leídas pp. 1–2: criterios generales valencianos y penalizaciones; no hay respuestas. false correcto. |
| 114bff1bacb1 | oficial | Lengua Castellana y Literatura II 2023 | 8 | **Confirmado**. 8 entradas contrastadas con pp. 5–6, ambas renderizadas: temas/tipos A/B, morfología, antónimos y 2 árboles sintácticos. Árboles convertidos en etiquetas sin relaciones. La fuente morfológica en plural contradice el enunciado en singular y no hay incidencia. |
| 13244a0fa596 | oficial | Historia de España 2021 | 0 | **Confirmado**. Leídas pp. 3–8: criterios de Historia, orientaciones y programa. No hay respuestas específicas de ese examen. false correcto. |
| 172579fa76d4 | oficial | Historia de la Filosofía 2021 | 0 | **Confirmado**. Leídas pp. 6–7: rúbricas graduadas de Filosofía, bloques 1 y 2. No hay respuesta filosófica concreta; false correcto. |
| 17445f0ab770 | oficial | Química 2023 | 0 | **Confirmado**. Leída p1 bilingüe es/va: seis reglas generales de Química. No hay resultados químicos. false correcto. |
| 184bfaad518f | oficial | Matemáticas II 2019 | 9 | **Confirmado**. 9 respuestas B de p6 cotejadas visualmente, incluida barra de complemento; p5 completa renderizada. El pipeline entrega el PDF desde la página 6 y omite 12 apartados de A en la página 5. n31 pierde la barra que indica el complemento de M e inventa una incidencia sobre una supuesta errata de la fuente. |
| 1bc800a06e3b | oficial | Matemáticas II 2021 | 20 | **Confirmado**. 20 respuestas contrastadas íntegramente con pp. 6–7 renderizadas: acciones, área, recta/plano, normal, sistema, derivadas/integral, planos y probabilidad. Incluidas barras de complemento correctas en B4. No se detecta ningún cambio matemático sustancial; corrige pequeñas erratas tipográficas de fuente sin avisar. |
| 2787fc4d640f | oficial | Química 2019 | 34 | **Confirmado**. 34 apartados contrastados textual y visualmente pp. 4–5: enlace/Lewis, solubilidad, ácidos, orgánica, electrolisis, átomos, cinética, redox/equilibrio. Fórmulas, cargas, coeficientes, resultados y tablas revisados. Lewis solo como marcador; K→k y corchete sobrante corregidos; tres incidencias de salida comprobadas. |
| 32384d10aa13 | oficial | Historia de España 2018 | 16 | **Confirmado**. 16 respuestas castellanas de pp. 4–7: 12 cuestiones, 2 fuentes, tema Transición y comentario Mendizábal. Cotejo léxico completo y atribución por A/B y contenido. n15/n16 citan p5 pero están íntegramente en p6, confirmado visual. |
| 3c134e1125e6 | oficial | Historia de España 2026 | 9 | **Confirmado**. 9 nodos con 18 textos es/va contrastados pp. 1–6: 4 conceptos, 2 fuentes, 2 temas y comparación agraria. Correspondencias correctas; n9 es empieza p4 y cita la página 5; n13 va traduce Fernando→Ferran; otras regularizaciones valencianas incumplen literalidad estricta. |
| 49e9ef3c3296 | oficial | Matemáticas II 2026 | 14 | **Confirmado**. 14 entradas de las pp. 1–3 cotejadas textual y visualmente: sistema/productores, cúbica, probabilidad, geometría, integral y área. Árbol de probabilidad p1 omitido sin marcador; definición de x/y/z ausente de n2. Gráfica 5B representada por marcador n18. Resultados de 14 entradas conservados. |

## Diferencias con r2 y publicación

En 8 de los 25 documentos existe un archivo r2 con el mismo ID. Solo 3 contienen respuestas comparables: `2787fc4d640f`, `3c134e1125e6`, `49e9ef3c3296`. Se localizaron 64 textos s1 con respuesta r2 en el mismo nodo/idioma; 15 son idénticos byte a byte. Las 49 diferencias restantes se documentan en `publicacion-r2.json`; muchas son saltos de línea, LaTeX y fórmulas equivalentes. El número 49 no es una cuenta de errores semánticos.

- Química: r2 y s1 conservan los 34 apartados. s1 transforma los equilibrios en tablas Markdown; r2 los serializa como arrays. Las notas sobre nomenclatura anterior a 1993 aparecen dentro de la respuesta de r2 y se excluyen correctamente de s1 como instrucción al corrector. Ambos carecen del dibujo Lewis; s1 cumple su marcador. s1 regulariza K→k y añade mol donde el documento no imprimió esa unidad; son cambios de literalidad pequeños.
- Historia 2026: s1 n12 incluye el párrafo de Constitución 1837/1845, partidos y organización administrativa; r2 lo guarda como criterio y empieza su respuesta en reforma agraria. El contenido de s1 está en la fuente y corresponde a la misma pregunta compuesta, no es invención. r2 conserva Fernando en la versión valenciana de n13; s1 lo convierte en Ferran.
- Matemáticas EHU: r2 agrupa ecuación de recta con n13 y contexto de gráfica con n18; s1 conserva esos preámbulos en n12/n17 y reparte el resto en hijos. No se considera reasignación incorrecta: son desarrollos comunes del mismo ejercicio. Ninguna de las dos etapas preserva el árbol de probabilidad p1.

**223 de 227 textos s1 están publicados idénticos en el nodo correspondiente**, con la misma página, origen y fuente; 4 faltan (S06). Por tanto, también se publican los errores S01–S03 y las referencias incorrectas S08. Se verificó el anclaje de apartados usando padre, etiqueta y enunciado del árbol; el banco no conserva IDs en los apartados. No se atribuye a s1 una transformación posterior inexistente.

## Fuente con erratas frente a errores de extracción

El manuscrito Matemáticas 2022 sí contiene la derivada incorrecta en A2a, la aproximación 0,99 en A4b y la omisión de pañuelos de cuadros en B4a; s1 los conserva y avisa. Son defectos del solucionario. Sin embargo, la raíz cuarta de A2c y el 69,5 de A4c están bien en el documento y se alteran al extraer. La barra de complemento de Matemáticas 2019 está bien en la fuente y se pierde en s1; su incidencia es falsa.

En `1bc800a06e3b` el documento contiene pequeñas erratas como determinadod/incompatibled y una notación descuidada de exclusión de valores; s1 las limpia sin avisar, pero los casos, resultados y barras de complemento coinciden. En Historia de academia se conservan afirmaciones discutibles del original: no deben confundirse con invenciones de Luna ni tomarse como validación histórica independiente.

## Figuras y límites del contrato

Hay 12 textos con el marcador de figura: 8 en Matemáticas academia, 2 en Lengua 2025, 1 de Lewis y 1 de la región de EHU. Esta ausencia de imagen está ordenada por s1, por lo que es una pérdida funcional del contrato, no una omisión espontánea del modelo. Distinto es el árbol de EHU, que ni siquiera tiene marcador, y los árboles de Lengua 2023, que se aplanan en etiquetas sueltas. En la academia se omite además el pequeño esquema del ángulo de A3c sin marcador, aunque se conserva el desarrollo numérico.

## Artefactos y reproducción

`audit.py` abre los 25 JSON/PDF, registra el SHA256 de la fuente, genera `registros.json`, `entradas.json` y contraste léxico de Historia. `compare_stages.py` mapea la publicación por ID de pregunta y padre/etiqueta/enunciado de apartados y compara r2. `finalize.py` agrega las observaciones manuales verificadas y produce los CSV y JSON revisados. Reejecutar en ese orden con `pipeline/.venv/bin/python docs/auditoria-2026-09-29/soluciones/<script>.py`. Ninguno llama al pipeline productivo o a red.

Los archivos `<origen>-<id>.txt` son cuadernos de trabajo locales con árbol, resultado y extracción de texto. Los PNG `<id>-p<n>.png` y dos detalles de manuscrito documentan la revisión visual; no son recortes productivos. `entradas-revisadas.json` tiene una fila por nodo/idioma, texto original, hallazgos, metodología y cotejo de publicación. `registros-revisados.json` y `registros.csv` cubren también los 10 false.
