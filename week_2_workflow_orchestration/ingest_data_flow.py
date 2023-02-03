#!/usr/bin/env python
# coding: utf-8

import os
import pandas as pd
from sqlalchemy import create_engine
import argparse
from time import time

def main(params):

    # map all the parameters you'll pass to the script    
    user = params.user
    password = params.password
    file_location = params.file_location
    host_name = params.host_name
    port = params.port
    table_name = params.table_name
    database_name = params.database_name
    csv_file_name = 'output.csv'

    t_start = time()

    # remember this is the file we're downloading for testing https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2022-01.csv
    # for the 2023 homework, we'll be using green taxi trips 2019-01:
    #   https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2019-01.csv
    os.system(f'wget {file_location} -O {csv_file_name}')
    # create engine connection to the postgres database
    engine = create_engine(f'postgresql://{user}:{password}@{host_name}:{port}/{database_name}')
    engine.connect()

    # read the csv file for ingestion - specify arrow as engine for csv
    df = pd.read_csv(csv_file_name,
                        , compression='gzip'
                        , iterator=True
                        , chunksize=100000)

    # change type of dates
    df.lpep_pickup_datetime = pd.to_datetime(df.lpep_pickup_datetime)
    df.lpep_dropoff_datetime = pd.to_datetime(df.lpep_dropoff_datetime)

    # create the table with the headers
    """
    df.head(n=0).to_sql(name=table_name,
            con=engine,
            if_exists='replace')
    """
    # write data to postgres
    df.to_sql(name=table_name,
            con=engine,
            if_exists='append',
            chunksize=10000)
    
    t_end = time()
    runtime = t_end-t_start

    print("job took a total of %3f seconds to complete" % runtime)

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