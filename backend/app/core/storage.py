"""Small storage boundary for backend-managed evidence objects."""

import asyncio
import os
import shutil
from pathlib import Path, PurePosixPath
from typing import Protocol

from app.core.config import settings


class EvidenceStorage(Protocol):
    """Storage operations required by the evidence upload service."""

    async def store(self, source_path: Path, storage_key: str) -> None: ...

    async def delete(self, storage_key: str) -> None: ...

    async def read(self, storage_key: str, max_bytes: int) -> bytes: ...


class LocalEvidenceStorage:
    """Store evidence below one configured, non-executable local directory."""

    def __init__(self, root: str) -> None:
        self.root = Path(root).expanduser().resolve()

    async def store(self, source_path: Path, storage_key: str) -> None:
        destination = self._path_for(storage_key)
        await asyncio.to_thread(destination.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(shutil.copyfile, source_path, destination)
        await asyncio.to_thread(os.chmod, destination, 0o600)

    async def delete(self, storage_key: str) -> None:
        destination = self._path_for(storage_key)
        try:
            await asyncio.to_thread(destination.unlink)
        except FileNotFoundError:
            return

    async def read(self, storage_key: str, max_bytes: int) -> bytes:
        """Read a bounded object for internal processing only."""
        destination = self._path_for(storage_key)

        def read_bounded() -> bytes:
            with destination.open("rb") as file:
                content = file.read(max_bytes + 1)
            if len(content) > max_bytes:
                raise ValueError("Evidence object exceeds processing limit.")
            return content

        return await asyncio.to_thread(read_bounded)

    def _path_for(self, storage_key: str) -> Path:
        relative = PurePosixPath(storage_key)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Storage key must remain inside the evidence root.")
        destination = (self.root / Path(*relative.parts)).resolve()
        if destination != self.root and self.root not in destination.parents:
            raise ValueError("Storage key must remain inside the evidence root.")
        return destination


def get_evidence_storage() -> EvidenceStorage:
    """Build the configured evidence storage backend."""
    return LocalEvidenceStorage(settings.evidence_storage_root)
