"""Dónde vive cada cosa. La raíz del repo se puede cambiar con PAU_RAIZ."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Rutas:
    raiz: Path

    @property
    def data(self) -> Path:
        return self.raiz / "data"

    @property
    def examenes(self) -> Path:
        return self.data / "examenes.json"

    @property
    def incrustados(self) -> Path:
        return self.data / "incrustados.json"

    @property
    def cache_html(self) -> Path:
        return self.data / "cache" / "html"

    @property
    def salida(self) -> Path:
        return self.raiz / "pipeline" / "salida"

    @property
    def prompts(self) -> Path:
        return self.raiz / "pipeline" / "prompts"

    @property
    def lotes(self) -> Path:
        return self.raiz / "pipeline" / "lotes"

    @property
    def datos(self) -> Path:
        return self.raiz / "datos"

    def ejecucion(self, nombre: str) -> Path:
        return self.salida / nombre


def rutas_por_defecto() -> Rutas:
    return Rutas(Path(os.environ.get("PAU_RAIZ", Path(__file__).resolve().parents[4])))
