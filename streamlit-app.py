import requests
import os
import streamlit as st
import utils
import pandas as pd
from streamlit_folium import st_folium as sf
from dotenv import load_dotenv
from datetime import datetime


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
st.header("Welcome to your very own Event Tracker! This is the go to search page for music lovers in any city. Start your search and find events near you!")
city_choice = st.text_input("Which city would you like to get the event information for? ")
genre_choice = st.selectbox("Which genre would you like to search for?", ["Pop", "Latin", "R&B", "Hip-Hop/Rap", "Country"])
start_date = str(st.date_input("What is a start date we are looking for? "))
end_date = str(st.date_input("What is your end date?"))

#If user inputs a city, get_event function is called
if city_choice:
    get_event(city_choice, genre_choice, start_date, end_date)
