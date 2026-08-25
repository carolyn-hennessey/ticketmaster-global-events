import csv
import os
import time
from datetime import datetime, timezone

import requests
import streamlit as st
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv


load_dotenv()

TICKETMASTER_URL = (
    "https://app.ticketmaster.com/discovery/v2/events.json"
)

GENRES = [
    "Pop",
    "Latin",
    "R&B",
    "Hip-Hop/Rap",
    "Country",
]

PAGE_SIZE = 200
MAX_RESULTS_PER_QUERY = 1000
REQUEST_INTERVAL_SECONDS = 0.25
MAX_RETRIES = 6


def get_api_key():
    """Load the API key from the environment or Streamlit secrets."""
    api_key = os.getenv("TICKETMASTER_API_KEY")

    if api_key:
        return api_key

    try:
        return st.secrets.get("TICKETMASTER_API_KEY")
    except (FileNotFoundError, KeyError):
        return None


def ticketmaster_get(session, params):
    """Make a Ticketmaster request with rate limiting and retries."""
    for attempt in range(MAX_RETRIES):
        time.sleep(REQUEST_INTERVAL_SECONDS)

        response = session.get(
            TICKETMASTER_URL,
            params=params,
            timeout=30,
        )

        if response.status_code != 429:
            response.raise_for_status()
            return response

        retry_after = response.headers.get("Retry-After")

        if retry_after:
            try:
                delay = float(retry_after)
            except ValueError:
                delay = 2 ** attempt
        else:
            delay = 2 ** attempt

        delay = min(delay, 60)

        print(
            f"Rate limit reached. Retrying in {delay:.1f} seconds "
            f"(attempt {attempt + 1}/{MAX_RETRIES})."
        )

        time.sleep(delay)

    raise RuntimeError(
        "Ticketmaster continued returning HTTP 429. "
        "The daily API quota may be exhausted."
    )


def fetch_data(
    city=None,
    target_genre=None,
    is_daily_fetch=False,
):
    """
    Fetch U.S. music events from the preceding three months.

    Genres are queried separately, and events are deduplicated by ID.
    """
    api_key = get_api_key()

    if not api_key:
        raise RuntimeError(
            "TICKETMASTER_API_KEY was not found."
        )

    end_datetime = datetime.now(timezone.utc)
    start_datetime = end_datetime - relativedelta(months=3)

    genres = [target_genre] if target_genre else GENRES
    unique_events = {}

    with requests.Session() as session:
        for genre in genres:
            print(f"\nFetching genre: {genre}")

            params = {
                "apikey": api_key,
                "countryCode": "US",
                "segmentName": "Music",
                "classificationName": genre,
                "startDateTime": start_datetime.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "endDateTime": end_datetime.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "size": PAGE_SIZE,
                "sort": "date,asc",
            }

            if city:
                params["city"] = city

            page_number = 0
            genre_event_count = 0
            total_elements = 0

            while True:
                params["page"] = page_number

                response = ticketmaster_get(session, params)
                data = response.json()

                events = (
                    data.get("_embedded", {}).get("events", [])
                )
                page_info = data.get("page", {})

                total_pages = page_info.get("totalPages", 0)
                total_elements = page_info.get(
                    "totalElements",
                    0,
                )

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
                    page_number * PAGE_SIZE
                    >= MAX_RESULTS_PER_QUERY
                )

                if (
                    reached_last_page
                    or reached_api_limit
                    or not events
                ):
                    break

            print(
                f"  Retrieved {genre_event_count} records "
                f"for {genre}."
            )

            if total_elements > MAX_RESULTS_PER_QUERY:
                print(
                    f"  Warning: {genre} has {total_elements} "
                    f"matches, but Ticketmaster exposes only "
                    f"{MAX_RESULTS_PER_QUERY} per query."
                )

    events = list(unique_events.values())

    print(f"\nRetrieved {len(events)} unique events.")

    if is_daily_fetch:
        write_ticketmaster_json_csv(events)

    return events


def write_ticketmaster_json_csv(events):
    """Flatten Ticketmaster events and save them as CSV."""
    rows = []

    for event in events:
        music_classification = next(
            (
                classification
                for classification in event.get(
                    "classifications",
                    [],
                )
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

        dates = event.get("dates", {})
        start = dates.get("start", {})
        status = dates.get("status", {})

        segment = music_classification.get("segment", {})
        genre = music_classification.get("genre", {})
        subgenre = music_classification.get("subGenre", {})

        address = venue.get("address", {})
        city = venue.get("city", {})
        state = venue.get("state", {})
        country = venue.get("country", {})
        location = venue.get("location", {})

        rows.append(
            {
                "event_id": event.get("id", ""),
                "event_name": event.get("name", ""),
                "event_url": event.get("url", ""),
                "local_date": start.get("localDate", ""),
                "local_time": start.get("localTime", ""),
                "utc_datetime": start.get("dateTime", ""),
                "timezone": dates.get("timezone", ""),
                "status": status.get("code", ""),
                "segment": segment.get("name", ""),
                "genre": genre.get("name", ""),
                "subgenre": subgenre.get("name", ""),
                "artists": artist_names,
                "venue_name": venue.get("name", ""),
                "venue_id": venue.get("id", ""),
                "address": address.get("line1", ""),
                "city": city.get("name", ""),
                "state": state.get("name", ""),
                "state_code": state.get("stateCode", ""),
                "postal_code": venue.get("postalCode", ""),
                "country_code": country.get(
                    "countryCode",
                    "",
                ),
                "latitude": location.get("latitude", ""),
                "longitude": location.get("longitude", ""),
                "min_price": price.get("min", ""),
                "max_price": price.get("max", ""),
                "currency": price.get("currency", ""),
                "image_url": image.get("url", ""),
            }
        )

    if not rows:
        print("The API response contained no events.")
        return None

    date_string = datetime.now().strftime("%Y-%m-%d")
    output_path = (
        f"data/ticketmaster_events_{date_string}.csv"
    )

    os.makedirs("data", exist_ok=True)

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

    return output_path