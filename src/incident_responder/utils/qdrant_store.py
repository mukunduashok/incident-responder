"""
Qdrant integration for storing report embeddings by alert_type.
"""

import os
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "incident_reports")

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def store_report_embedding(
    investigation_id: str,
    alert_type: str,
    service_name: str,
    report_path: str,
    embedding: list[float],
    timestamp: str,
    extra_metadata: dict[str, Any] | None = None,
):
    """
    Store a report embedding in Qdrant, keyed by alert_type and investigation_id.
    """
    metadata = {
        "investigation_id": investigation_id,
        "alert_type": alert_type,
        "service_name": service_name,
        "report_path": report_path,
        "timestamp": timestamp,
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    # Ensure collection exists
    if QDRANT_COLLECTION not in [c.name for c in client.get_collections().collections]:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=len(embedding), distance=Distance.COSINE),
        )

    point = PointStruct(
        id=investigation_id,
        vector=embedding,
        payload=metadata,
    )
    client.upsert(collection_name=QDRANT_COLLECTION, points=[point])
