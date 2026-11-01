import json

from app.apify_provider import ApifyGoogleMapsProvider
from app.discovery_service import DiscoveryService


def run_discovery(
    niches: list[str],
    locations: list[str],
    max_raw_candidates: int = 100
) -> dict:

    # Initialize provider
    provider = ApifyGoogleMapsProvider()

    # Initialize discovery service
    discovery_service = DiscoveryService(
        provider=provider
    )

    # Execute discovery
    result = discovery_service.discover(
        niches=niches,
        locations=locations,
        max_raw_candidates=max_raw_candidates
    )

    return result


# --------------------------------
# TEST EXECUTION
# --------------------------------

if __name__ == "__main__":

    niches = [
        "real estate agency",
        "dental clinic"
    ]

    locations = [
        "Dubai, UAE",
        "Abu Dhabi, UAE",
    ]

    result = run_discovery(
        niches=niches,
        locations=locations,
        max_raw_candidates=100
    )

    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False,
            default=str
        )
    )

    # Save JSON response for testing
    with open(
        "discovery_results.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            indent=4,
            ensure_ascii=False,
            default=str
        )

    print("\nResults saved successfully!")