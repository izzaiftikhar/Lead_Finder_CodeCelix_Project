import hashlib
import time
from typing import Any

from app.base_provider import BaseDiscoveryProvider
from app.config import settings


class DiscoveryService:

    def __init__(
        self,
        provider: BaseDiscoveryProvider
    ):

        self.provider = provider

        # Temporary in-memory query cache
        self.cache = {}

    # --------------------------------
    # GENERATE CACHE KEY
    # --------------------------------

    def generate_cache_key(
        self,
        query: str,
        location: str
    ) -> str:

        raw_key = (
            f"{query.lower().strip()}|"
            f"{location.lower().strip()}"
        )

        return hashlib.sha256(
            raw_key.encode()
        ).hexdigest()

    # --------------------------------
    # GET CACHED RESULTS
    # --------------------------------

    def get_cached_results(
        self,
        cache_key: str,
        required_limit: int
    ):

        cached = self.cache.get(cache_key)

        if not cached:
            return None

        age = time.time() - cached["created_at"]

        ttl_seconds = (
            settings.CACHE_TTL_HOURS * 60 * 60
        )

        if age > ttl_seconds:
            self.cache.pop(cache_key, None)
            return None

        # Reuse only if this cache entry was fetched
        # with at least the requested candidate limit.
        if cached["requested_limit"] < required_limit:
            return None

        return cached["results"]

    # --------------------------------
    # SAVE RESULTS IN CACHE
    # --------------------------------

    def save_cached_results(
        self,
        cache_key: str,
        results: list[dict[str, Any]],
        requested_limit: int
    ):

        self.cache[cache_key] = {

            "results": results,

            "created_at": time.time(),

            "requested_limit": requested_limit
        }

    # --------------------------------
    # NORMALIZE BUSINESS DATA
    # --------------------------------

    def normalize_business(
        self,
        raw: dict[str, Any]
    ) -> dict[str, Any] | None:

        place_id = raw.get("placeId")

        # placeId is necessary for reliable
        # provider-based deduplication.
        if not place_id:
            return None

        location = raw.get("location") or {}

        coordinates = None

        if (
            location.get("lat") is not None
            and location.get("lng") is not None
        ):
            coordinates = {
                "latitude": location["lat"],
                "longitude": location["lng"]
            }

        return {

            "provider_name": "apify_google_maps",

            "provider_place_id": str(place_id),

            "name": raw.get("title"),

            "category": raw.get("categoryName"),

            "address": raw.get("address"),

            "city": raw.get("city"),

            "state": raw.get("state"),

            "country_code": raw.get("countryCode"),

            "website": raw.get("website"),

            "phone": raw.get("phone"),

            "location": coordinates,

            "rating": raw.get("totalScore"),

            "reviews_count": raw.get("reviewsCount"),


            "google_maps_url": raw.get("url"),

            "image_url": raw.get("imageUrl"),

            "scraped_at": (
                str(raw["scrapedAt"])
                if raw.get("scrapedAt") is not None
                else None
            ),

            "search_query": raw.get("searchString")
        }

    # --------------------------------
    # DISCOVER BUSINESSES
    # --------------------------------

    def discover(
        self,
        niches: list[str],
        locations: list[str],
        max_raw_candidates: int = 100
    ) -> dict[str, Any]:

        if not niches or not locations:
            raise ValueError(
                "At least one niche and location are required."
            )

        if not 1 <= max_raw_candidates <= settings.MAX_RAW_CANDIDATES:
            raise ValueError(
                "max_raw_candidates must be between 1 and 100."
            )

        # Remove empty values and repeated inputs
        niches = list(dict.fromkeys(
            item.strip()
            for item in niches
            if item and item.strip()
        ))

        locations = list(dict.fromkeys(
            item.strip()
            for item in locations
            if item and item.strip()
        ))

        if not niches or not locations:
            raise ValueError(
                "Provide valid niches and locations."
            )

        search_pairs = [
            (niche, location)
            for location in locations
            for niche in niches
        ]

        businesses = {}

        search_details = []

        raw_candidate_count = 0

        duplicates_removed = 0

        missing_place_id = 0

        # --------------------------------
        # SEARCH LOOP
        # --------------------------------

        for index, (niche, location) in enumerate(search_pairs):

            remaining = (
                max_raw_candidates - raw_candidate_count
            )

            if remaining <= 0:
                break

            searches_left = len(search_pairs) - index

            # Distribute the remaining candidate
            # budget across remaining searches.
            search_limit = (
                remaining + searches_left - 1
            ) // searches_left

            cache_key = self.generate_cache_key(
                niche,
                location
            )

            cached_results = self.get_cached_results(
                cache_key,
                search_limit
            )

            cache_hit = cached_results is not None

            if cache_hit:

                raw_results = cached_results

            else:

                raw_results = self.provider.search(
                    query=niche,
                    location=location,
                    limit=search_limit
                )

                raw_results = raw_results[:search_limit]

                self.save_cached_results(
                    cache_key,
                    raw_results,
                    search_limit
                )

            # Count raw candidates before deduplication.
            raw_candidate_count += len(raw_results)

            # --------------------------------
            # NORMALIZE AND DEDUPLICATE
            # --------------------------------

            for raw in raw_results:

                business = self.normalize_business(raw)

                if business is None:
                    missing_place_id += 1
                    continue

                unique_key = (
                    business["provider_name"],
                    business["provider_place_id"]
                )

                if unique_key in businesses:

                    duplicates_removed += 1
                    continue

                businesses[unique_key] = business

            search_details.append({

                "niche": niche,

                "location": location,

                "raw_candidates": len(raw_results),

                "cache_hit": cache_hit
            })

        # --------------------------------
        # FINAL JSON RESPONSE
        # --------------------------------

        unique_businesses = list(
            businesses.values()
        )

        return {

            "success": True,

            "provider": "apify_google_maps",

            "summary": {

                "raw_candidates": raw_candidate_count,

                "unique_businesses": len(unique_businesses),

                "duplicates_removed": duplicates_removed,

                "missing_place_id": missing_place_id,

                "max_raw_candidates": max_raw_candidates
            },

            "searches": search_details,

            "businesses": unique_businesses
        }