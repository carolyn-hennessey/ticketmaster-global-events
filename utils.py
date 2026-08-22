import requests
import os
import csv
from dotenv import load_dotenv
from dateutil.relativedelta import relativedelta
from datetime import datetime



load_dotenv()

TICKETMASTER_BASE_URL = 'https://app.ticketmaster.com'
API_KEY = os.getenv("TICKETMASTER_API_KEY")

def fetch_data():
    """
    Fetches Ticketmaster dataset for a specified genre and stores the response in a .json file
    """

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    three_months_ago = datetime.now() - relativedelta(months=3)
    three_months_ago = three_months_ago.strftime("%Y-%m-%dT%H:%M:%SZ")

    query_string = TICKETMASTER_BASE_URL + f"/discovery/v2/events.json?classificationName=music&classificationName=Pop,Latin,R%26B,Hip-Hop%2FRap,Country&startDateTime={three_months_ago}&endDateTime={now}&size=200"

    response = requests.get(query_string + "&apikey=" + API_KEY )

    data = response.json()

    write_ticketmaster_json_csv(data)


def write_ticketmaster_json_csv(json_data):

    events = json_data.get("_embedded", {}).get("events", [])

    rows = []

    for event in events:
        # Select the classification belonging to the Music segment
        music_classification = next(
            (
                item
                for item in event.get("classifications", [])
                if item.get("segment", {}).get("name") == "Music"
            ),
            {},
        )

        # An event normally has one venue
        venues = event.get("_embedded", {}).get("venues", [])
        venue = venues[0] if venues else {}

        # Combine multiple artists/attractions into one CSV cell
        attractions = event.get("_embedded", {}).get("attractions", [])
        artist_names = "; ".join(
            attraction.get("name", "")
            for attraction in attractions
            if attraction.get("name")
        )

        # Use the first price range when one exists
        price_ranges = event.get("priceRanges", [])
        price = price_ranges[0] if price_ranges else {}

        # Find the largest 16:9 image
        images = [
            image
            for image in event.get("images", [])
            if image.get("ratio") == "16_9"
        ]
        image = max(images, key=lambda x: x.get("width", 0), default={})

        row = {
            "event_id": event.get("id", ""),
            "event_name": event.get("name", ""),
            "event_url": event.get("url", ""),
            "local_date": event.get("dates", {}).get("start", {}).get(
                "localDate", ""
            ),
            "local_time": event.get("dates", {}).get("start", {}).get(
                "localTime", ""
            ),
            "utc_datetime": event.get("dates", {}).get("start", {}).get(
                "dateTime", ""
            ),
            "timezone": event.get("dates", {}).get("timezone", ""),
            "status": event.get("dates", {}).get("status", {}).get("code", ""),
            "segment": music_classification.get("segment", {}).get("name", ""),
            "genre": music_classification.get("genre", {}).get("name", ""),
            "subgenre": music_classification.get("subGenre", {}).get("name", ""),
            "artists": artist_names,
            "venue_name": venue.get("name", ""),
            "venue_id": venue.get("id", ""),
            "address": venue.get("address", {}).get("line1", ""),
            "city": venue.get("city", {}).get("name", ""),
            "state": venue.get("state", {}).get("name", ""),
            "state_code": venue.get("state", {}).get("stateCode", ""),
            "postal_code": venue.get("postalCode", ""),
            "country_code": venue.get("country", {}).get("countryCode", ""),
            "latitude": venue.get("location", {}).get("latitude", ""),
            "longitude": venue.get("location", {}).get("longitude", ""),
            "min_price": price.get("min", ""),
            "max_price": price.get("max", ""),
            "currency": price.get("currency", ""),
            "image_url": image.get("url", ""),
        }

        rows.append(row)

    if rows:
        with open("data/ticketmaster_events.csv", "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        print(f"Saved {len(rows)} events to ticketmaster_events.csv")
    else:
        print("The API response contained no events.")
