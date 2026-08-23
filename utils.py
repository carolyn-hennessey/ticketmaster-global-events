import csv
import os

import requests
from dotenv import load_dotenv

load_dotenv()

TICKETMASTER_URL = (
    "https://app.ticketmaster.com/discovery/v2/events.json"
)
API_KEY = os.getenv("TICKETMASTER_API_KEY")

GENRES = [
    "Pop",
    "Latin",
    "R&B",
    "Hip-Hop/Rap",
    "Country",
]
PAGE_SIZE = 200
MAX_RESULTS_PER_QUERY = 1000


def fetch_data():
    """
    Fetch U.S. music events from the preceding three months.

    Each genre is queried separately to allow up to 1,000 results per genre.
    Events are deduplicated by Ticketmaster event ID.
    """
    if not API_KEY:
        raise RuntimeError(
            "TICKETMASTER_API_KEY was not found in the environment."
        )

    # Dictionary prevents duplicate events across genres
    unique_events = {}

    for genre in GENRES:
        print(f"\nFetching genre: {genre}")

        params = {
            "apikey": API_KEY,
            "segmentName": "Music",
            "classificationName": genre,
            "size": PAGE_SIZE
        }

        page_number = 0
        genre_event_count = 0
        total_elements = 0

        while True:
            params["page"] = page_number

            response = requests.get(
                TICKETMASTER_URL,
                params=params,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            events = data.get("_embedded", {}).get("events", [])
            page_info = data.get("page", {})

            total_pages = page_info.get("totalPages", 0)
            total_elements = page_info.get("totalElements", 0)

            for event in events:
                event_id = event.get("id")

                if event_id:
                    unique_events[event_id] = event

            genre_event_count += len(events)

            print(
                f"  Page {page_number + 1}/{total_pages}: "
                f"{len(events)} events"
            )

            page_number += 1

            reached_last_page = page_number >= total_pages
            reached_api_limit = (
                page_number * PAGE_SIZE >= MAX_RESULTS_PER_QUERY
            )

            if reached_last_page or reached_api_limit or not events:
                break

        print(
            f"  Retrieved {genre_event_count} records for {genre}."
        )

        if total_elements > MAX_RESULTS_PER_QUERY:
            print(
                f"  Warning: {genre} has {total_elements} matches, "
                f"but Ticketmaster exposes only "
                f"{MAX_RESULTS_PER_QUERY} per query."
            )

    events = list(unique_events.values())

    print(
        f"\nRetrieved {len(events)} unique events across "
        f"{len(GENRES)} genres."
    )

    write_ticketmaster_json_csv(events)

def write_ticketmaster_json_csv(events):
    """Flatten Ticketmaster event records and save them as CSV."""
    rows = []

    for event in events:
        music_classification = next(
            (
                classification
                for classification in event.get("classifications", [])
                if (
                    classification
                    .get("segment", {})
                    .get("name", "")
                    .casefold()
                    == "music"
                )
            ),
            {},
        )

        venues = event.get("_embedded", {}).get("venues", [])
        venue = venues[0] if venues else {}

        attractions = (
            event.get("_embedded", {}).get("attractions", [])
        )
        artist_names = "; ".join(
            attraction.get("name", "")
            for attraction in attractions
            if attraction.get("name")
        )

        price_ranges = event.get("priceRanges", [])
        price = price_ranges[0] if price_ranges else {}

        images = [
            image
            for image in event.get("images", [])
            if image.get("ratio") == "16_9"
        ]
        image = max(
            images,
            key=lambda item: item.get("width", 0),
            default={},
        )

        event_dates = event.get("dates", {})
        start = event_dates.get("start", {})
        status = event_dates.get("status", {})

        state = venue.get("state", {})
        country = venue.get("country", {})
        location = venue.get("location", {})

        row = {
            "event_id": event.get("id", ""),
            "event_name": event.get("name", ""),
            "event_url": event.get("url", ""),
            "local_date": start.get("localDate", ""),
            "local_time": start.get("localTime", ""),
            "utc_datetime": start.get("dateTime", ""),
            "timezone": event_dates.get("timezone", ""),
            "status": status.get("code", ""),
            "segment": (
                music_classification
                .get("segment", {})
                .get("name", "")
            ),
            "genre": (
                music_classification
                .get("genre", {})
                .get("name", "")
            ),
            "subgenre": (
                music_classification
                .get("subGenre", {})
                .get("name", "")
            ),
            "artists": artist_names,
            "venue_name": venue.get("name", ""),
            "venue_id": venue.get("id", ""),
            "address": (
                venue.get("address", {}).get("line1", "")
            ),
            "city": venue.get("city", {}).get("name", ""),
            "state": state.get("name", ""),
            "state_code": state.get("stateCode", ""),
            "postal_code": venue.get("postalCode", ""),
            "country_code": country.get("countryCode", ""),
            "latitude": location.get("latitude", ""),
            "longitude": location.get("longitude", ""),
            "min_price": price.get("min", ""),
            "max_price": price.get("max", ""),
            "currency": price.get("currency", ""),
            "image_url": image.get("url", ""),
        }

        rows.append(row)

    output_path = "data/ticketmaster_events.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if not rows:
        print("The API response contained no events.")
        return

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=rows[0].keys(),
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} events to {output_path}")