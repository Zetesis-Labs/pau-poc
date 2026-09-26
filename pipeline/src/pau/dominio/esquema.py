"""Contrato de extracción de preguntas.

El examen es un árbol, pero las salidas estructuradas no admiten esquemas
recursivos: se representa como lista plana de nodos con referencia al padre.
"""

from typing import Literal

from pydantic import BaseModel, Field

VERSION = "v3"

Idioma = Literal["es", "eu", "va", "ca", "en", "fr", "de", "it", "pt", "la", "grc", "otro"]


class Texto(BaseModel):
    idioma: Idioma
    markdown: str = Field(description="Texto literal en Markdown. Fórmulas en LaTeX compatible con KaTeX: $…$ en línea, $$…$$ en bloque; química con \\ce{…}.")


class Pagina(BaseModel):
    idioma: Idioma
    pagina: int = Field(description="Página física del PDF, empezando en 1.")


class Recorte(BaseModel):
    idioma: Idioma
    pagina: int = Field(description="Página física del PDF, empezando en 1.")
    x0: float = Field(description="Borde izquierdo, fracción del ancho de la página (0 = izquierda, 1 = derecha).")
    y0: float = Field(description="Borde superior, fracción del alto de la página (0 = arriba, 1 = abajo).")
    x1: float = Field(description="Borde derecho, fracción del ancho.")
    y1: float = Field(description="Borde inferior, fracción del alto.")


class Estimulo(BaseModel):
    id: str = Field(description="Identificador corto: E1, E2…")
    tipo: Literal["texto", "figura", "tabla", "grafica", "mapa", "partitura", "audio", "otro"]
    paginas: list[Pagina] = Field(description="Dónde aparece, una entrada por idioma.")
    descripcion: str = Field(description="Qué es y qué muestra, para localizarlo y entenderlo sin verlo.")
    contenido: list[Texto] = Field(description="Transcripción literal si es texto o tabla; vacío si es una imagen.")
    recortes: list[Recorte] = Field(description="Rectángulo que contiene la figura completa en la página, uno por cada vez que aparece (por ejemplo, una por idioma). Vacío para estímulos de solo texto.")


class ReglaEleccion(BaseModel):
    minimo: int | None = Field(description="Mínimo de hijos que debe responder; null si no se indica.")
    maximo: int | None = Field(description="Máximo de hijos que puede responder o que se corrigen. Si hay que responder exactamente N, minimo = maximo = N.")
    de: int | None = Field(description="Entre cuántos hijos elige.")
    agregacion: Literal["suma", "media"] = Field(description="Cómo se combinan las notas de los hijos respondidos: 'suma' (lo habitual) o 'media' si el examen dice que la nota es la media.")
    literal: list[Texto] = Field(description="La instrucción tal como aparece, por idioma.")


class Nodo(BaseModel):
    id: str = Field(description="Identificador corto y único: n1, n2…")
    padre: str | None = Field(description="id del nodo padre; null para los nodos de primer nivel.")
    tipo: Literal["bloque", "opcion", "pregunta", "apartado"]
    etiqueta: list[Texto] = Field(description="Etiqueta tal como aparece impresa, por idioma: 'Opción A' / 'Opció A', '3', 'b)'.")
    sintetico: bool = Field(description="true si el nodo no existe como tal en el examen y lo creas para agrupar (por ejemplo, para dar su regla a un grupo de preguntas).")
    orden: int = Field(description="Posición entre sus hermanos, empezando en 1.")
    enunciado: list[Texto] = Field(description="Enunciado propio del nodo, una entrada por idioma en que aparece. Sin el texto de sus hijos.")
    puntos: float | None = Field(description="Puntuación máxima indicada en el examen para este nodo; null si no aparece.")
    eleccion: ReglaEleccion | None = Field(description="Regla que se aplica a los hijos de este nodo; null si hay que responderlos todos y se suman.")
    estimulos: list[str] = Field(description="ids de los estímulos que necesita este nodo.")
    paginas: list[Pagina] = Field(description="Página donde empieza el nodo, una entrada por idioma.")


class ExamenExtraido(BaseModel):
    es_examen: bool = Field(description="false si el PDF no contiene el enunciado de un examen.")
    idiomas: list[Idioma]
    paginas_enunciado: list[int] = Field(description="Páginas que contienen enunciados; excluye criterios y soluciones.")
    otro_contenido: list[Literal["portada", "instrucciones", "criterios", "soluciones", "hoja_respuestas", "otro"]]
    instrucciones: list[Texto] = Field(description="Instrucciones generales del examen, literales.")
    eleccion_raiz: ReglaEleccion | None = Field(description="Regla de elección entre los nodos de primer nivel.")
    puntuacion_total: float | None = Field(description="Puntuación total declarada en el examen, si aparece.")
    estimulos: list[Estimulo]
    nodos: list[Nodo]
    incidencias: list[str] = Field(description="Todo lo que no encaja en este esquema o genera dudas. Vacío si nada.")
