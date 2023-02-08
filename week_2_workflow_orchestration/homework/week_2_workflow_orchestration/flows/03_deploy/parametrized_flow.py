from pathlib import Path
import pandas as pd
from prefect import task, flow
from prefect_gcp import GcsBucket
from prefect.tasks import task_input_hash
from datetime import timedelta


@task(
    log_prints=True,
    retries=3,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(days=1),
)
def extract(url: str) -> pd.DataFrame:
    """Extract data from website and convert to a pandas dataframe"""
    df = pd.read_csv(url)
    return df


@task(log_prints=True)
def transform(df=pd.DataFrame) -> pd.DataFrame:
    """Do some data transformations before loading data"""

    # convert date fields to datatime dtype:
    df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
    df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)
    print(df.head(2))
    print(f"columns dtypes: {df.dtypes}")
    print(f"number of rows: {len(df)}")
    return df


@task(log_prints=True)
def export_local(df: pd.DataFrame, colour: str, file_name: str) -> Path:
    """Convert csv data to parquet and store locally in a nice directory structure"""
    local_file_path = Path(
        f"/Users/waleed/Documents/school/datatalksclub/data-engineering-zoomcamp/week_2_workflow_orchestration/data/{colour}taxidata/{file_name}.parquet"
    )
    df.to_parquet(local_file_path, compression="gzip")
    return local_file_path


@flow(log_prints=True)
def load_to_gcs(local_file_path: Path, colour: str, file_name: str) -> None:
    """Upload parquet file from local file path to GCS"""

    gcs_connection_block = GcsBucket.load("taxidata-gcs")
    gcs_connection_block.upload_from_path(
        from_path=local_file_path, to_path=f"data/{colour}/{file_name}.parquet"
    )

    return


@flow(name="GCS ETL subflow", log_prints=True)
def etl_web_to_gcs(taxi_colour: str, year: int, month: int) -> None:
    """Subflow for ETL to GCS function"""

    # parametrize the taxi files found here: https://github.com/DataTalksClub/nyc-tlc-data/releases/tag/green
    # the url we need to break down is this one: https://github.com/DataTalksClub/nyc-tlc-data/releases/download/green/green_tripdata_2019-03.csv.gz

    file_name = f"{taxi_colour}_tripdata_{year}-{month:02}"
    file_location = f"https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{taxi_colour}/{file_name}.csv.gz"

    # extracts from file_location and returns a pandas dataframe
    df = extract(file_location)
    # transforms data and returns a pandas dataframe again
    df_clean = transform(df)
    # load 1: takes a dataframe and stores it locally as a parquet file
    path = export_local(df_clean, taxi_colour, file_name)
    # load 2: takes a local parquet file and uploads it to GCS
    load_to_gcs(path, taxi_colour, file_name)


@flow(name="GCS ETL main flow", log_prints=True)
def etl_main_flow(taxi_colour: str, year: int, months: list[int]) -> None:
    """Main flow that sends inputs to the GCS ETL subflow as parameters"""
    for month in months:
        etl_web_to_gcs(taxi_colour, year, month)


if __name__ == "__main__":
    taxi_colour = "yellow"
    year = 2019
    months = [2, 3]
    etl_main_flow(taxi_colour, year, months)
