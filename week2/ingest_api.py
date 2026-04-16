import pandas as pd 
from pathlib import Path
# --- Data ingestion function --
def load_data(path:str) -> pd.DataFrame:
    """Load CSV data into a DataFrame"""
    df = pd.read_csv(path)
    return df

#--- Dataa cleaning functions ---

def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.lower()
    return df

def strip_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].str.strip()
    return df

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["director", "cast", "country", "rating"]:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")
    return df

def convert_date(df: pd.DataFrame) -> pd.DataFrame:
    df["date_added"] = pd.to_datetime(df["date_added"], errors = "coerce")
    return df

def remove_duplicates(df: pd.DataFrame) ->pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(
        subset = "show_id", keep = "first"
    )
    after  = len(df)
    print(f"Dropped {before - after} duplicate rows")
    assert df["show_id"].is_unique, "Duplicate show_id found after dropping duplicates"
    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = standardize_columns(df)
    df = strip_whitespace(df)
    df = handle_missing_values(df)
    df = convert_date(df)
    df = remove_duplicates(df)
    return df

#--- Data transformation functions ---

def extract_duration_value(df: pd.DataFrame) -> pd.DataFrame:
    df["duration_value"] = df["duration"].str.extract(r"(\d+)")[0].astype("int64")
    return df

def extract_duration_unit(df: pd.DataFrame) -> pd.DataFrame:
    df["duration_unit"] = df["duration"].str.extract(r"([a-zA-Z]+)")[0].str.lower()
    return df

def normalize_duration_unit(df: pd.DataFrame) -> pd.DataFrame:
    df["duration_unit"] = df["duration_unit"].replace(
        {"mins": "min", 
        "minutes": "min", 
        "seasons": "season", 
        "season": "season"
        }
    )
    return df

def transform_duration(df: pd.DataFrame) -> pd.DataFrame:
    df = extract_duration_value(df)
    df = extract_duration_unit(df)
    df = normalize_duration_unit(df)
    return df

def transform_genres(df: pd.DataFrame) -> pd.DataFrame:
    df["genres"] = df["listed_in"].str.split(",")
    return df

def clean_genres(df: pd.DataFrame) -> pd.DataFrame:
    df["genres"] = df["genres"].apply(
        lambda x: [genre.strip() for genre in x] if isinstance(x, list) else x
    )
    return df

def transform_genres_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    df = transform_genres(df)
    df = clean_genres(df)
    return df

def create_is_movie(df: pd.DataFrame) -> pd.DataFrame:
    df["is_movie"] = df["type"] == "Movie"
    return df

def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    df = transform_duration(df)
    df = transform_genres_pipeline(df)
    df = create_is_movie(df)
    return df
# --- Saving the cleaned and transformed data ---
def save_data(df: pd.DataFrame, path:str) ->None:
    path_obj = Path(path)

    #Ensure the directory exists
    path_obj.parent.mkdir(parents = True, exist_ok = True)

    # Save the DataFrame to CSV
    df.to_csv(path, index = False)

    # Save the DataFrame to Parquet
    parquet_path = path_obj.with_suffix(".parquet")
    df.to_parquet(parquet_path, index = False)

    # Save the DataFrame to JSON
    json_path = path_obj.with_suffix(".json")
    df.to_json(json_path, orient = "records", lines = True)


def main() -> None:
    path = "week2/data/raw/netflix.csv"
    df = load_data(path)
   # print("Shape:", df.shape)
   # print("\n Columns: ", df.columns)
   # print("\nFirst rows\n: ", df.head())
    df = clean_data(df)
   # print(df.columns)
   # print(df["type"].unique())
   # print(df["country"].head(5))
   # print("Missing values:\n", df.isnull().sum())
   # print("Data types:\n", df.dtypes)
    df = transform_data(df)
    print(df[["duration", "duration_value", "duration_unit"]].head(5))
    print(df[["listed_in", "genres"]].head(5))
    # Debug after the split 
    print(df["genres"].iloc[1])
    print(type(df["genres"].iloc[1]))
    print(repr(df["genres"].iloc[1]))
    print(df["is_movie"].head(5))
    save_data(df, "week2/data/processed/netflix_processed.csv")

if __name__ == "__main__":
    main()