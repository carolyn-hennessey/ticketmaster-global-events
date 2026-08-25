from dataframe_utils import (
    df,
    event_counts,
    filter_by_date,
    count_events,
    make_state_tables,
    make_state_summary
)


# [1] Base data
print("\n[1] BASE DATA")
print("Total events:", len(df))
print("First date:", df["local_date"].min())
print("Last date:", df["local_date"].max())


# [2] Main count dataframe
print("\n[2] EVENT COUNTS")
print(event_counts.head(10))
print("Grouped rows:", len(event_counts))
print("Total events:", event_counts["event_count"].sum())


# [3] Example date range
period_counts = filter_by_date(
    event_counts,
    "2026-09-01",
    "2026-09-30"
)

print("\n[3] SEPTEMBER DATA")
print("Grouped rows:", len(period_counts))
print("Total events:", period_counts["event_count"].sum())


# [4] State and genre tables
state_genre_counts, state_counts, genre_counts = make_state_tables(
    period_counts
)

print("\n[4] STATE + GENRE")
print(state_genre_counts.head(20))

print("\n[5] STATE TOTALS")
print(state_counts.head(20))

print("\n[6] GENRE TOTALS")
print(genre_counts)


# [7] Summary table for visualization
state_summary = make_state_summary(
    state_genre_counts,
    state_counts
)

print("\n[7] STATE SUMMARY")
print(state_summary.head(20))


# [8] Example of a same-period comparison
nc_country = count_events(
    period_counts,
    state_code="NC",
    genre="Country"
)

us_country = count_events(
    period_counts,
    genre="Country"
)

if us_country == 0:
    nc_country_share = 0
else:
    nc_country_share = round(
        nc_country / us_country * 100,
        2
    )

print("\n[8] EXAMPLE COMPARISON")
print("NC Country events:", nc_country)
print("U.S. Country events:", us_country)
print("NC share of U.S. Country events:", nc_country_share, "%")