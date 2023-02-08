docker run -it \
  --name pgsql-dev \
#  --user $(id -u):$(id -g) \ # didn't work on synology
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="testdb" \
  -d \
  -v /volume1/docker/data:/var/lib/postgresql/data \
  -p 5433:5432 \
  --network=pg-network \
  postgres:13-alpine