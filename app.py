from datetime import datetime
from pathlib import Path
from utils import fetch_data

if __name__ == "__main__":
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d")
    csv_file = Path(f"data/ticketmaster_events_{formatted_date}.csv")

    if csv_file.is_file():
        print("Today's data file already exists")
    else:
        print("No data file for today exists, retrieving data from Ticketmaster")
        fetch_data()




