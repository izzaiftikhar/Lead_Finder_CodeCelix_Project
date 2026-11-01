from typing import Any

from apify_client import ApifyClient

from app.config import settings
from app.base_provider import BaseDiscoveryProvider


class ApifyGoogleMapsProvider(BaseDiscoveryProvider):

    def __init__(self):

        if not settings.APIFY_API_TOKEN:
            raise ValueError(
                "APIFY_API_TOKEN is missing. "
                "Add it to your .env file."
            )

        self.client = ApifyClient(
            settings.APIFY_API_TOKEN
        )

        self.actor_id = settings.APIFY_ACTOR_ID

    def search(
        self,
        query: str,
        location: str,
        limit: int
    ) -> list[dict[str, Any]]:

        limit = min(
            max(1, limit),
            settings.MAX_RAW_CANDIDATES
        )

        actor_input = {

            "searchStringsArray": [
                query
            ],

            "locationQuery": location,

            "maxCrawledPlacesPerSearch": limit,

            "language": "en",

            "includeWebResults": False,

            "scrapePlaceDetailPage": False,

            "maxReviews": 0,

            "maxImages": 0,

            "scrapeContacts": False,

            "scrapeDirectories": False,

            "scrapeSocialMediaProfiles": {
                "facebooks": False,
                "instagrams": False,
                "linkedIns": False,
                "tiktoks": False,
                "twitters": False,
                "youtubes": False
            }
        }

        # Run Apify actor
        run = self.client.actor(
            self.actor_id
        ).call(
            run_input=actor_input
        )

        if not run:
            raise RuntimeError(
                "Apify actor execution failed."
            )

        dataset_id = run.default_dataset_id

        if not dataset_id:
            raise RuntimeError(
                "Apify did not return a dataset ID."
            )

        # Retrieve results
        results = list(
            self.client.dataset(
                dataset_id
            ).iterate_items()
        )

        return results[:limit]