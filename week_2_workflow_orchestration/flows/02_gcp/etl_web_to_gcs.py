from pathlib import Path
import pandas as pd
from prefect import task, flow
from prefect_gcp import GcsBucket


@task(log_prints=True, retries=3)
def extract(url: str) -> pd.DataFrame:
    """Extract data from website and convert to a pandas dataframe"""
    df = pd.read_csv(url)
    return df


@task(log_prints=True)
def transform(df=pd.DataFrame) -> pd.DataFrame:
    """Do some data transformations before loading data"""

    # convert date fields to datatime dtype:
    df.lpep_pickup_datetime = pd.to_datetime(df.lpep_pickup_datetime)
    df.lpep_dropoff_datetime = pd.to_datetime(df.lpep_dropoff_datetime)
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


@flow(name="GCS ETL flow", log_prints=True)
def etl_web_to_gcs() -> None:
    """The main ETL to GCS function"""

    # parametrize the taxi files found here: https://github.com/DataTalksClub/nyc-tlc-data/releases/tag/green
    # the url we need to break down is this one: https://github.com/DataTalksClub/nyc-tlc-data/releases/download/green/green_tripdata_2019-03.csv.gz

    taxi_colour = "green"
    year = 2020
    month = 1
    file_name = f"{taxi_colour}_tripdata_{year}-{month:02}"
    file_location = f"https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{taxi_colour}/{file_name}.csv.gz"

    # extract
    df = extract(file_location)
    # transform
    df_clean = transform(df)
    # load
    path = export_local(df_clean, taxi_colour, file_name)
    load_to_gcs(path, taxi_colour, file_name)


if __name__ == "__main__":
    etl_web_to_gcs()
