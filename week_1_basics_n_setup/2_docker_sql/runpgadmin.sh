docker run -it \
  --name pgadmin-dev \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -e PGADMIN_LISTEN_ADDRESS=0.0.0.0 \
  -d \
  -p 8080:80 \
  --network=pg-network \
  dpage/pgadmin4:4.8