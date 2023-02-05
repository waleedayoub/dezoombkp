from pathlib import Path
import pandas as pd
from prefect import task, flow
from prefect_gcp import GcsBucket
from prefect_gcp import GcpCredentials


# extract task
@task(log_prints=True, retries=3)
def extract_from_gcs(taxi_colour: str, year: int, month: int) -> Path:
    """Download trip data from GCS and save it locally"""

    gcs_path = f"data/{taxi_colour}/{taxi_colour}_tripdata_{year}-{month:02}.parquet"
    local_path = f"/Users/waleed/Documents/school/datatalksclub/data-engineering-zoomcamp/week_2_workflow_orchestration/data/gcs/"

    gcs_connection_block = GcsBucket.load("taxidata-gcs")
    gcs_connection_block.get_directory(from_path=gcs_path, local_path=local_path)
    return Path(f"{local_path}/{gcs_path}")


# transform task
@task(log_prints=True)
def transform(path: Path) -> pd.DataFrame:
    """Transformations on the dataset"""
    df = pd.read_parquet(path)

    # change type of dates
    df.lpep_pickup_datetime = pd.to_datetime(df.lpep_pickup_datetime)
    df.lpep_dropoff_datetime = pd.to_datetime(df.lpep_dropoff_datetime)

    # remove records where passenger_count is 0
    print(
        f"pre transform: missing passenger count = {df['passenger_count'].isin([0]).sum()}"
    )
    df = df[df["passenger_count"] != 0]
    print(
        f"post transform: missing passenger count = {df['passenger_count'].isin([0]).sum()}"
    )
    return df


# load to bigquery task
@task(log_prints=True)
def load_to_bq(df: pd.DataFrame) -> None:
    """Load task to write data to bigquery table"""

    # load gcp credentials
    gcp_credentials_block = GcpCredentials.load("de-gcp-creds")

    df.to_gbq(
        destination_table="trips_data_all.greentaxidata",
        project_id="possible-lotus-375803",
        credentials=gcp_credentials_block.get_credentials_from_service_account(),
        chunksize=500_000,
        if_exists="append",
    )


# main flow
@flow(name="GCS to BQ", log_prints=True)
def etl_gcs_to_bq():
    """Main etl flow to load data from gcs to bigquery"""

    taxi_colour = "green"
    year = 2020
    month = 1

    # extract
    path = extract_from_gcs(taxi_colour, year, month)
    # transform
    df = transform(path)
    # load
    load_to_bq(df)


if __name__ == "__main__":
    etl_gcs_to_bq()
