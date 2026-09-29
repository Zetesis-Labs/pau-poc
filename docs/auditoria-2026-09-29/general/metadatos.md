# Metadatos, selección de fuentes y trazabilidad

Se inspeccionaron las cabeceras de los **266 exámenes p5** en 14 hojas de contacto. Cada celda contiene los metadatos del catálogo y el 36 % superior de la primera página. Se ampliaron los tres casos siguientes para contrastar la identificación del PDF. Una cabecera sin anomalía visible no certifica todos sus metadatos: hay portadas sin fecha o materia, nombres de asignatura que evolucionan y convocatorias con calendarios excepcionales.

| ID | Registro | Catálogo | PDF original | Dictamen |
| --- | --- | --- | --- | --- |
| META-01 · P1 | `09fa045004f2` | Comunidad Valenciana, Lengua, modelo 2025 | Logo y nombre «Comisión Interuniversitaria de Galicia», código 01 | Región incorrecta. Fuente Llibreta; el metadato ya era incorrecto antes de p5. |
| META-02 · P1 | `61e34b1b42fa` | Comunidad Valenciana, Historia, modelo 2025 | Logo y nombre «Comisión Interuniversitaria de Galicia», código 03 | Región incorrecta. Además tiene figuras equivocadas, documentadas por separado. |
| META-03 · P1 | `cb9d8c2c12d7` | Lengua Castellana y Literatura II, CV, junio 2010 | Cabecera «LITERATURA UNIVERSAL»; preguntas sobre Dante | Asignatura incorrecta. Incluso el nombre del archivo remoto lo llama Castellano: la ruta de descarga no valida su contenido. |

Las imágenes `<id>-pagina-1.png` documentan la prueba. Los campos erróneos están en `documento` del registro, no en un campo inferido por Luna dentro de `resultado`. El contrato p5 no reconcilia la identidad de catálogo con la cabecera. Estos fallos contaminan filtros, muestreo y distribución regional del banco aunque la transcripción del cuerpo sea fiel.

El barrido por palabras regionales había señalado `b996e7795739`: es un falso positivo por alusiones a Madrid/Cataluña dentro del texto del examen. No se usa como prueba de región incorrecta. Las cabeceras de algunos documentos EHU no permiten confirmar el año desde la portada; la diferencia de año entre portada vasca y castellana de `3ad09f75385c` requiere resolver la contradicción de la fuente, no acusar al modelo de alterar el año.

## Anexos y página de inicio

El caso previo `e880b6f47a91 → 2337676aef2a` sigue abierto: el examen pregunta sobre Manuel Martín-Loeches y el solucionario enlazado sobre María Novo. Se documenta en [la revisión de código](../../revision-2026-09-29.md). El parser solo reconoce variantes A/B, y una variante D perdida se empareja como vacía. La existencia física del PDF no hace correcto el vínculo.

Hay dos discordancias adicionales contrastadas en [rúbricas](../rubricas/informe.md): `5091bd5d23ad` tiene una pregunta de poema donde su anexo responde *Historia de una escalera*; en `ab690a84e30c` difieren baremo y número de ítems. Luna detectó y señaló esas diferencias. Tampoco se certifica la autoría oficial de dos PDF con marca de academia solo porque el catálogo los denomine «criterios»; no se afirma que esa marca demuestre autoría privada.

En `184bfaad518f`, el anexo incrustado comienza en el catálogo en la **página 6**, aunque el PDF tiene criterios en la 4 y soluciones A en la 5. `incrustado_por_texto` no reconoce los títulos con acentos separados/precedidos por el nombre de la asignatura; detecta el título de la 6. La alternativa `incrustado_por_extraccion` devuelve la 3 y `combinar()` da preferencia a la detección textual 6. Así se entregan al modelo s1 solo las soluciones B: **12 apartados A quedan fuera de la entrada**, y este examen no tiene salida r1/r2 de rúbrica. Véase S04 en [soluciones](../soluciones/informe.md). Corregir solo el prompt no recuperará texto que nunca se envió.

## Alcance exacto

El catálogo contiene 4.633 documentos, pero solo 266 exámenes tienen extracción p5. Se comprobó la identidad visual de las cabeceras de esos 266; **no** las cabeceras de los 4.633 ni la correspondencia semántica de cada anexo de todo el catálogo. Los scripts de integridad comprueban todos los registros de extracción existentes y los archivos que estos usan. Ninguno de esos checks constituye validación editorial del catálogo completo.

`cabeceras/manifest.json` identifica las 266 celdas y registra la inspección efectuada por el agente. `metadatos-region-candidatos.json` conserva la salida heurística sin convertirla en hechos. `hallazgos.json` contiene las observaciones confirmadas y los recuentos de pérdidas/limitaciones de publicación.
