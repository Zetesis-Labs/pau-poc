# Auditoría de figuras y partituras

Se inspeccionaron visualmente las **292 imágenes publicadas**, distribuidas en las 15 hojas `contacto-01.png` a `contacto-15.png`. Las hojas sirven para cribar recortes vacíos, texto inesperado y cortes visibles. Se contrastaron páginas originales completas en los casos de la tabla. **Ver una miniatura no certifica que todos sus símbolos, márgenes o rótulos sean correctos**. No se cotejaron una por una todas las figuras contra la página original.

El inventario geométrico reconstruye los 311 planes p5 con el código actual, sin modificar fuentes: 299 producen imagen, 292 están publicadas y 12 se descartan por `casi-pagina`. Las siete imágenes generadas sin publicación y los duplicados exactos son pistas, no siete errores ni copias indebidas demostradas. Hay 252 hashes distintos entre las 292 imágenes: varias versiones lingüísticas pueden compartir legítimamente el dibujo.

## Errores contrastados

| ID | Documento / estímulo / página | Evidencia e impacto | Causa localizada |
| --- | --- | --- | --- |
| FIG-01 · P1 | `184bfaad518f`, E1, p. 2 | El estímulo describe la gráfica de la pregunta 2. El recorte publicado muestra texto de las preguntas 3 y 4, situado más abajo. Falta la gráfica que debe interpretar el alumno. | Coordenadas p5 erróneas; método guardado `modelo`. |
| FIG-02 · P1 | `1f06fc98f001`, E2/E3, p. 2 | Los recortes empiezan sobre el texto y terminan antes de completar las gráficas de Física; cortan la zona inferior y ejes necesarios para leerlas. | Coordenadas p5 demasiado altas; método `modelo`. |
| FIG-03 · P1 | `fdd6ca513f80`, E5, p. 7 | El original contiene la pieza A2 de Dibujo Técnico. La imagen publicada es la casilla de identificación del alumno. La caja propuesta estaba en la zona superior derecha, cerca de la pieza; el ajuste `pdf` la desplaza a `[271.3,22.1,563.3,82.1]` puntos. | El ajuste geométrico selecciona un objeto ajeno al dibujo. No atribuir todo el fallo a Luna. |
| FIG-04 · P1 | `61e34b1b42fa`, E4/E5, p. 2 | E4 describe producción siderúrgica pero contiene la tabla de electrodomésticos de otra pregunta. E5 solo conserva la última fila, 1970, de esa segunda tabla. | Cajas p5 demasiado bajas y ajuste PDF que acepta contenido incorrecto. |
| FIG-05 · P1 | `9c4cbc92103b`, E2/E3, p. 4 | E2 describe jóvenes con móviles pero recorta el conejo de otra pregunta. E3, que debería contener ese conejo, muestra el borde inferior casi vacío. | Coordenadas p5 equivocadas; que una caja esté dentro de la página no prueba correspondencia. |
| FIG-06 · P2 | `03364198c8fb`, E2, p. 4 | La primera de cuatro posiciones de la niña queda cortada casi por completo; solo se ven sus pies. | Caja p5 recorta por arriba parte esencial del conjunto. |
| FIG-07 · P1 | `67eea232db63`, E2, p. 3 | La vista de Dibujo Técnico continúa hacia la zona superior izquierda; el recorte empieza por debajo y elimina parte de su contorno. | Caja p5 incompleta. No se extiende este juicio a las otras vistas sin comparación individual. |
| FIG-08 · P1 | `4a7c96ae2912`, E1/E2, pp. 5–12; `3068d1110070`, E3, pp. 7–10 | Se rechazan **12 páginas de partituras** porque las cajas ocupan casi toda la página. Páginas representativas 5 y 7 renderizadas: son partituras reales. Los doce planes constan como `casi-pagina` y no se publican. | `pipeline/src/pau/dominio/geometria.py:109` trata todo recorte de gran área como inválido. Luna sí identificó estas partituras. |
| FIG-09 · P1 | `3068d1110070`, E2, pp. 4–6 | Tres páginas de Mahler están publicadas con idioma `de`, pero el examen ofrece idioma `es`. `figurasDe(figuras,"es")` devuelve solo la primera por `slice(0,1)`: dos páginas quedan fuera de la vista. | Fallback de `web/src/dominio/banco.ts:200`. Confirmación por datos y ejecución de la función; sin prueba visual en navegador. |

Las páginas originales renderizadas se guardan como `<documento>-pagina-<n>.png`. Para FIG-08 se contrastaron visualmente páginas representativas, no cada compás de las doce. FIG-09 es independiente del rechazo de las cuatro páginas de Ravel: las tres de Mahler sí tienen archivos, pero la interfaz selecciona solo uno.

## Qué debe comprobarse al corregir

- Correspondencia entre descripción, pregunta y contenido de la imagen, además de geometría válida y archivo existente.
- Conservación de todos los elementos necesarios: ejes, leyendas, escala, cotas, notas, compases y filas de tablas.
- El ajuste geométrico no debe reemplazar una figura por un encabezado, casilla o figura vecina.
- Admitir estímulos legítimos que ocupan una página, especialmente partituras; conservar su secuencia completa.
- Si no existe el idioma solicitado, elegir una versión lingüística completa, no una sola página.

`revision-visual.json` deja una fila por imagen publicada y el alcance de la inspección. `hallazgos.json` identifica las excepciones demostradas; su ausencia no equivale a aprobación. `geometria.json` conserva las cajas del modelo, las recalculadas, método, página y problemas. `contactos.json` permite localizar cada imagen en su hoja.

Para reproducir el inventario y las hojas: `pipeline/.venv/bin/python docs/auditoria-2026-09-29/figuras/revisar.py`. Las observaciones visuales son un registro de esta auditoría, no una inferencia automática del script.
