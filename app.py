from pathlib import Path
from utils import fetch_data

CSV_FILE = Path("data/ticketmaster_events.csv")

if __name__ == "__main__":
    if CSV_FILE.is_file():
        print("Data file already exists")
    else:
        print("No data file exists, retrieving data from Ticketmaster")
        fetch_data()




