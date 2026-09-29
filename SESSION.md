# Sesión: auditoría y recuperación de respuestas de rúbricas — actualizado 2026-09-29

## Objetivo

Revisar el POC completo en main y todos los resultados existentes de Luna: preguntas, soluciones, rúbricas, figuras y publicación. Tras guardar la auditoría, el usuario autorizó cambios preventivos en prompts, controles locales de conservación y una evaluación pequeña de cinco llamadas de IA. Después pidió rediseñar la vista (filtros en modal, PDFs al pie en acordeones, bordes suaves) y tema claro/oscuro según navegador. Después autorizó corregir los tres primeros pendientes: HTML inseguro, solución de otra variante y pérdida de elección propia. Incluye reparación local acotada de los datos afectados. No ha pedido regenerar todo el corpus, commitear ni desplegar.

## Estado actual

- Petición más reciente: publicar todos los cambios en GitHub Pages. Autorizado commit/push/integración para desplegar. Flujo existente `.github/workflows/pages.yml`, destino `https://zetesis-labs.github.io/pau-poc/`. Rama de entrega `feat/pau-quality-and-ui`; build adicional en contenedor con `BASE_PATH=/pau-poc/` correcto. El resultado del despliegue se comprueba en GitHub Actions y en la web pública.

- Última petición autorizada: recuperar respuestas ya extraídas en rúbricas que no llegaban a soluciones, sin llamadas nuevas de IA. Cruce actualizado: 587 candidatas en 348 preguntas de 42 exámenes.
- Implementado `dominio/recuperacion.py`, compartido por `aplicacion/banco.py` y `verificacion.py`. Preserva soluciones propias/ancestros y recupera solo respuestas con identidad, fuente pública/correspondencia y referencias de idioma/página utilizables. Excluye las fuentes/nodos problemáticos conocidos; registra razones. Añade `extraccion: rubrica` sin certificar fidelidad académica.
- Aplicada reparación local cerrada: **479 respuestas en 285 preguntas de 36 exámenes**; 108 candidatas quedan pendientes. No se cambian extracciones, catálogo, rúbricas, reglas ni soluciones previas. `docs/recuperacion-respuestas-2026-09-29/` contiene script, plan con 224 entradas hasheadas, resultado e informe de verificación. Script idempotente; no ejecutar el reparador anterior sobre este nuevo banco.
- Web etiqueta «Respuesta en los criterios oficiales», PDF bajo Soluciones con página del idioma, y salto con grupo explícito para distinguir Criterios/Soluciones cuando comparten PDF/página. Etiqueta centralizada en `dominio/rubrica.ts`.
- Validación recuperación: 151 tests Python; 101 web y prueba dirigida de navegación; tipos/build en contenedor pasan. Ruff y Biome en contenedor. QA Chrome ficha cdd0f4f759e1:n2 muestra cuatro definiciones, clic de respuesta abre Soluciones en página 4 de a94284193403.pdf. Servidor sigue en puerto 3100.
- Verificación completa posterior sin IA: 20 exámenes con controles superados, 246 pendientes; cero exámenes con cobertura reducida. Los pendientes previos no se ocultan ni se autoriza publicación completa con ellos. No commit ni despliegue.

- Revisión de código guardada en `docs/revision-2026-09-29.md`: XSS por HTML sin sanear, carrera del visor PDF, anexo de variante equivocada y reglas propias de elección omitidas. PAU-REV-01/03/04 corregidos localmente en código/datos. PAU-REV-02 tiene corrección local; falta regresión de estrés con PDF.js real.
- Auditoría documentada en `docs/auditoria-2026-09-29/README.md`, con informes separados de preguntas, rúbricas, soluciones, figuras y metadatos. Índice JSON y CSV por examen.
- Comprobados mecánicamente los 431 registros: 266 p5 + 58 p4, 76 r2 + 6 r1, 25 s1. 326 PDF fuente, 1.691 páginas inventariadas. No se ha cotejado semánticamente cada frase ni leído visualmente las 1.691 páginas.
- Inspeccionadas todas las 292 miniaturas publicadas y 266 cabeceras. Contraste ampliado de los casos señalados; los informes explican límites por área.
- Tres errores matemáticos confirmados y publicados: barra de complemento perdida en `184bfaad518f:n31`, raíz cuarta→cuadrada y 69,5→67,5 en `25fcf7208b8f:n7/n15`.
- Omisiones confirmadas: pregunta 4.2 de `0b7e227a5499`, B.2 de `a25ae1a53c4f`, 24 apartados de `fda5ea13b6c5`. Inventario de 80 apartados fuera de pregunta en 14 exámenes.
- Dos rúbricas `070c3795d83c:n5/n13` convierten bandas alternativas de 0–5 en reparto sumable de 10. Otros casos incluyen páginas incorrectas y enunciado francés como criterio.
- Figuras: gráficos sustituidos por texto, tablas/fotos intercambiadas, pieza de Dibujo por casilla del alumno, contornos/ejes cortados. 12 páginas de partituras descartadas por tamaño. La web muestra una de tres páginas de Mahler por fallback de idioma; reproducido ejecutando el cuerpo real de `figurasDe`.
- Catálogo: dos modelos CIUG Galicia (`09fa045004f2`, `61e34b1b42fa`) etiquetados como CV; `cb9d8c2c12d7` es Literatura Universal, no Lengua.
- En revisión previa pasaron 91 tests Python y 61 web con Node 22. No hubo build ni lint. En esta fase de documentación no se repitieron suites no afectadas.
- Aplicados candidatos `pipeline/prompts/p6.md`, `r3.md`, `s2.md`: cobertura/estructura, bandas de rúbrica, soluciones sin correspondencia, símbolos y figuras. Prompts anteriores/defaults intactos; esquema sin cambios. El inventario previo es instrucción, no dato persistido.
- Añadidos controles de apartado fuera de pregunta y cardinalidad de elección; detectan 80 apartados y 15 discrepancias sobre p5 en memoria. Son hallazgos graves y ahora bloquean publicar.
- CLI `banco`/`publicar` acepta `--rubricas` y `--soluciones` para escoger las nuevas ejecuciones sin fallback silencioso. Pruebas de integración en temporales verifican selección y compatibilidad anterior.
- Nuevo dominio `conservacion.py` y aplicación `verificacion.py`: cotejo extracción→banco, estados por examen/pregunta en informe, huellas, exclusiones explícitas, existencia de fuentes/figuras y comparación de cobertura con banco publicado. CLI `pau verificar` sin IA. `publicar` bloquea antes de sustituir datos y usa copia temporal/respaldo con recuperación.
- Barrido actual: 19 exámenes con controles superados, 247 pendientes, principalmente pérdidas conocidas de instrucciones y literales en el constructor. No es tasa de transcripción correcta. Resumen/CSV/script en `docs/verificacion-2026-09-29/`; explicación en `docs/verificacion-banco.md`.
- Suite pipeline: 136 tests pasan con Node 22. Revisiones detectaron y se corrigieron pérdidas de cobertura por archivo desaparecido, duplicados y omisión de criterios generales sin rúbricas por nodo. Sin build; un subagente ejecutó Ruff en host incumpliendo el procedimiento, no se usa como gate de entrega.
- Cinco respuestas completadas, sin reintentos automáticos, con script `docs/evaluacion-prompts-2026-09-29/ejecutar.py`. Primer intento sandbox falló sin uso; la autorización técnica para continuar tardó y el agente fue interrumpido para recuperar estado. El lote final de cuatro se ejecutó en paralelo desde raíz (sesión 77055, terminada con exit 0), comprobando antes que no hubiese procesos de extracción previos. No quedan llamadas en curso.
- Resultados: p6 fda conserva 6 preguntas y 24 apartados; p6 0b7 recupera 4.2 a/b; r3 070 conserva bandas 0–5 sin sumarlas; s2 academia 25f recupera raíz cuarta y 69,5. Control positivo s2 oficial 1bc conserva resultados pero pierde sustitución intermedia en n26. Su n12 reproduce ambigüedad literal de la fuente; no atribuirla a un error nuevo del modelo. S2 academia omite también un paso factorial en n13 y un pequeño gráfico en n19 sin advertirlo. El informe recoge el alcance dirigido, sin tasa global.
- Consumo de las cinco respuestas: 83.961 tokens de entrada + 55.674 de salida = 139.635 en total. No coste monetario calculado sin tarifa verificada. Informe/evidencias en `docs/evaluacion-prompts-2026-09-29/README.md`; prompts por defecto intactos.
- Las 431 extracciones originales se conservaron durante la evaluación. `datos/` se reparó después de forma acotada para PAU-REV-03/04; huellas de JSON antes/después en `docs/correcciones-2026-09-29/plan.json`. Las nuevas salidas y los informes están en subdirectorios nuevos.
- HEAD revisado `2ceef10b24ea13410d1a17ffa3ff45e18d78432e`. Cambios locales incluyen prompts, validación, CLI/publicación, tests y documentación; no hay commit/PR nuevo.

- Rediseño web implementado: dos columnas lista/detalle, modal de filtros con borrador/aplicar/cancelar y foco, documentos plegados al pie con carga diferida y saltos al PDF correcto, controles y superficies redondeados. Criterios generales conservados al pie y correcciones por nodo intactas.
- Tema Sistema por defecto con `prefers-color-scheme` en vivo; Claro/Oscuro persistidos y vuelta a Sistema. Probado con almacenamiento bloqueado.
- Web: 78 tests pasan, tipos, lint y build con prerender de `/` y `/catalogo` en contenedor. QA visual Chrome en escritorio y 390×844: filtros/recuento/aplicación/Escape, temas, detalle móvil y PDF real con franja. Sin nuevas llamadas IA.
- Servidor local en `http://127.0.0.1:3100/` (Vite, sesión 27876); pestaña Chrome 377482858 abierta y tema Sistema. Cambios sin commit.

- Correcciones actuales: DOMPurify 3.4.16 en la inserción final de Markdown (fallback de texto sin DOM, KaTeX trust:false); parser recupera opción D y emparejador acepta catálogo antiguo sin recrear el vínculo erróneo; banco/ficha conservan regla propia y literal bilingüe.
- Datos: 80 reglas y 79 literales incorporados; vínculo `e880b6f47a91`→`2337676aef2a` retirado del catálogo y 11 fichas. 2.697 preguntas/4.633 documentos conservados. `data/examenes.json` actualizado por rastreo SIN RED. No PDF borrado ni extracción reejecutada.
- Excepción local al banco existente documentada: script `docs/correcciones-2026-09-29/aplicar.py` solo admite IDs y huellas cerradas de `plan.json`. Idempotente y recuperación que no pisa ediciones externas. No modifica `exigir_conservacion` ni permite publicación completa con pendientes.
- Última validación: 139 tests Python (host, Node22) y 96 web (contenedor), Ruff/Biome/tipos/build pasan. Revisión Standards/Spec sin pendientes tras corregir guardas del reparador. Ficha de ejemplo verificada en navegador en es/va.

## Decisiones y porqués

- Separar errores de Luna, fuente, pipeline y web: varios fallos no se resolverían cambiando el modelo.
- Usar `datos/preguntas.json` como banco vigente: el agregado de `pipeline/salida/.../preguntas.json` es antiguo (58 exámenes), no representa los 266 publicados.
- No asignar tasa de precisión: los controles mecánicos cubren todo, pero el cotejo semántico es dirigido y no una muestra representativa etiquetada.
- No dar por aprobadas filas sin hallazgos: solo significan ausencia de alerta con el método utilizado.
- La cautela inicial de no volcar las 587 respuestas r2 sin filtros se concreta, tras autorización del usuario, en recuperación de 479 y exclusiones explícitas. No equivale a cotejo académico exhaustivo.
- Preservar extracciones originales; las correcciones locales posteriores autorizadas se registran separadas de la auditoría histórica.
- Mantener candidatos optativos hasta comparación contra PDF: una instrucción nueva y tests de código no prueban mejor fidelidad del modelo.

## Hipótesis descartadas

- Todos los avisos de puntuación implican error: en Historia, sumar alternativas produce 13/14 donde el alumno elige un subconjunto de 10.
- `contiene_soluciones=false` equivale a pérdida: los diez s1 negativos contienen criterios, no respuestas concretas.
- KaTeX válido implica matemática correcta: los tres cambios graves son fórmulas sintácticamente admisibles.
- PDF y figura existentes implican correspondencia: hay anexos de otro examen e imágenes de otra pregunta sin referencias rotas.
- Los 12 apartados A de Matemáticas 2019 los omitió Luna: `fuente.desde=6` excluye la p. 5 antes de llamar al modelo.
- Marca de academia prueba autoría privada: solo se registra oficialidad pendiente de acreditar en los dos casos señalados.
- Los 55 elementos del índice son 55 bugs distintos de Luna: incluyen solapamientos, limitaciones y problemas de procedencia.

## Pendientes

- Ampliar la evaluación antes de activar defaults; corregir la omisión de pasos de s2 sin sobrescribir el prompt ya utilizado (conservar trazabilidad). No consumir más llamadas automáticamente; ampliar evaluación requiere alcance posterior.
- El control bloquea pérdidas; todavía no corrige el constructor para conservar instrucciones/literales ni adapta la web. Tampoco certifica corrección matemática o correspondencia de anexos.
- Para seguir corrigiendo el pipeline, aplicar el orden del informe: identidad/anexos y página inicial → jerarquía/completitud → matemáticas → figuras/partituras → semántica de rúbrica y publicación.
- Abrir el JSON de cada hallazgo y su PDF antes de editar. Los nodos y páginas están en los informes de área.
- Cerrar cada cambio con contraste fuente→salida→banco→vista; no marcar todo el documento como validado por arreglar un caso.
- Un cotejo literal exhaustivo de los 266 exámenes y todas las rúbricas sigue pendiente si se exige certificación completa; el informe no lo simula.
- Ampliar regresión del adaptador PDF.js antes de considerar completamente cerrado PAU-REV-02. PAU-REV-01/03/04 resueltos localmente.

## Gotchas descubiertos

- PDFs crudos están en `data/`, no `pipeline/data/`. Fuentes e intermedios están ignorados por Git; otra máquina necesita conservarlos para reproducir todo.
- `pipeline/.venv/bin/python` funciona con PyMuPDF; Pillow no está instalado. Las hojas se generan con PyMuPDF.
- El Node por defecto falla; usar `/opt/homebrew/opt/node@22/bin/node`. No ejecutar build/lint en host según instrucciones del workspace.
- `incrustado_por_texto` no reconoce ciertos acentos/glifos separados; `combinar` prioriza una detección tardía sobre la salida del modelo. Caso `184bfaad518f`.
- Hay DOS poblaciones diferentes de tamaño 80: apartados mal anidados y preguntas cuya elección propia se pierde al publicar.
- Las 223/227 transcripciones s1 publicadas idénticas incluyen errores del modelo: igualdad de salida no es calidad.

- Validación web aislada en `/tmp/pau-ui-validation/web` de `zetesisportal_devcontainer-app-1`, con dependencias Linux propias y copia de datos publicados. No está montado directamente `pau-poc`; sincronizar antes de repetir checks.
- Al copiar con tar desde macOS usar `COPYFILE_DISABLE=1` y excluir `._*`: los metadatos AppleDouble se detectan como tests y rompen parsers.

- El contenedor ZP usa musl/Alpine: PyMuPDF intenta compilar sin cc y su instalador puede volcar el entorno. Para Ruff usar uvx con entorno mínimo; pruebas Python con venv local y Node22. No capturar env de aplicaciones ni logs de ese instalador.

## Referencias

- `docs/auditoria-2026-09-29/README.md`
- `docs/prompts-extraccion.md`
- `docs/verificacion-banco.md`
- `docs/verificacion-2026-09-29/resumen.json`
- `docs/evaluacion-prompts-2026-09-29/README.md`
- `docs/auditoria-2026-09-29/hallazgos.json`
- `docs/auditoria-2026-09-29/estado-examenes.csv`
- `docs/auditoria-2026-09-29/general/inventario.csv`
- `docs/revision-2026-09-29.md`
- `2ceef10b24ea13410d1a17ffa3ff45e18d78432e`

- `docs/correcciones-2026-09-29/README.md`
- `docs/saneado-html.md`
