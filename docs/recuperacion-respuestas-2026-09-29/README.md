# Recuperación local de respuestas extraídas con rúbricas

El usuario autorizó recuperar respuestas existentes sin volver a extraer con IA.
El cruce del banco encontró 587 entradas r2 en nodos publicados sin solución,
repartidas entre 348 preguntas de 42 exámenes. No equivale a 587 ejercicios completos.

El plan incorpora **479 respuestas en 285 preguntas de 36 exámenes**. Las otras
108 candidatas quedan pendientes. Hay también 55 entradas r2 con solución ya publicada
y 10 en nodos no publicados; estas dos poblaciones no son parte de las 587 candidatas.

## Regla de recuperación

`pau.dominio.recuperacion.recuperar_respuestas` se usa tanto al construir el banco
como al verificar su conservación. La solución existente en el nodo o sus ancestros
tiene prioridad. Cada recuperación conserva el texto original y añade
`extraccion: "rubrica"`, con procedencia y páginas por idioma.

Se exige identidad del examen, fuente pública, origen conocido, correspondencia
exacta para anexos sueltos, nodo existente y respondible, texto no vacío y páginas
inequívocas para los idiomas de respuesta. Las respuestas duplicadas por nodo o idioma
se excluyen. Los idiomas adicionales de los criterios no se atribuyen a la respuesta.
Se registran motivos de exclusión; no se consideran errores las entradas de rúbrica
que solo contienen criterios y carecen de respuesta.

Se excluyen expresamente los anexos de autoría dudosa `c4afc8d9c75a` y `361720afddf5`,
los exámenes con correspondencia dudosa `5091bd5d23ad` y `ab690a84e30c`, y las referencias
incorrectas conocidas en `9c4cbc92103b:n21/n25`, `3c134e1125e6:n9` y `cdd0f4f759e1:n9`.
Evidencia: [auditoría de rúbricas](../auditoria-2026-09-29/rubricas/informe.md).
Una coincidencia exacta del catálogo no acredita por sí sola la correspondencia real.

## Aplicación al banco local existente

El publicador completo continúa bloqueando los problemas de conservación anteriores.
Esta reparación no desactiva ese control: cambia únicamente `solucion` en nodos
existentes de `datos/preguntas.json`. Conserva preguntas, orden, enunciados, rúbricas,
figuras, reglas, anexos y soluciones previas. No modifica el catálogo ni los resultados
originales de Luna. La web reconoce el documento de solución desde su procedencia,
sin reclasificar todos los documentos de criterios como solucionarios.

`plan.json` fija la huella del banco anterior y posterior, los IDs permitidos, las
huellas de cada solución y de los registros/PDF usados. Para cada respuesta añadida
se comprueba la identidad de la copia publicada del PDF y que sus páginas existen.
La correspondencia nodo→apartado se verifica por jerarquía, orden, etiqueta y enunciado.
El script rechaza cualquier cambio de entradas o resultado respecto al plan.

Desde la raíz, con la dependencia local `pau` instalada:

```bash
pipeline/.venv/bin/python docs/recuperacion-respuestas-2026-09-29/aplicar.py
pipeline/.venv/bin/python docs/recuperacion-respuestas-2026-09-29/aplicar.py --aplicar
```

La primera orden simula. La segunda reemplaza el único JSON de forma atómica, tras
volver a comprobar que no cambió durante la preparación. Repetirla sobre el resultado
es inocuo. Si el banco ha evolucionado después, el plan queda obsoleto y se rechaza.

Las comprobaciones de estructura, páginas y huellas no certifican cada frase ni
cálculo frente al PDF. Las respuestas se presentan como material extraído de criterios,
no como respuestas revisadas académicamente. No se ha llamado a la IA del pipeline.

## Comprobaciones posteriores

- 151 pruebas Python y 101 web; regresión de saltos cuando criterio y solución
  comparten PDF y página. Tipos, lint y build web en contenedor.
- Aplicación repetida: `ya_aplicado`, sin modificar nuevamente el JSON.
- Verificación de corpus: 20 exámenes con controles superados, 246 pendientes por
  hallazgos del conjunto; ningún examen pierde cobertura respecto al banco actualizado.
  [Informe](verificacion.json). Estos estados no son una tasa de exactitud académica.
- Ficha `cdd0f4f759e1:n2` comprobada en navegador: cuatro definiciones recuperadas;
  «ver en el PDF» abre Soluciones, página 4 de `a94284193403.pdf`.
