"""Parser puro de selectividad.academy: índice JSON de exámenes."""

import json

from pau.dominio.documento import Documento, asignatura_canonica

FUENTE = "selectividad.academy"
DATOS = "https://www.selectividad.academy/data/examenes-cache.json"
ALMACEN = "https://tlncyaczduqxaujxjivu.supabase.co/storage/v1/object/public/examenes-pdf/"
INDICE = "https://www.selectividad.academy/examenes/pais-vasco"
PAGINA = "https://www.selectividad.academy/examenes/{ccaa}/{asignatura}/{year}-{convocatoria}"
REGIONES = {"pais-vasco": "País Vasco"}


def parse(texto: str) -> list[Documento]:
    documentos = []
    for fila in json.loads(texto):
        region = REGIONES.get(fila["ccaa"])
        if region is None:
            continue
        slug_web = fila["storage_path"].split("/")[3]
        documentos.append(
            Documento(
                region=region,
                fuente=FUENTE,
                pagina=PAGINA.format(**{**fila, "asignatura": slug_web}),
                asignatura=asignatura_canonica(fila["asignatura"].replace("-", " ")),
                anio=fila["year"],
                convocatoria=fila["convocatoria"],
                tipo="examen",
                url=ALMACEN + fila["storage_path"],
                titulo=f"{fila['asignatura'].replace('-', ' ').capitalize()} {fila['year']} {fila['convocatoria']}",
            )
        )
    return documentos
