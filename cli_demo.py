from datetime import date, datetime
from pathlib import Path
from utils import fetch_data
from streamlit_app import get_music_classification

if __name__ == "__main__":
    matching_events = []
    city = input("Enter a city: ")
    genre = input("Enter a genre: Pop, Latin, R&B, Hip-Hop/Rap, Country: ")
    start_date = date.fromisoformat(input("Enter a start date for the search (YYYY-MM-DD): "))
    end_date = date.fromisoformat(input("Enter an end date for the search (YYYY-MM-DD): "))

    events = fetch_data(
        city = city,
        target_genre = genre,
        is_daily_fetch = False
    )

    for event in events:
            local_date_string = (
                event.get("dates", {})
                .get("start", {})
                .get("localDate")
            )
    
            if not local_date_string:
                continue
    
            try:
                event_date = date.fromisoformat(local_date_string)
            except ValueError:
                continue
    
            if start_date <= event_date <= end_date:
                matching_events.append((event_date, event))
    
    matching_events.sort(key=lambda item: item[0])
    
    if not matching_events:
        print("No events match your criteria.")

    else:
    
        event_word = (
         "event" if len(matching_events) == 1 else "events"
        )
    
        print(
        f"Found {len(matching_events)} matching {event_word}."
        )
        print("See additional event details below")
        print("------------")
    
        for event_date, event in matching_events:
            venues = (
            event.get("_embedded", {}).get("venues", [])
            )
            venue = venues[0] if venues else {}
    
            classification = get_music_classification(event)
    
            genre = (
                classification.get("genre", {}).get(
                    "name",
                    "Unknown",
                )
            )
            subgenre = (
                classification.get("subGenre", {}).get(
                    "name",
                    "",
                )
            )
    
            event_name = event.get("name", "Unnamed event")
            event_url = event.get("url")
    
            local_time = (
                event.get("dates", {})
                .get("start", {})
                .get("localTime", "")
            )
    
            venue_name = venue.get("name", "Unknown venue")
            state_code = (
                venue.get("state", {}).get("stateCode", "")
            )

            print(event_name)
            print("Date: ", event_date)
            if local_time:
                print(f"**Time:** {local_time}")

                print(f"**Genre:** {genre}")

            if subgenre and subgenre != genre:
                print(f"**Subgenre:** {subgenre}")

          
            print(f"**Venue:** {venue_name}")

            if state_code:
                print(f"**State:** {state_code}")

            if event_url:
                print(
                    "View on Ticketmaster",
                    event_url,
                )

            print("------------")



# if __name__ == "__main__":
#     now = datetime.now()
#     formatted_date = now.strftime("%Y-%m-%d")
#     csv_file = Path(f"data/ticketmaster_events_{formatted_date}.csv")

#     if csv_file.is_file():
#         print("Today's data file already exists")
#     else:
#         print("No data file for today exists, retrieving data from Ticketmaster")
#         fetch_data(is_daily_fetch=True)
