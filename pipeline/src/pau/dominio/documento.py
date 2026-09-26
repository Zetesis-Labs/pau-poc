"""Documentos del catálogo y su clasificación a partir de textos y URLs."""

import hashlib
import re
import unicodedata
from dataclasses import asdict, dataclass
from urllib.parse import urlsplit

CONVOCATORIAS = ("ordinaria", "extraordinaria", "modelo", "reserva")
TIPOS = ("examen", "solucion", "criterios", "video", "modelo")


@dataclass(frozen=True)
class Documento:
    region: str
    fuente: str
    pagina: str
    asignatura: str
    anio: int | None
    convocatoria: str
    tipo: str
    url: str
    titulo: str
    variante: str = ""

    @property
    def id(self) -> str:
        return hashlib.sha1(f"{self.fuente}|{self.url}".encode()).hexdigest()[:12]

    def to_json(self) -> dict:
        return {"id": self.id, **asdict(self), "formato": formato(self.url), "descargable": url_descarga(self.url) is not None}


def formato(url: str) -> str:
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    if "ehutb.ehu.eus" in url:
        return "audio"
    if "drive.google.com/drive/folders" in url:
        return "carpeta"
    if "drive.google.com/file" in url:
        return "drive"
    if "docs.google.com/document" in url:
        return "gdoc"
    if urlsplit(url).path.endswith("/"):
        return "web"
    return "pdf"


def url_descarga(url: str) -> str | None:
    tipo = formato(url)
    if tipo == "pdf":
        return url
    identificador = re.search(r"/d/([\w-]+)", url)
    if tipo == "drive" and identificador:
        return f"https://drive.usercontent.google.com/download?id={identificador.group(1)}&export=download&confirm=t"
    if tipo == "gdoc" and identificador:
        return f"https://docs.google.com/document/d/{identificador.group(1)}/export?format=pdf"
    return None


def slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", plano(texto)).strip("-")


def ruta_local(documento: Documento) -> str:
    partes = [str(documento.anio or "sin-anio"), documento.convocatoria, documento.tipo, documento.variante, documento.fuente, documento.id]
    nombre = "-".join(slug(p) for p in partes if p)
    return f"pdfs/{slug(documento.region)}/{slug(documento.asignatura)}/{nombre}.pdf"


def limpiar(texto: str) -> str:
    return re.sub(r"\s+", " ", texto.replace("\xa0", " ")).strip()


def plano(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return limpiar(sin_tildes).lower()


ASIGNATURAS: list[tuple[str, str]] = [
    (r"matematicas? (aplicadas|ccss|cc\.? ?ss|.*sociales)|mat.*ccss|maaccss|matematicas-ccss|mates ccss", "Matemáticas Aplicadas a las CCSS II"),
    (r"matematicas? generales", "Matemáticas Generales"),
    (r"matematicas|mates", "Matemáticas II"),
    (r"historia de espana|historia-de-espana|espainiako historia|^historia$", "Historia de España"),
    (r"historia del arte|historia-del-arte|artearen historia|^arte$", "Historia del Arte"),
    (r"filosofia|filosofi", "Historia de la Filosofía"),
    (r"castellano|lengua castellana|lengua-castellana|^lengua$|gaztelania", "Lengua Castellana y Literatura II"),
    (r"valenci", "Valenciano"),
    (r"euskara|euskera|vasca", "Lengua Vasca y Literatura II"),
    (r"ingles|ingelesa|english", "Inglés"),
    (r"frances|frantsesa", "Francés"),
    (r"aleman|alemana", "Alemán"),
    (r"italiano", "Italiano"),
    (r"portugues", "Portugués"),
    (r"quimica|kimika", "Química"),
    (r"fisica|fisika", "Física"),
    (r"biologia", "Biología"),
    (r"geologia", "Geología y Ciencias Ambientales"),
    (r"ciencias.*tierra|ctma|medioambientales", "Ciencias de la Tierra y Medioambientales"),
    (r"ciencias generales", "Ciencias Generales"),
    (r"dibujo te[c]?nico|dibujo-tecnico|marrazketa", "Dibujo Técnico II"),
    (r"dibujo artistico", "Dibujo Artístico II"),
    (r"geografia|geografi", "Geografía"),
    (r"latin", "Latín II"),
    (r"griego", "Griego II"),
    (r"empresa y diseno|modelos de negocio", "Empresa y Diseño de Modelos de Negocio"),
    (r"economia|ekonomia", "Economía de la Empresa"),
    (r"fundamentos (del )?art|fundamentos-del-arte", "Fundamentos Artísticos"),
    (r"artes escenicas", "Artes Escénicas II"),
    (r"cultura audiovisual", "Cultura Audiovisual"),
    (r"analisis musical", "Análisis Musical II"),
    (r"historia de la musica|musica y la danza", "Historia de la Música y de la Danza"),
    (r"diseno", "Diseño"),
    (r"lenguaje y practica musical|practica musical", "Lenguaje y Práctica Musical"),
    (r"tecnologia", "Tecnología e Ingeniería II"),
    (r"quimica", "Química"),
    (r"tecnicas de expresion", "Técnicas de Expresión Gráfico-Plástica"),
    (r"coro", "Coro y Técnica Vocal II"),
    (r"movimientos culturales", "Movimientos Culturales y Artísticos"),
]


def asignatura_canonica(texto: str) -> str:
    t = plano(texto)
    for patron, nombre in ASIGNATURAS:
        if re.search(patron, t):
            return nombre
    return limpiar(texto).title()


MESES = {"junio": "ordinaria", "julio": "extraordinaria", "septiembre": "extraordinaria"}
"""En 2020 (COVID) la ordinaria fue en julio y la extraordinaria en septiembre."""


def convocatoria_de(texto: str) -> str:
    t = plano(texto)
    if "modelo" in t:
        return "modelo"
    if "reserva" in t:
        return "reserva"
    if "extraordinaria" in t or "ez ohiko" in t:
        return "extraordinaria"
    if "2a convocatoria" in t or "2ª convocatoria" in t:
        return "extraordinaria"
    if "ordinaria" in t or "ohiko" in t:
        return "ordinaria"
    if "julio" in t and re.search(r"\b2020\b", t):
        return "ordinaria"
    for mes, conv in MESES.items():
        if mes in t:
            return conv
    return "otra"


def anio_de(texto: str) -> int | None:
    curso = re.search(r"(20\d\d)\s*[-/]\s*(20)?(\d\d)", texto)
    if curso:
        return int(curso.group(1)) + 1
    suelto = re.findall(r"20\d\d", texto)
    return int(suelto[-1]) if suelto else None
