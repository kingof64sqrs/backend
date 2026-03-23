from __future__ import annotations

import logging
from dataclasses import dataclass

from qdrant_client.http import models as qm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.qdrant_client import get_qdrant
from app.core.redis_client import get_redis
from app.core.security import hash_password
from app.modules.places.model import Place
from app.modules.posts.model import Post
from app.modules.users.model import User

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SeedPlace:
    name: str
    category: str
    lat: float
    lon: float


BANGALORE_PLACES: list[SeedPlace] = [
    SeedPlace("Cubbon Park", "parks", 12.9763, 77.5929),
    SeedPlace("Lalbagh Botanical Garden", "parks", 12.9507, 77.5848),
    SeedPlace("MG Road", "nightlife", 12.9758, 77.6066),
    SeedPlace("Church Street", "cafes", 12.9753, 77.6055),
    SeedPlace("Indiranagar 100ft Road", "nightlife", 12.9718, 77.6412),
    SeedPlace("Koramangala 5th Block", "food", 12.9336, 77.6153),
    SeedPlace("Bannerghatta Road", "events", 12.8930, 77.5970),
    SeedPlace("UB City", "hidden_gems", 12.9716, 77.5946),
    SeedPlace("Vidhana Soudha", "hidden_gems", 12.9797, 77.5907),
    SeedPlace("Bangalore Palace", "events", 12.9987, 77.5920),
]

QDRANT_PLACES_COLLECTION = "places"
QDRANT_USERS_COLLECTION = "users"
QDRANT_VECTOR_SIZE = 384


def _vector_from_text(text: str, size: int = QDRANT_VECTOR_SIZE) -> list[float]:
    # Deterministic pseudo-embedding so Qdrant is usable without an ML model.
    h = abs(hash(text))
    out: list[float] = []
    for i in range(size):
        h = (h * 1103515245 + 12345 + i) & 0x7FFFFFFF
        out.append(((h % 20000) / 10000.0) - 1.0)  # [-1, 1]
    return out


def _ensure_qdrant_collections() -> None:
    client = get_qdrant()
    existing = {c.name for c in client.get_collections().collections}

    if QDRANT_PLACES_COLLECTION not in existing:
        client.create_collection(
            collection_name=QDRANT_PLACES_COLLECTION,
            vectors_config=qm.VectorParams(size=QDRANT_VECTOR_SIZE, distance=qm.Distance.COSINE),
        )

    if QDRANT_USERS_COLLECTION not in existing:
        client.create_collection(
            collection_name=QDRANT_USERS_COLLECTION,
            vectors_config=qm.VectorParams(size=QDRANT_VECTOR_SIZE, distance=qm.Distance.COSINE),
        )


async def seed_if_empty(db: AsyncSession) -> None:
    # Seed only if there are no places.
    places_count = (await db.execute(select(Place.id).limit(1))).scalar_one_or_none()
    if places_count is not None:
        return

    logger.info("Seeding dev data (Bangalore places + demo user + posts)")

    # Create demo user (for seeded posts)
    demo_phone = "9999999999"
    demo = User(
        email=f"{demo_phone}@aroundyou.local",
        phone=demo_phone,
        name="Demo User",
        hashed_password=hash_password(demo_phone),
    )
    db.add(demo)
    await db.flush()

    created_places: list[Place] = []
    for p in BANGALORE_PLACES:
        place = Place(
            name=p.name,
            category=p.category,
            lat=p.lat,
            lon=p.lon,
            location=f"SRID=4326;POINT({p.lon} {p.lat})",
            metadata_json=None,
        )
        db.add(place)
        created_places.append(place)

    await db.flush()

    created_posts: list[Post] = []
    for i, place in enumerate(created_places):
        post = Post(
            user_id=demo.id,
            place_id=place.id,
            caption=f"Discover #{i+1}: {place.name}",
            media_url=None,
        )
        db.add(post)
        created_posts.append(post)

    await db.commit()

    # Redis trending seed (optional)
    try:
        redis = get_redis()
        for idx, post in enumerate(created_posts[:6]):
            await redis.zincrby("trending:posts", 10 - idx, post.id)
    except Exception as exc:  # pragma: no cover
        logger.debug("Redis seed skipped: %s", exc)

    # Qdrant seed
    try:
        _ensure_qdrant_collections()
        qdrant = get_qdrant()

        qdrant.upsert(
            collection_name=QDRANT_PLACES_COLLECTION,
            points=[
                qm.PointStruct(
                    id=place.id,
                    vector=_vector_from_text(f"{place.name} {place.category}"),
                    payload={"place_id": place.id, "name": place.name, "category": place.category},
                )
                for place in created_places
            ],
        )

        qdrant.upsert(
            collection_name=QDRANT_USERS_COLLECTION,
            points=[
                qm.PointStruct(
                    id=demo.id,
                    vector=_vector_from_text(f"user {demo.phone}"),
                    payload={"user_id": demo.id, "phone": demo.phone},
                )
            ],
        )
    except Exception as exc:  # pragma: no cover
        logger.debug("Qdrant seed skipped: %s", exc)
