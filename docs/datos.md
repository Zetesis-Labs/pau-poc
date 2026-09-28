# Contrato del conjunto publicado (`datos/`)

`datos/` es lo único que la web consume y lo único del corpus que se versiona. Lo
escribe `pau publicar` a partir de una ejecución de extracción; nunca se edita a mano.

```
datos/
  catalogo.json        todos los documentos rastreados (metadatos y enlace de origen)
  preguntas.json       banco de preguntas de los exámenes procesados
  figuras/<nombre>.png recortes de las figuras de las preguntas
  pdfs/<docid>.pdf     solo los PDF de exámenes procesados
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
    "apartados": [Apartado],         // recursivo: { etiqueta, enunciado, puntos, estimulos: [id], regla, apartados }
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

`Textos` es un objeto `{ [idioma]: markdown }` con idiomas `es`, `va`, `eu`, `en`, `fr`, …

## `Anexo`: la corrección de un examen

Criterios de corrección o soluciones vinculados a un examen. Van ordenados de más a menos fiable: primero lo que
viene dentro del propio PDF, luego lo oficial, los criterios antes que las soluciones y lo accesible antes que lo
privado o roto. Ningún anexo suelto se publica en `pdfs/`: se enlaza a su origen.

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
  // o corrección dentro del PDF del examen, a partir de esa página:
  "incrustado": { "pagina": 3 }
}
```

El vínculo se hace por región, asignatura, año y convocatoria, y dentro de eso por variante (opción A/B,
coincidencias…): variantes distintas no se vinculan nunca. La página de la corrección incrustada sale de la extracción
en los exámenes procesados (primera página tras el último enunciado) y de `pau anexos`, que busca sus títulos en el
texto, en el resto.
