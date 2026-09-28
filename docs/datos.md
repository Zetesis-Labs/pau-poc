# Contrato del conjunto publicado (`datos/`)

`datos/` es lo único que la web consume y lo único del corpus que se versiona. Lo
escribe `pau publicar` a partir de una ejecución de extracción; nunca se edita a mano.

```
datos/
  catalogo.json        todos los documentos rastreados (metadatos y enlace de origen)
  preguntas.json       banco de preguntas de los exámenes procesados
  figuras/<nombre>.png recortes de las figuras de las preguntas
  pdfs/<docid>.pdf     los PDF de los exámenes procesados y de sus anexos sueltos públicos
```

Las rutas dentro de los JSON son relativas a `datos/`.

## `catalogo.json`

```jsonc
{
  "generado": "2026-09-26T03:00:00Z",
  "fuentes": { "uc3m": { "region": "Madrid", "url": "https://…" } },
  "documentos": [{
    "id": "ac1e68a880cb",
    "region": "Madrid",
    "fuente": "uc3m",
    "pagina": "https://…",          // página donde se encontró
    "asignatura": "Lengua Castellana y Literatura II",
    "anio": 2026,
    "convocatoria": "ordinaria" | "extraordinaria" | "modelo" | "reserva" | "otra",
    "tipo": "examen" | "modelo" | "criterios" | "solucion" | "video" | "audio",
    "titulo": "…",
    "variante": "",
    "formato": "pdf" | "drive" | "gdoc" | "youtube" | "audio" | "web" | "carpeta",
    "url": "https://…",             // enlace de origen, siempre presente
    "descargable": true,
    "bytes": 297896,                // tamaño descargado, si se descargó
    "error": "HTTP 404",             // solo si la descarga falló
    "procesado": false,             // true si sus preguntas están en preguntas.json
    "pdf": "pdfs/ac1e68a880cb.pdf", // solo si procesado
    "anexos": [Anexo]               // solo en exámenes y modelos con alguna corrección vinculada
  }]
}
```

## `preguntas.json`

```jsonc
{
  "ejecucion": "gpt-6-luna__p5",   // modelo__prompt que produjo la extracción
  "preguntas": [{
    "id": "012555da3d70:n3",         // <docid>:<nodo>
    "examen": { "id", "region", "asignatura", "anio", "convocatoria", "tipo", "fuente", "url", "pdf", "anexos": [Anexo] },
    "reglaExamen": "elegir 2 de 4",  // "" si no hay
    "contexto": [{ "etiqueta": Textos, "tipo": "bloque" | "opcion" | "pregunta", "enunciado": Textos, "regla": "", "sintetico": false }],
    "etiqueta": Textos,
    "enunciado": Textos,             // markdown + LaTeX (KaTeX, mhchem)
    "puntos": 2.5 | null,
    "rubrica": Rubrica | null,       // lo que dicen los criterios oficiales de este nodo
    "solucion": Solucion | null,     // la respuesta de este nodo: oficial si la hay, de academia si no
    "criteriosGenerales": Textos,    // criterios que valen para todo el examen; {} si no hay
    "fuenteRubrica": { "tipo": "criterios" | "solucion", "incrustado": true } | { "tipo", "incrustado": false, "url", "pdf" } | null,
    "apartados": [Apartado],         // recursivo: { etiqueta, enunciado, puntos, estimulos: [id], regla, rubrica, solucion, apartados }
    "idiomas": ["es", "va"],
    "estimulos": [{
      "id": "E1",
      "tipo": "texto" | "figura" | "grafica" | "tabla" | "mapa" | "partitura" | "otro" | "…",
      "descripcion": "…",
      "contenido": Textos,
      "figuras": [{ "src": "figuras/012555da3d70_E1_es_1.png", "idioma": "es" }]
    }],
    "paginas": { "es": 4, "va": 2 },
    "anclas": { "es": { "pagina": 4, "y0": 0.30, "y1": 0.33 } }  // fracciones de alto de página; y0/y1 null si no se localizó
  }]
}
```

`Rubrica` es `{ "puntos": 1.5 | null, "criterios": Textos, "desglose": [{ "descripcion": Textos, "puntos": 0.5 }], "paginas": { "es": 6 } }`:
puntos que dan los criterios (pueden no coincidir con los del enunciado), qué valora el corrector, cómo reparte los puntos
y en qué página del documento de criterios está (del propio PDF si `fuenteRubrica.incrustado`). Se extrae en una etapa
aparte (`pau rubricas`, prompt `r2`) con el árbol del examen ya extraído, y solo de fuentes oficiales.

`Solucion` es `{ "texto": Textos, "origen": "oficial" | "academia", "fuente": "mundoestudiante", "incrustado": false, "url": "https://…", "pdf": "pdfs/…", "paginas": { "es": 2 } }`:
la respuesta literal del documento del que sale, con su procedencia (`url` y `pdf` solo si no va dentro del PDF del examen).
Se extrae en otra etapa (`pau soluciones`, prompt `s1`): primero `--origen oficial` y después `--origen academia`, que
solo se consulta para los exámenes en los que lo oficial deja preguntas sin respuesta.

`Textos` es un objeto `{ [idioma]: markdown }` con idiomas `es`, `va`, `eu`, `en`, `fr`, …

## `Anexo`: la corrección de un examen

Criterios de corrección o soluciones vinculados a un examen. Van ordenados de más a menos fiable: primero lo que
viene dentro del propio PDF, luego lo oficial, los criterios antes que las soluciones y lo accesible antes que lo
privado o roto. Los anexos sueltos de los exámenes procesados que son públicos y están descargados en PDF se publican
en `pdfs/` y llevan `pdf`; el resto (privados, rotos, páginas web) solo se enlaza a su origen.

```jsonc
{
  "tipo": "criterios" | "solucion",   // lo principal
  "contenido": ["criterios", "solucion"], // todo lo que trae: la corrección incrustada puede traer ambos
  "origen": "oficial" | "academia",   // criterios siempre oficiales; soluciones oficiales solo de uc3m, ehu y umh
  "fuente": "llibreta",
  "acceso": "publico" | "privado" | "roto",
  "coincidencia": "exacta" | "por_clave", // por_clave: misma asignatura, año y convocatoria, pero una de las dos partes sin variante
  // anexo suelto, con su propio documento en el catálogo:
  "id": "0f6f289bd62a", "url": "https://…", "titulo": "…",
  "pdf": "pdfs/0f6f289bd62a.pdf",     // solo si es público y está descargado en PDF
  // o corrección dentro del PDF del examen, a partir de esa página:
  "incrustado": { "pagina": 3 }
}
```

El vínculo se hace por región, asignatura, año y convocatoria, y dentro de eso por variante (opción A/B,
coincidencias…): variantes distintas no se vinculan nunca. La página de la corrección incrustada sale de la extracción
en los exámenes procesados (primera página tras el último enunciado) y de `pau anexos`, que busca sus títulos en el
texto, en el resto.
