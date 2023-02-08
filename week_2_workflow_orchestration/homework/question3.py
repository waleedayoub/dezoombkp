from pathlib import Path
from datetime import timedelta

import pandas as pd

from prefect import task, flow
from prefect_gcp import GcsBucket
from prefect_gcp import GcpCredentials
from prefect_gcp.bigquery import bigquery_load_cloud_storage
from prefect.tasks import task_input_hash


# extract data from url and return a dataframe
@task(
    log_prints=True,
    retries=3,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(days=1),
)
def extract_to_df(url: str, colour: str, file_name: str) -> Path:
    """Extract data from website, convert to pandas dataframe -> parquet -> load to GCS"""

    # read the data into a dataframe
    df_temp = pd.read_csv(url)

    local_file_path = Path(
        f"/Users/waleed/Documents/school/datatalksclub/data-engineering-zoomcamp/week_2_workflow_orchestration/data/{colour}taxidata/{file_name}.parquet"
    )
    # convert dataframe to parquet
    df_temp.to_parquet(local_file_path, compression="gzip")

    df = pd.read_parquet(local_file_path)

    return df


# load to bigquery task
@task(log_prints=True)
def load_to_bq(taxi_colour: str, df: pd.DataFrame) -> None:
    """Load task to write data to bigquery table"""

    # load gcp credentials
    gcp_credentials_block = GcpCredentials.load("de-gcp-creds")

    df.to_gbq(
        destination_table=f"trips_data_all.{taxi_colour}taxidata",
        project_id="possible-lotus-375803",
        credentials=gcp_credentials_block.get_credentials_from_service_account(),
        chunksize=500_000,
        if_exists="append",
    )


# main flow
@flow(name="GCS to BQ subflow", log_prints=True)
def etl_gcs_to_bq(taxi_colour, year, month) -> int:
    """ETL subflow to load data from gcs to bigquery"""

    file_name = f"{taxi_colour}_tripdata_{year}-{month:02}"
    file_location = f"https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{taxi_colour}/{file_name}.csv.gz"

    # get data from the web, save locally and return a dataframe
    df = extract_to_df(file_location, taxi_colour, file_name)

    # load the data to BQ using pd.DataFrame.to_gbq
    load_to_bq(taxi_colour, df)

    return len(df)


@flow(name="Load to BQ main flow", log_prints=True)
def bq_main_flow(taxi_colour: str, year: int, months: list[int]) -> None:
    """Main flow that calls the subflow"""
    i = 0
    for month in months:
        i += etl_gcs_to_bq(taxi_colour, year, month)

    print(f"there are {i} rows processed")


if __name__ == "__main__":
    taxi_colour = "yellow"
    year = 2019
    months = [2, 3]
    bq_main_flow(taxi_colour, year, months)
