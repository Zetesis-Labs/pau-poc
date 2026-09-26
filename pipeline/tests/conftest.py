from pau.dominio.esquema import ExamenExtraido, Nodo, ReglaEleccion, Texto


def texto(md: str, idioma: str = "es") -> list[Texto]:
    return [Texto(idioma=idioma, markdown=md)]


def nodo(
    id: str, padre: str | None = None, tipo: str = "pregunta", orden: int = 1, enunciado: str = "Enunciado de prueba",
    puntos: float | None = None, eleccion: ReglaEleccion | None = None, etiqueta: str | None = None,
) -> Nodo:
    return Nodo(
        id=id, padre=padre, tipo=tipo, etiqueta=texto(etiqueta or str(orden)), sintetico=False, orden=orden,
        enunciado=texto(enunciado) if enunciado else [], puntos=puntos, eleccion=eleccion, estimulos=[], paginas=[],
    )


def examen(*nodos: Nodo, **extra) -> ExamenExtraido:
    base = dict(
        es_examen=True, idiomas=["es"], paginas_enunciado=[1], otro_contenido=[], instrucciones=[],
        eleccion_raiz=None, puntuacion_total=None, estimulos=[], nodos=list(nodos), incidencias=[],
    )
    return ExamenExtraido(**{**base, **extra})


def regla(minimo: int, maximo: int, de: int, agregacion: str = "suma") -> ReglaEleccion:
    return ReglaEleccion(minimo=minimo, maximo=maximo, de=de, agregacion=agregacion, literal=[])
