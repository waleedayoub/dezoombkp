
```toc
```
## Week 1 scratch notes

### useful links:
On container lifecycles: https://www.tutorialworks.com/why-containers-stop/#what-if-my-docker-container-dies-immediately

### full set of steps to get a running docker network and ingestion pipeline
1. docker compose up the pg and pgadmin containers
  - optional is to create a network and specify the network they need to run on
  - map the volumes, especially for the pg container to not lose data
2. docker build the ingestion script
3. call the ingestion script with the correct parameters

## Some useful docker commands
### how to login into the container with a bash prompt (container needs to already be running):
```shell 
docker exec -it pgsql-dev bash
```
### how to start a container with an image and bash into it:
```shell
docker run --interactive --tty --network=pg-network --entrypoint /bin/sh taxi_ingest:v001
```

### how to do a docker build:
```shell
docker build -t taxi_ingest:v001 .
```

### using a docker-compose:
#### final docker-compose used on the synology:
- note the use of tag 4.8 on the pgadmin image

```docker
version: "3.9"

networks:
  pg-network:
    external: true

services:
  pgdatabase:
    container_name: pgsql-dev
    image: postgres:13
    healthcheck:
      test: ["CMD", "pg_isready"]
      interval: 10s
      timeout: 45s
      retries: 10
      start_period: 30s
    volumes:
      - /volume1/docker/data:/var/lib/postgresql/data:rw
    environment:
      - POSTGRES_DB=nytaxi
      - POSTGRES_USER=root
      - POSTGRES_PASSWORD=root
    ports:
      - "5433:5432"
    restart: always
    networks:
      - pg-network

  pgadmin:
    container_name: pgadmin-dev
    image: dpage/pgadmin4:4.8
    volumes:
      - /volume1/docker/pgadmin:/var/lib/pgadmin
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@admin.com
      - PGADMIN_DEFAULT_PASSWORD=root
      - PGADMIN_LISTEN_ADDRESS=0.0.0.0
    ports:
      - 8080:80
    restart: always
    networks:
      - pg-network
    depends_on:
      - pgdatabase
```

#### examples:
```docker
version: "3.9"
services:
  pgsql-db:
    image: postgres:13
    networks:
      - bridge-network-u-know
    hostname: test-db
    healthcheck:
        test: ["CMD", "pg_isready", "-q", "-d", "data-data", "-U", "username"]
        timeout: 45s
        interval: 10s
        retries: 10
    user: 1044:100 #optional
    volumes:
      - /volume1/docker/your-data-folder:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: data-data
      POSTGRES_USER: username
      POSTGRES_PASSWORD: password
    ports:
      - 192.168.2.137:12014:5432
    restart: always

networks:
  bridge-network-u-know:
    external: true 
```
```docker
version: "3.9"
services:
  pgsql-db:
    image: postgres:13
    hostname: test-db
    healthcheck:
        test: ["CMD", "pg_isready", "-q", "-d", "data-data", "-U", "username"]
        timeout: 45s
        interval: 10s
        retries: 10
    user: 1044:100 #optional
    volumes:
      - /volume1/docker/your-data-folder:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: data-data
      POSTGRES_USER: username
      POSTGRES_PASSWORD: password
    ports:
      - 192.168.2.137:12014:5432
    restart: always
```

### for running outside of network
```shell
python ingest_taxi_data.py \
  --user=root \
  --password=root \
  --file_location="https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2022-02.parquet" \
  --host_name=192.168.2.137 \
  --port=5433 \
  --table_name=yellowtaxidata \
  --database_name=nytaxi
```

### for running inside the virtual network
```shell
python ingest_taxi_data.py \
  --user=root \
  --password=root \
  --file_location="https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2021-01.parquet" \
  --host_name=pgsql-dev \
  --port=5432 \
  --table_name=yellowtaxidata \
  --database_name=nytaxi
```

### Once the docker build is complete from above, you can rerun the above with this:
### Be sure to run it in the network
```shell
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
```
```shell
docker run -it taxi_ingest:v001 \
    --user=root \
    --password=root \
    --file_location="https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2022-02.parquet" \
    --host_name=localhost \
    --port=5433 \
    --table_name=yellowtaxidata \
    --database_name=nytaxi
```

## Week 2 scratch notes - Terraform and public cloud resource set up

### Getting Terraform and GCP working
- Terraform:
  - Need to download terraform: https://www.terraform.io/downloads
  - Or just use homebrew:
    - brew tap hashicorp/tap
    - brew install hashicorp/tap/terraform
  - Not that I had to install latest Xcode and Xcode tools for this to work
- GCP:
  - Install gcloud CLI: https://cloud.google.com/sdk/docs/install-sdk
  - Google cloud console: https://console.cloud.google.com/

### Steps to get project, resources and accounts set up in GCP:
- Set up a new project
- Create a new service account
  - Assign the user basic>viewer access
  - Create a new managed JSON key (JSON file will automatically download):
    - file name of key: dtc-de-367718-d447f0bbc32c.json
    - saved to ~/.gc/ 
- NB: Need to make sure the GCP SDK is installed (previous step)
- Make sure the google environment variable points to the auth key:
  - ``` export GOOGLE_APPLICATION_CREDENTIALS="/Users/waleed/.gc/dtc-de-367718-d447f0bbc32c.json" ```
  - refresh the token and verify the authentication using the SDK:
    - ``` gcloud auth application-default login ```
    - in case gcloud doesn't work, just use it from wherever the google-cloud-sdk folder is located (in my case, I put it in ~/development/)
- GCP should now be configured

- Next up, we'll need a data lake (GCS bucket) and a data warehouse (BQ):
- To do that, we'll need to grant our service account access to various services and IAM roles to those services
- This can be done by editing the service account user and adding the following IAM roles
  - Services:
    - Storage Admin
    - Storage Object Admin
    - BigQuery Admin and Viewer
- We then enable the iam and iamcredentials APIs for our project:
  - You can navigate to these by going to the google main dashboard and browsing the APIs
  - https://console.cloud.google.com/apis/library/iam.googleapis.com
  - https://console.cloud.google.com/apis/library/iamcredentials.googleapis.com

### Creating terraforms
- There's a lot to go through here, but the basics are:
  - There is a main.tf and a variables.tf (other options files exist too)
  - In main.tf is where you specific your resource provider (e.g. google) and the resources you want to deploy (e.g. gcs bucket, bq data warehouse, etc.)
  - In variables.tf is where you can specific resource specific variables that you don't want to clutter the main.tf with
    - This includes things like your project id, storage classes, regions, etc.

  - Once you have your terraform files ready to go, you need to run:
``` terraform
terraform init
terraform apply
terraform destroy
```
  - These do what they sound like

## Running a parallel process in Azure

## Airflow setup


