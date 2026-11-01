import os

from dotenv import load_dotenv

load_dotenv()


class Settings:

    APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

    APIFY_ACTOR_ID = os.getenv(
        "APIFY_ACTOR_ID",
        "compass/crawler-google-places"
    )

    CACHE_TTL_HOURS = int(
        os.getenv("CACHE_TTL_HOURS", "24")
    )

    MAX_RAW_CANDIDATES = 100


settings = Settings()