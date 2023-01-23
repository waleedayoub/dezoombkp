## Get the data for the project
- Where to find the nytaxi data:
  - parquet: [yellow taxi](https://github.com/DataTalksClub/nyc-tlc-data/releases/tag/yellow)
  - csv: no longer available

## How to run postgres and pg-admin on the synology server:

### step 0: get docker context working via ssh:
https://skb.io/blog/2021/03/07/docker-contexts-synology/

### step 0b: make it easy to ssh into the machine by adding a config
- In your home network, find .ssh directory, create a file called config, change its permissions to read and put something like the below in there
- This will allow you to ssh into your machine by just typing the name under Host
```shell
Host seventhirteen
    Hostname 192.168.2.137
    User waleed
    IdentityFile ~/.ssh/id_rsa
```

### step 1: create a network so you can connect across containers
docker network create pg-network

### step 2: run postgres in a container
- if ports are occupied, make sure you map internal port (5432) to something else you know is available (5433)
- basic script:  
```docker
docker run \
  --name pgsql-dev \
  -e POSTGRES_PASSWORD=test1234 \
  -d \
  -p 5433:5432 postgres:13-alpine
```
- more involved script:  
```docker
docker run -it \
  --name pgsql-dev \
#  --user $(id -u):$(id -g) \ # didn't work on synology
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -d \
  -v /volume1/docker/data:/var/lib/postgresql/data \
  -p 5433:5432 \
  --network=pg-network \
  postgres:13-alpine
```
- Once the volume above is mapped, the user/group is changed to user = 70 and group = users
- In order to be able to navigate that directory, make sure you chmod u+rwx

### step 3: run pg-admin on the same network as postgres
```docker
docker run -it \
  --name pgadmin-dev \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -e PGADMIN_LISTEN_ADDRESS=0.0.0.0 \
  -d \
  -p 8080:80 \
  --network=pg-network \
  dpage/pgadmin4
```
- running it like this generates an error on my Synology:
```bash
waleed@seventhirteen:/volume1/docker$ ./runpgadmin.sh

NOTE: Configuring authentication for SERVER mode.

pgAdmin 4 - Application Initialisation
======================================

postfix/postfix-script: starting the Postfix mail system
[2022-10-17 23:53:55 +0000] [1] [INFO] Starting gunicorn 20.1.0
[2022-10-17 23:53:55 +0000] [1] [ERROR] Retrying in 1 second.
[2022-10-17 23:53:56 +0000] [1] [ERROR] Retrying in 1 second.
[2022-10-17 23:53:57 +0000] [1] [ERROR] Retrying in 1 second.
[2022-10-17 23:53:58 +0000] [1] [ERROR] Retrying in 1 second.
[2022-10-17 23:53:59 +0000] [1] [ERROR] Retrying in 1 second.
[2022-10-17 23:54:00 +0000] [1] [ERROR] Can't connect to ('::', 80)
```
Some quick googling suggests this happening on machines where IPv6 is disabled. If you look at [/entrypoint.sh](https://github.com/pgadmin-org/pgadmin4/blob/master/pkg/docker/entrypoint.sh) for the pgadmin4 image, this line here suggests that when gunicorn is launched, it binds to an ipv6

When I look at the Synology network control panel, IPv6 seems to be enabled. (run this to find out: ```sysctl -a 2>/dev/null | grep disable_ipv6```)

Some deeper googling [suggests](https://community.synology.com/enu/forum/1/post/131211) I just downgrade to [pgadmin4:4.8](https://hub.docker.com/layers/dpage/pgadmin4/4.8/images/sha256-81b3aae140d98279b57d7aa3e415bb366522604262ba14bdd6c3f389307466a2?context=explore)

After doing that, hurray, it works!
(Note to self, I should investigate why later versions of pgadmin don't work on the synology. One solution to explore would be to build the pgadmin image myself on the machine I'm using).

With all that out of the way, I can finally craft a docker-compose to fire this up as a set of connected containers:

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

And with that, I've got myself a nice little sandbox running on my synology through a docker context. It should come as no surprise that hardware utilization on my Synology is a fraction of what it is running a Linux VM on my macbook air:

