from datetime import date, datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

import utils
from dataframe_utils import (
    count_events,
    make_state_summary,
    make_state_tables,
)


st.set_page_config(
    page_title="Ticketmaster Event Tracker",
    layout="wide",
)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_search_events(city, genre):
    """
    Cache search results for one hour to prevent repeated API calls
    during Streamlit reruns.
    """
    return utils.fetch_data(
        city=city,
        target_genre=genre,
        is_daily_fetch=False,
    )


def get_music_classification(event):
    """Return the event classification belonging to Music."""
    return next(
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


def display_events(events, start_date, end_date):
    """Display events that fall within the selected date range."""
    matching_events = []

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
        st.info("No events match your criteria.")
        return

    event_word = (
        "event" if len(matching_events) == 1 else "events"
    )

    st.success(
        f"Found {len(matching_events)} matching {event_word}."
    )

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

        with st.container(border=True):
            st.subheader(event_name)

            col1, col2 = st.columns(2)

            with col1:
                st.write(
                    f"**Date:** {event_date:%B %d, %Y}"
                )

                if local_time:
                    st.write(f"**Time:** {local_time}")

                st.write(f"**Genre:** {genre}")

                if subgenre and subgenre != genre:
                    st.write(f"**Subgenre:** {subgenre}")

            with col2:
                st.write(f"**Venue:** {venue_name}")

                if state_code:
                    st.write(f"**State:** {state_code}")

                if event_url:
                    st.link_button(
                        "View on Ticketmaster",
                        event_url,
                    )


def display_snapshot(today_file):
    """Load and display analytics for today's CSV snapshot."""
    event_counts = pd.read_csv(today_file)

    if event_counts.empty:
        st.info("Today's data file contains no events.")
        return

    # Each row in the CSV represents one event.
    event_counts["event_count"] = 1

    (
        state_genre_counts,
        state_counts,
        genre_counts,
    ) = make_state_tables(event_counts)

    state_summary = make_state_summary(
        state_genre_counts,
        state_counts,
    )

    # Add missing genre columns when a genre has no events.
    for genre in utils.GENRES:
        if genre not in state_summary.columns:
            state_summary[genre] = 0

    total_events = count_events(event_counts)

    top_state = "N/A"
    if not state_counts.empty:
        top_state_index = (
            state_counts["state_total"].idxmax()
        )
        top_state = state_counts.loc[
            top_state_index,
            "state_code",
        ]

    top_genre = "N/A"
    if not genre_counts.empty:
        top_genre_index = (
            genre_counts["genre_total"].idxmax()
        )
        top_genre = genre_counts.loc[
            top_genre_index,
            "genre",
        ]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total events", f"{total_events:,}")
    col2.metric("States", f"{len(state_counts):,}")
    col3.metric("Top state", top_state)
    col4.metric("Top genre", top_genre)

    figure = px.choropleth(
        state_summary,
        locations="state_code",
        color="state_total",
        locationmode="USA-states",
        scope="usa",
        hover_name="state_code",
        hover_data={
            "Pop": True,
            "Country": True,
            "R&B": True,
            "Hip-Hop/Rap": True,
            "Latin": True,
            "state_total": ":,",
            "state_share_us": ":.2f",
        },
        color_continuous_scale="Blues",
        title="Events by State",
    )

    st.plotly_chart(
        figure,
        width="stretch",
    )


search_tab, snapshot_tab = st.tabs(
    [
        "Search Events",
        "Daily Snapshot",
    ]
)


with search_tab:
    st.header("Ticketmaster Event Tracker")

    st.write(
        "Search for U.S. music events by city, genre, "
        "and date."
    )

    with st.form("event_search_form"):
        city_choice = st.text_input(
            "Which city would you like to search?"
        )

        genre_choice = st.selectbox(
            "Which genre would you like to search?",
            utils.GENRES,
        )

        col1, col2 = st.columns(2)

        with col1:
            start_date = st.date_input(
                "Start date",
                value=date.today(),
            )

        with col2:
            end_date = st.date_input(
                "End date",
                value=date.today(),
            )

        search_submitted = st.form_submit_button(
            "Search events",
            type="primary",
        )

    if search_submitted:
        city_choice = city_choice.strip()

        if not city_choice:
            st.warning("Please enter a city.")

        elif start_date > end_date:
            st.warning(
                "The start date must be before the end date."
            )

        else:
            try:
                with st.spinner(
                    "Searching Ticketmaster..."
                ):
                    events = fetch_search_events(
                        city_choice,
                        genre_choice,
                    )

                display_events(
                    events,
                    start_date,
                    end_date,
                )

            except requests.HTTPError as error:
                st.error(
                    f"Ticketmaster returned an error: {error}"
                )

            except RuntimeError as error:
                st.error(str(error))


with snapshot_tab:
    st.header("Daily U.S. Music Snapshot")

    st.write(
        "Pop, Latin, R&B, Hip-Hop/Rap, and Country events."
    )

    formatted_date = datetime.now().strftime("%Y-%m-%d")

    today_file = Path(
        f"data/ticketmaster_events_{formatted_date}.csv"
    )

    if today_file.exists():
        st.success("Today's data is available.")

        if st.button("Refresh today's snapshot"):
            try:
                with st.spinner(
                    "Refreshing Ticketmaster data..."
                ):
                    utils.fetch_data(
                        city=None,
                        target_genre=None,
                        is_daily_fetch=True,
                    )

                st.cache_data.clear()
                st.success("Snapshot refreshed.")
                st.rerun()

            except requests.HTTPError as error:
                st.error(
                    f"Ticketmaster returned an error: {error}"
                )

            except RuntimeError as error:
                st.error(str(error))

        display_snapshot(today_file)

    else:
        st.info(
            "Today's snapshot has not been downloaded yet."
        )

        if st.button(
            "Download today's snapshot",
            type="primary",
        ):
            try:
                with st.spinner(
                    "Downloading Ticketmaster data..."
                ):
                    utils.fetch_data(
                        city=None,
                        target_genre=None,
                        is_daily_fetch=True,
                    )

                if today_file.exists():
                    st.success(
                        "Today's snapshot was created."
                    )
                    st.rerun()
                else:
                    st.error(
                        "The download finished, but no CSV "
                        "was created."
                    )

            except requests.HTTPError as error:
                st.error(
                    f"Ticketmaster returned an error: {error}"
                )

            except RuntimeError as error:
                st.error(str(error))