import pandas as pd
from week2.ingest_api import (
    handle_missing_values,
    convert_date,
    transform_duration,
    remove_duplicates,
    transform_genres_pipeline,
    standardize_columns,
    strip_whitespace,
    create_is_movie
)
def test_handle_missing_values():
    df = pd.DataFrame({
        "director": [None],
        "cast": [None],
        "country": [None],
        "rating": [None]
    })
    df = handle_missing_values(df)
    assert df["director"].iloc[0] == "Unknown"
    assert df["cast"].iloc[0] == "Unknown"
    assert df["country"].iloc[0] == "Unknown"
    assert df["rating"].iloc[0] == "Unknown"
    
def test_convert_date():
    df = pd.DataFrame({
        "date_added": ["September 9, 2019", None]
    })
    df = convert_date(df)

    # Check dtype is datetime
    assert pd.api.types.is_datetime64_any_dtype(df["date_added"])

    # Check valid date parsed correctly
    assert df["date_added"].iloc[0] == pd.Timestamp("2019-09-09")

    #Check invalid date is NaT
    assert pd.isna(df["date_added"].iloc[1])

def test_remove_duplicates():
    df = pd.DataFrame({
        "show_id": ["s1", "s2", "s1"],
        "title": ["Title 1", "Title 2", "Title 1 Duplicate"]
    })
    df = remove_duplicates(df)

    # Ensure only unique show_id remains
    assert df["show_id"].nunique() == len(df)

    #Ensure correct number of rows
    assert len(df) == 2

def test_transform_duration():
    df = pd.DataFrame({
        "duration": ["90 min", "2 seasons", "45 mins", "1 season"]
    })
    df = transform_duration(df)

    # Check duration_value extracted correctly
    assert df["duration_value"].iloc[0] == 90
    assert df["duration_value"].iloc[1] == 2
    assert df["duration_value"].iloc[2] == 45
    assert df["duration_value"].iloc[3] == 1
    # Check duration_unit extracted and normalized correctly
    assert df["duration_unit"].iloc[0] == "min"
    assert df["duration_unit"].iloc[1] == "season"
    assert df["duration_unit"].iloc[2] == "min"
    assert df["duration_unit"].iloc[3] == "season"

def test_transform_genres_pipeline():
    df = pd.DataFrame({
        "listed_in": ["Comedy", "Drama"]
    })
    df = transform_genres_pipeline(df)
    
    #Check type
    assert isinstance(df["genres"].iloc[0], list)
    assert isinstance(df["genres"].iloc[1], list)

    #Check values
    assert df["genres"].iloc[0] == ["Comedy"]
    assert df["genres"].iloc[1] == ["Drama"]

def test_standardize_columns():
    df = pd.DataFrame(
        columns = ["Show ID", "Title"]
    )  
    df = standardize_columns(df)
    assert list(df.columns) == ["show_id", "title"]

def test_strip_whitespace():
    df = pd.DataFrame({
        "title": ["  Movie Title  ", "  Another Title  "]
    })
    df = strip_whitespace(df)
    assert df["title"].iloc[0] == "Movie Title"
    assert df["title"].iloc[1] == "Another Title"

def test_create_is_movie():
    df = pd.DataFrame({
        "type": ["Movie", "TV Show"]
    }) 

    df = create_is_movie(df)

    assert df["is_movie"].iloc[0] == True
    assert df["is_movie"].iloc[1] == False