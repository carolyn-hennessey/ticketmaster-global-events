from pathlib import Path
import pandas as pd


# Load the newest Ticketmaster CSV
data_folder = Path(__file__).parent / "data"
csv_files = sorted(data_folder.glob("ticketmaster_events_*.csv"))

if not csv_files:
    raise FileNotFoundError("No Ticketmaster CSV file found in the data folder.")

data_file = csv_files[-1]
df = pd.read_csv(data_file)


# Change local_date to date format
df["local_date"] = pd.to_datetime(df["local_date"])

#only US
df = df[df["country_code"] == "US"]

#only five genres
genres = ["Pop", "Country", "R&B", "Hip-Hop/Rap", "Latin"]
df = df[df["genre"].isin(genres)].copy()

df = df.reset_index(drop=True)

states = sorted(df["state_code"].unique())


#[1] Create the main count dataframe
event_counts = (
    df.groupby(["local_date", "state_code", "genre"])
      .size()
      .reset_index(name="event_count")
)


#[2] Filter by date
def filter_by_date(data, start_date=None, end_date=None):

    start = pd.to_datetime(start_date) if start_date is not None else None
    end = pd.to_datetime(end_date) if end_date is not None else None

    if start is not None and end is not None and start > end:
        raise ValueError("Start date cannot be after end date.")

    result = data.copy()

    if start is not None:
        result = result[result["local_date"] >= start]

    if end is not None:
        result = result[result["local_date"] <= end]

    return result


#[3] Get event total using state and genre filters
def count_events(data, state_code=None, genre=None):

    result = data

    if state_code is not None:
        result = result[result["state_code"] == state_code]

    if genre is not None:
        result = result[result["genre"] == genre]

    return int(result["event_count"].sum())


#[4] Count events for each state and genre
def make_state_tables(data):

    state_genre_counts = (
        data.groupby(["state_code", "genre"])["event_count"]
            .sum()
            .reset_index()
    )

    # Keep all five genres for every state in the dataset
    all_groups = pd.MultiIndex.from_product(
        [states, genres],
        names=["state_code", "genre"]
    )

    state_genre_counts = (
        state_genre_counts
        .set_index(["state_code", "genre"])
        .reindex(all_groups, fill_value=0)
        .reset_index()
    )


    # Count total events in each state
    state_counts = (
        state_genre_counts.groupby("state_code")["event_count"]
                          .sum()
                          .reset_index(name="state_total")
    )


    # Percentage of all U.S. events that come from each state
    national_total = state_counts["state_total"].sum()

    if national_total == 0:
        state_counts["state_share_us"] = 0.0
    else:
        state_counts["state_share_us"] = (
            state_counts["state_total"]
            / national_total
            * 100
        ).round(2)


    # Count total events for each genre across the U.S.
    genre_counts = (
        state_genre_counts.groupby("genre")["event_count"]
                          .sum()
                          .reset_index(name="genre_total")
    )


    # Add state totals to the state-genre dataframe
    state_genre_counts = state_genre_counts.merge(
        state_counts[["state_code", "state_total"]],
        on="state_code"
    )


    # Percentage of each genre within a state
    state_genre_counts["genre_share_in_state"] = (
        state_genre_counts["event_count"]
        / state_genre_counts["state_total"]
        * 100
    ).fillna(0).round(2)


    # Add national genre totals
    state_genre_counts = state_genre_counts.merge(
        genre_counts,
        on="genre"
    )


    # Percentage of the national genre total that comes from each state
    state_genre_counts["state_share_of_genre"] = (
        state_genre_counts["event_count"]
        / state_genre_counts["genre_total"]
        * 100
    ).fillna(0).round(2)

    return state_genre_counts, state_counts, genre_counts


#[5] Create summary table for visualization
def make_state_summary(state_genre_counts, state_counts):

    state_summary = state_genre_counts.pivot(
        index="state_code",
        columns="genre",
        values="event_count"
    ).reset_index()

    state_summary = state_summary[
        ["state_code"] + genres
    ]

    state_summary = state_summary.merge(
        state_counts,
        on="state_code"
    )

    state_summary.columns.name = None

    return state_summary