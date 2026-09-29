"""Comprueba pérdidas entre la extracción y el banco interno del mismo examen."""

from collections import Counter, defaultdict

from pau.dominio.banco import regla
from pau.dominio.rubrica import rubricas_por_nodo
from pau.dominio.validar import Hallazgo

VISUALES = {"figura", "grafica", "mapa", "partitura"}


def _por_idioma(textos: list[dict]) -> dict[str, str]:
    return {t["idioma"]: t["markdown"] for t in textos}


def _avisar(hallazgos: list[Hallazgo], codigo: str, detalle: str) -> None:
    hallazgos.append(Hallazgo(codigo, True, detalle))


def _campo(hallazgos: list[Hallazgo], id: str, campo: str, esperado: object, real: dict) -> None:
    if campo not in real or real[campo] != esperado:
        _avisar(hallazgos, "campo-alterado", f"{id}.{campo}")


def _literal(eleccion: dict | None) -> dict[str, str]:
    return _por_idioma(eleccion.get("literal", [])) if eleccion else {}


def _ancestros(nodo: dict, nodos: dict[str, dict]) -> list[dict]:
    camino, vistos = [], set()
    padre = nodo.get("padre")
    while padre in nodos and padre not in vistos:
        vistos.add(padre)
        actual = nodos[padre]
        camino.insert(0, actual)
        padre = actual.get("padre")
    return camino


def _descendientes(id: str, hijos: dict[str | None, list[dict]]) -> list[dict]:
    salida, pendientes, vistos = [], list(hijos.get(id, [])), {id}
    while pendientes:
        actual = pendientes.pop()
        if actual["id"] not in vistos:
            vistos.add(actual["id"])
            salida.append(actual)
            pendientes.extend(hijos.get(actual["id"], []))
    return salida


def _con_contenido(nodo: dict) -> bool:
    return bool(nodo.get("eleccion") or nodo.get("estimulos") or nodo.get("puntos") is not None
                or any(t["markdown"].strip() for t in nodo.get("etiqueta", []))
                or any(t["markdown"].strip() for t in nodo.get("enunciado", [])))


def _contexto_igual(fuente: dict, real: dict) -> bool:
    return (real.get("tipo") == fuente["tipo"] and real.get("etiqueta") == _por_idioma(fuente["etiqueta"])
            and real.get("enunciado") == _por_idioma(fuente["enunciado"]) and real.get("regla") == regla(fuente["eleccion"])
            and real.get("sintetico") == fuente.get("sintetico", False))


def _comprobar_contexto(hallazgos: list[Hallazgo], pregunta: dict, origen: dict, nodos: dict[str, dict], representados: set[str]) -> None:
    todos = _ancestros(origen, nodos)
    reales = pregunta.get("contexto", [])
    posicion = 0
    for fuente in todos:
        if not _con_contenido(fuente):
            if posicion < len(reales) and _contexto_igual(fuente, reales[posicion]):
                representados.add(fuente["id"])
                posicion += 1
            continue
        if posicion >= len(reales):
            _avisar(hallazgos, "contexto-alterado", f"{origen['id']}.contexto: falta {fuente['id']}")
            continue
        real = reales[posicion]
        posicion += 1
        representados.add(fuente["id"])
        for campo, valor in (("tipo", fuente["tipo"]), ("etiqueta", _por_idioma(fuente["etiqueta"])),
                             ("enunciado", _por_idioma(fuente["enunciado"])), ("regla", regla(fuente["eleccion"])),
                             ("sintetico", fuente.get("sintetico", False))):
            _campo(hallazgos, fuente["id"], f"contexto.{campo}", valor, {f"contexto.{campo}": real.get(campo)})
        if literal := _literal(fuente["eleccion"]):
            _campo(hallazgos, fuente["id"], "contexto.literalRegla", literal,
                   {"contexto.literalRegla": real.get("literalRegla")})
    if posicion < len(reales):
        _avisar(hallazgos, "contexto-alterado", f"{origen['id']}.contexto: entradas sobrantes")


def _comprobar_estimulos(hallazgos: list[Hallazgo], registro: dict, pregunta: dict, origen: dict, nodos: dict[str, dict], hijos: dict[str | None, list[dict]]) -> None:
    fuentes = {e["id"]: e for e in registro["resultado"].get("estimulos", [])}
    relacionados = [*_ancestros(origen, nodos), origen, *_descendientes(origen["id"], hijos)]
    usados = {id for n in relacionados for id in n.get("estimulos", [])}
    reales = {e.get("id"): e for e in pregunta.get("estimulos", [])}
    for id in usados - reales.keys():
        _avisar(hallazgos, "estimulo-omitido", f"{origen['id']}.estimulos.{id}")
    for id in reales.keys() - usados:
        _avisar(hallazgos, "estimulo-desconocido", f"{origen['id']}.estimulos.{id}")
    for id in usados & fuentes.keys():
        fuente = fuentes[id]
        figuras = [f for f in registro.get("figuras", []) if f.get("estimulo") == id]
        esperadas = {("figuras/" + f["archivo"], f["idioma"]) for f in figuras if f.get("archivo")}
        recortes_con_archivo = {(f["idioma"], f.get("pagina")) for f in figuras if f.get("archivo")}
        idiomas_con_figura = {idioma for idioma, _ in recortes_con_archivo}
        for figura in figuras:
            for problema in figura.get("problemas", []):
                _avisar(hallazgos, "recorte-con-problemas", f"{id}.figuras: {problema}")
        for recorte in fuente.get("recortes", []):
            idioma, pagina = recorte["idioma"], recorte.get("pagina")
            if pagina is not None and (idioma, pagina) not in recortes_con_archivo:
                _avisar(hallazgos, "figura-sin-imagen", f"{id}.figuras.{idioma}.pagina-{pagina}")
            elif pagina is None and idioma not in idiomas_con_figura:
                _avisar(hallazgos, "figura-sin-imagen", f"{id}.figuras.{idioma}")
        if not esperadas and not fuente.get("recortes") and (fuente["tipo"] in VISUALES or fuente["tipo"] == "tabla" and not fuente["contenido"]):
            _avisar(hallazgos, "figura-sin-imagen", f"{id}.figuras")
        if id not in reales:
            continue
        real = reales[id]
        for campo, valor in (("tipo", fuente["tipo"]), ("descripcion", fuente["descripcion"]),
                             ("contenido", _por_idioma(fuente["contenido"]))):
            _campo(hallazgos, id, campo, valor, real)
        if "figuras" not in real or {(f.get("src"), f.get("idioma")) for f in real["figuras"]} != esperadas:
            _avisar(hallazgos, "campo-alterado", f"{id}.figuras")


def comprobar_conservacion(registro: dict, preguntas: list[dict], rubrica: dict | None = None, soluciones: dict[str, dict] | None = None) -> list[Hallazgo]:
    """Señala pérdidas graves observables; no coteja el PDF ni juzga el contenido extraído."""
    hallazgos: list[Hallazgo] = []
    resultado = registro["resultado"]
    nodos = {n["id"]: n for n in resultado["nodos"]}
    hijos: dict[str | None, list[dict]] = defaultdict(list)
    for n in resultado["nodos"]:
        hijos[n["padre"]].append(n)
    entradas_vistas: set[str] = set()
    for entrada in rubrica["resultado"].get("entradas", []) if rubrica else []:
        id_entrada = entrada["nodo"]
        if id_entrada in entradas_vistas:
            _avisar(hallazgos, "rubrica-duplicada", id_entrada)
        entradas_vistas.add(id_entrada)
    rubricas, generales = rubricas_por_nodo(rubrica["resultado"]) if rubrica and rubrica["resultado"]["contiene_criterios"] else ({}, {})
    soluciones = soluciones or {}
    vistos: Counter[str] = Counter()
    representados: set[str] = set()
    prefijo = registro["documento"]["id"] + ":"

    def revisar_nodo(id: str, real: dict, padre: str | None, raiz: bool) -> None:
        vistos[id] += 1
        if id not in nodos:
            _avisar(hallazgos, "nodo-desconocido", id)
            return
        fuente = nodos[id]
        representados.add(id)
        if not raiz and fuente["padre"] != padre:
            _avisar(hallazgos, "padre-alterado", f"{id}.padre")
        for campo, valor in (("etiqueta", _por_idioma(fuente["etiqueta"])), ("enunciado", _por_idioma(fuente["enunciado"])),
                             ("puntos", fuente["puntos"]), ("regla", regla(fuente["eleccion"]))):
            if campo != "regla" or not raiz or fuente["eleccion"] is not None:
                _campo(hallazgos, id, campo, valor, real)
        if literal := _literal(fuente["eleccion"]):
            _campo(hallazgos, id, "literalRegla", literal, real)
        if not raiz:
            _campo(hallazgos, id, "estimulos", fuente["estimulos"], real)
        _campo(hallazgos, id, "rubrica", rubricas.get(id), real)
        _campo(hallazgos, id, "solucion", soluciones.get(id), real)
        for apartado in real.get("apartados", []):
            apartado_id = apartado.get("_nodo")
            if apartado_id is None:
                _avisar(hallazgos, "nodo-sin-id", f"{id}.apartados._nodo")
            else:
                revisar_nodo(apartado_id, apartado, id, False)

    for pregunta in preguntas:
        identificador = pregunta.get("id", "")
        id = identificador[len(prefijo):] if identificador.startswith(prefijo) else identificador
        if not identificador.startswith(prefijo):
            _avisar(hallazgos, "id-alterado", f"{identificador}: esperado {prefijo}")
        revisar_nodo(id, pregunta, None, True)
        if id not in nodos:
            continue
        fuente = nodos[id]
        _comprobar_contexto(hallazgos, pregunta, fuente, nodos, representados)
        _campo(hallazgos, id, "reglaExamen", regla(resultado.get("eleccion_raiz")), pregunta)
        if literal := _literal(resultado.get("eleccion_raiz")):
            _campo(hallazgos, id, "literalReglaExamen", literal, pregunta)
        if resultado.get("instrucciones"):
            _campo(hallazgos, id, "instruccionesExamen", _por_idioma(resultado["instrucciones"]), pregunta)
        _campo(hallazgos, id, "criteriosGenerales", generales, pregunta)
        _comprobar_estimulos(hallazgos, registro, pregunta, fuente, nodos, hijos)

    for n in resultado["nodos"]:
        id = n["id"]
        if n["tipo"] in {"pregunta", "apartado"}:
            if vistos[id] == 0:
                _avisar(hallazgos, "nodo-omitido", id)
            elif vistos[id] > 1:
                _avisar(hallazgos, "nodo-duplicado", id)
        elif id not in representados and _con_contenido(n):
            _avisar(hallazgos, "contexto-omitido", id)
    referenciados = {e for n in resultado["nodos"] for e in n.get("estimulos", [])}
    for id in {e["id"] for e in resultado.get("estimulos", [])} - referenciados:
        _avisar(hallazgos, "estimulo-sin-referencia", id)
    for id in rubricas:
        if id not in nodos or vistos[id] == 0:
            _avisar(hallazgos, "rubrica-sin-nodo", id)
    for id in soluciones:
        if id not in nodos or vistos[id] == 0:
            _avisar(hallazgos, "solucion-sin-nodo", id)
    return hallazgos
