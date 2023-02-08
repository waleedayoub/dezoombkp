docker run -it \
  --network=pg-network \
  taxi_ingest:v001 \
    --user=root \
    --password=root \
    --file_location="https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2019-01.parquet" \
    --host_name=pgsql-dev \
    --port=5432 \
    --table_name=greentaxidata \
    --database_name=nytaxi