import requests
import os
import streamlit as st
import utils
import pandas as pd
import plotly.express as px
from streamlit_folium import st_folium as sf
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
from dataframe_utils import (
    count_events,
    event_counts,
    make_state_summary,
    make_state_tables,
)


# Load your API key from .env file
load_dotenv()
API_KEY = os.getenv("TICKETMASTER_API_KEY")

def get_event(city, genre, start_date, end_date):
    """
    Fetch event information for the given city and print it nicely.
    """
    #Referencing fetch data function in utils.py to pull API data
    events = utils.fetch_data(city, genre)

    
    match_found = False
    #all events go through for loop to return relevant event information for each
    for event in events:
        event_date = event["dates"]["start"]["localDate"]
        event_id = event["id"]

        #if event date falls within range selected by user, results will be returned
        if event_date >= start_date and event_date <= end_date:
            venue = event["_embedded"]["venues"][0]["name"]
            genre = event["classifications"][0]["segment"]["name"]
            st.write("Date: ", event_date)
            st.write("Genre: ", genre)
            st.write("Venue: ", venue)
            st.write("---")
            match_found = True

    #if no results match criteria, user will be informed
    if match_found == False:
        st.write("No events match your critera.")
   

#Streamlit webpage layout
# Separate the event search from the daily analytics snapshot.
search_tab, snapshot_tab = st.tabs(["Search Events", "Daily Snapshot"])

with search_tab:
    st.header("Welcome to your very own Event Tracker! This is the go to search page for music lovers in any city. Start your search and find events near you!")
    city_choice = st.text_input("Which city would you like to get the event information for? ")
    genre_choice = st.selectbox("Which genre would you like to search for?", ["Pop", "Latin", "R&B", "Hip-Hop/Rap", "Country"])
    start_date = str(st.date_input("What is a start date we are looking for? "))
    end_date = str(st.date_input("What is your end date?"))

    #If user inputs a city, get_event function is called
    if city_choice:
        get_event(city_choice, genre_choice, start_date, end_date)

with snapshot_tab:
    st.header("Daily snapshot of interesting ticketmaster concerts across U.S. including Pop, Latin, R&B, Hip-Hop/Rap & Country")
    today_file = Path(f"data/ticketmaster_events_{datetime.now():%Y-%m-%d}.csv")
    if today_file.exists():
        st.success("Today's data is available.")

        # Build summary tables with Canyang's dataframe helpers.
        state_genre_counts, state_counts, genre_counts = make_state_tables(
            event_counts
        )
        state_summary = make_state_summary(state_genre_counts, state_counts)
        total_events = count_events(event_counts)
        top_state = state_counts.loc[
            state_counts["state_total"].idxmax(), "state_code"
        ]
        top_genre = genre_counts.loc[
            genre_counts["genre_total"].idxmax(), "genre"
        ]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total events", f"{total_events:,}")
        col2.metric("States", f"{len(state_counts):,}")
        col3.metric("Top state", top_state)
        col4.metric("Top genre", top_genre)

        # Show total event counts by state on an interactive U.S. map.
        fig = px.choropleth(
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
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Today's data is not available yet.")
