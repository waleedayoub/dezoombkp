FROM python:3.9

RUN apt-get install wget
RUN pip install pandas sqlalchemy psycopg2 pyarrow

WORKDIR /app

COPY ingest_taxi_data.py ingest_taxi_data.py

ENTRYPOINT [ "python", "-u", "ingest_taxi_data.py" ]