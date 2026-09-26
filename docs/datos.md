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
    "pdf": "pdfs/ac1e68a880cb.pdf"  // solo si procesado
  }]
}
```

## `preguntas.json`

```jsonc
{
  "ejecucion": "gpt-6-luna__p5",   // modelo__prompt que produjo la extracción
  "preguntas": [{
    "id": "012555da3d70:n3",         // <docid>:<nodo>
    "examen": { "id", "region", "asignatura", "anio", "convocatoria", "tipo", "fuente", "url", "pdf" },
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
