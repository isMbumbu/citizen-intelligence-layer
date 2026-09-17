"""Bounded, deterministic processing boundary for citizen evidence."""

import hashlib

from app.core.storage import EvidenceStorage
from app.models.evidence import EvidenceRecord

_MAX_PROCESSING_BYTES = 10 * 1024 * 1024


class EvidenceProcessor:
    """Read bounded untrusted bytes and produce non-authoritative metadata."""

    def __init__(self, storage: EvidenceStorage) -> None:
        self.storage = storage

    async def process(self, evidence: EvidenceRecord) -> str:
        """Return a digest of the original object without interpreting its contents."""
        content = await self.storage.read(evidence.storage_key, _MAX_PROCESSING_BYTES)
        return hashlib.sha256(content).hexdigest()
