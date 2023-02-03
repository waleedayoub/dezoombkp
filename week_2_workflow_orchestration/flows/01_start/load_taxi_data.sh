docker run -it \
  --network=pg-network \
  taxi_ingest:v001 \
    --user=root \
    --password=root \
    --file_location="https://github.com/DataTalksClub/nyc-tlc-data/releases/download/green/green_tripdata_2019-02.csv.gz" \
    --host_name=pgsql-dev \
    --port=5432 \
    --table_name=greentaxi \
    --database_name=nytaxi