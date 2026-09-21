import httpx
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.core.config import settings
import uuid
import asyncio
import json

logger = logging.getLogger(__name__)


class VectorStore:
    """Векторное хранилище для semantic search и дедупликации"""

    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            timeout=5.0,
            check_compatibility=False,
        )
        self.collection_name = settings.QDRANT_COLLECTION
        self._initialized = False
        self._available = True

    async def _get_embedding(self, text: str) -> list:
        """Get embedding from Ollama"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.OLLAMA_URL}/api/embeddings",
                    json={"model": settings.OLLAMA_MODEL, "prompt": text}
                )
                response.raise_for_status()
                data = response.json()
                return data.get("embedding", [0.0] * 768)
        except Exception as e:
            logger.error("Embedding error: %s", e)
            return [0.0] * 768

    async def initialize(self):
        """Initialize collection if not exists"""
        if self._initialized:
            return

        try:
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                )

            self._initialized = True
        except Exception as e:
            logger.warning("Vector store initialization error (non-critical): %s", e)
            self._available = False

    async def add_project(self, project_id: str, name: str, description: str,
                         category: str, metadata: dict = None) -> str:
        """Add project to vector store (graceful fallback if unavailable)"""
        if not self._available:
            return ""

        await self.initialize()

        try:
            text = f"{name} {description} {category}"
            embedding = await self._get_embedding(text)

            point_id = str(uuid.uuid4())

            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            'project_id': project_id,
                            'name': name,
                            'description': description,
                            'category': category,
                            **(metadata or {})
                        }
                    )
                ]
            )

            return point_id
        except Exception as e:
            logger.warning("Vector store add error (non-critical): %s", e)
            self._available = False
            return ""

    async def search_similar(self, text: str, threshold: float = 0.85, limit: int = 5) -> list:
        """Search for similar projects"""
        await self.initialize()

        try:
            embedding = await self._get_embedding(text)

            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=limit,
                score_threshold=threshold
            )

            return [
                {
                    'id': r.payload.get('project_id'),
                    'score': r.score,
                    'name': r.payload.get('name'),
                    'category': r.payload.get('category')
                }
                for r in results
            ]
        except Exception as e:
            logger.error("Vector search error: %s", e)
            return []

    async def find_duplicates(self, name: str, description: str,
                             threshold: float = 0.90) -> list:
        """Find potential duplicates (returns empty list if unavailable)"""
        if not self._available:
            return []
        text = f"{name} {description}"
        return await self.search_similar(text, threshold=threshold, limit=3)

    async def delete_project(self, project_id: str):
        """Delete project from vector store"""
        await self.initialize()

        try:
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter={
                    'must': [
                        {'key': 'project_id', 'match': {'value': project_id}}
                    ]
                },
                limit=100
            )

            point_ids = [r.id for r in results[0]]
            if point_ids:
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=point_ids
                )
        except Exception as e:
            logger.error("Vector delete error: %s", e)

    async def get_collection_stats(self) -> dict:
        """Get collection statistics"""
        await self.initialize()

        try:
            info = self.client.get_collection(self.collection_name)
            return {
                'vectors_count': info.vectors_count,
                'indexed_vectors_count': info.indexed_vectors_count,
                'status': info.status
            }
        except Exception as e:
            return {'error': str(e)}


vector_store = VectorStore()
