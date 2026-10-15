"""Read persisted contracts without treating corruption as an absent artifact."""
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)
ArtifactState = Literal['available', 'not_generated', 'invalid', 'unavailable', 'stale']


@dataclass(frozen=True)
class ArtifactRead(Generic[T]):
    state: ArtifactState
    value: T | None = None
    message: str | None = None

    def diagnostic(self):
        return {'state': self.state, 'message': self.message}


def read_artifact(path: Path, model: type[T]) -> ArtifactRead[T]:
    try:
        contents = path.read_bytes()
    except FileNotFoundError:
        return ArtifactRead('not_generated')
    except OSError:
        return ArtifactRead('unavailable', message=f'Não foi possível ler {path.name}. Verifique o acesso ao arquivo. Os dados foram preservados.')
    try:
        return ArtifactRead('available', model.model_validate_json(contents))
    except ValueError:
        return ArtifactRead('invalid', message=f'Arquivo {path.name} inválido ou corrompido. Os dados originais foram preservados; restaure uma cópia ou gere este artefato novamente.')
