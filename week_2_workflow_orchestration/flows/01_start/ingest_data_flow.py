#!/usr/bin/env python
# coding: utf-8

import os
import argparse
from time import time
from datetime import timedelta

import pandas as pd
from sqlalchemy import create_engine
from prefect import flow, task
from prefect.tasks import task_input_hash
from prefect_sqlalchemy import SqlAlchemyConnector

# extract task:
@task(log_prints=True, retries=3, cache_key_fn=task_input_hash, cache_expiration=timedelta(days=1))
def extract_data(url):
    # since backed up files from data talks are gzipped, need to make sure we include correct extension
    # this is for pandas to know what to do when you call read_csv
    if url.endswith('.csv.gz'):
        csv_file_name = 'output.csv.gz'    
    else:
        csv_file_name = 'output.csv'

    # remember this is the file we're downloading for testing https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2022-01.csv
    # for the 2023 homework, we'll be using green taxi trips 2019-01:
    #   https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2019-01.csv
    os.system(f'wget {url} -O {csv_file_name}')

    # read the csv file for ingestion - specify arrow as engine for csv
    # df_iter = pd.read_csv(csv_file_name, compression='gzip', iterator=True, chunksize=100000)
    df_iter = pd.read_csv(csv_file_name, iterator=True, chunksize=100000)
    
    df = next(df_iter)

    return df

# transform task:
@task(log_prints=True)
def transform_data(df):

    # change type of dates
    df.lpep_pickup_datetime = pd.to_datetime(df.lpep_pickup_datetime)
    df.lpep_dropoff_datetime = pd.to_datetime(df.lpep_dropoff_datetime)

    # remove records where passenger_count is 0
    print(f"pre transform: missing passenger count = {df['passenger_count'].isin([0]).sum()}")
    df = df[df['passenger_count'] != 0]
    print(f"post transform: missing passenger count = {df['passenger_count'].isin([0]).sum()}")
    return df

@task(log_prints=True, retries=3)
def ingest_data(table_name, df):

    connection_block = SqlAlchemyConnector.load("postgres-connector")

    with connection_block.get_connection(begin=False) as engine:
        # create headers for the table
        df.head(n=0).to_sql(name=table_name, con=engine, if_exists='replace')
        # load the data to postgres table
        df.to_sql(name=table_name, con=engine, if_exists='append')

@flow(name="table name log", log_prints=True)
def log_subflow(table_name: str):
    print(f"logging subflow for: {table_name}")

@flow(name="ingest data")
def main_flow(table_name: str):
    file_location = "https://github.com/DataTalksClub/nyc-tlc-data/releases/download/green/green_tripdata_2019-03.csv.gz"

    log_subflow(table_name)
    # extract
    raw_data = extract_data(file_location)
    # transform
    transformed_data = transform_data(raw_data)
    # load
    ingest_data(table_name, transformed_data)    


if __name__ == '__main__':
    main_flow(table_name = "greentaxi")



# original call from week 1 accepts params when the docker container is invoked
# for this exercise, we'll just hard code the params above
""" 
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ingest csv data to postgres')

    # arguments we need to pass to the script:
    parser.add_argument('--user', help='user name for postgres')
    parser.add_argument('--password', help='password for postgres')
    parser.add_argument('--file_location', help='location of the csv file to ingest')
    parser.add_argument('--host_name', help='name of the postgres host')
    parser.add_argument('--port', help='port of the postgres host')
    parser.add_argument('--table_name', help='name of the table to create or update')
    parser.add_argument('--database_name', help='name of the database where the table will be created or updated')

    args = parser.parse_args()

    # call main with the args above
    main(args) 
"""

# connection info:
"""
user = "root"
    password = "root"
    file_location = "https://github.com/DataTalksClub/nyc-tlc-data/releases/download/green/green_tripdata_2019-03.csv.gz"
    host_name = "192.168.50.64"
    port = "5433"
    table_name = "greentaxi"
    database_name = "nytaxi"
"""