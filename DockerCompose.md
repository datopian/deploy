# `docker-compose` howto

## Directory structure

```
|
+- deploy (git cloned from git@github.com:datahq/deploy)
+- assembler (git cloned from git@github.com:datahq/assembler)
+- auth (git cloned from git@github.com:datahq/auth)
+- plans (git cloned from git@github.com:datahq/plans)
+- resolver (git cloned from git@github.com:datahq/resolver)
+- filemanager (git cloned from git@github.com:datahq/filemanager)
+- specstore (git cloned from git@github.com:datahq/specstore)
   +- ...
   +- events_repo (git cloned from git@github.com:datahq/events)
   +- events (symlink to events_repo/events)
   +- planner_repo (git cloned from git@github.com:datahq/planner)
   +- planner (symlink to planner_repo/planner)
+- bitstore (git cloned from git@github.com:datahq/bitstore)
+- frontend (git cloned from git@github.com:datahq/frontend)
+- metastore (git cloned from git@github.com:datahq/metastore)
+- moto (git cloned from git@github.com:akariv/moto.git)
```

## Starting everything

You will need to resolve 127.0.0.1 to `motoserver`. Add the following line to hosts file: `127.0.0.1 motoserver`.

Your `etc/hosts` file should look something like this:

```
127.0.0.1 localhost
127.0.0.1 motoserver
# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
...
```

This will start everything up and create the `core` user.

When in `/deploy/`, run:

```
$ docker-compose down && docker-compose up --build -d

# After everything is up, you should create the default user ('core'):
$ python2 main.py user_create
```


## Using the cli

Use the configuration file `cli.json` as so:

```
$ DATAHUB_JSON=cli.json data --debug push filename.csv --published
```

## Seeing logs

Attach to the specific container you want to observe:

```
$ docker ps
CONTAINER ID        IMAGE                                                 COMMAND                  CREATED             STATUS              PORTS                                   NAMES
560cf5b40c49        dockercloud/haproxy:latest                            "/sbin/tini -- doc..."   3 hours ago         Up 3 hours          443/tcp, 0.0.0.0:80->80/tcp, 1936/tcp   deploy_proxy_1
2a9b2664aeda        deploy_specstore                                      "/bin/sh -c $APP_P..."   3 hours ago         Up 3 hours          0.0.0.0:32999->8000/tcp                 deploy_specstore_1
9c30e7d263cc        deploy_resolver                                       "/bin/sh -c $APP_P..."   3 hours ago         Up 3 hours          0.0.0.0:32998->8000/tcp                 deploy_resolver_1
f141b6aff71b        deploy_rawstore                                       "/bin/sh -c $APP_P..."   3 hours ago         Up 3 hours          0.0.0.0:32997->8000/tcp                 deploy_rawstore_1
cfcffab13f0f        deploy_assembler                                      "/app/startup.sh"        3 hours ago         Up 3 hours          5000/tcp                                deploy_assembler_1
95d95451517e        deploy_metastore                                      "/bin/sh -c $APP_P..."   3 hours ago         Up 3 hours          0.0.0.0:32995->8000/tcp                 deploy_metastore_1
b20c7459e0ea        deploy_auth                                           "/bin/sh -c $APP_P..."   3 hours ago         Up 3 hours          0.0.0.0:32996->8000/tcp                 deploy_auth_1
17907c0d88a2        deploy_frontend                                       "/bin/sh -c 'npm s..."   3 hours ago         Up 3 hours          0.0.0.0:32994->4000/tcp                 deploy_frontend_1
870b8a7f2a3f        motoserver/moto                                       "/usr/bin/moto_ser..."   3 hours ago         Up 3 hours          0.0.0.0:5000->5000/tcp                  deploy_motoserver_1
792dc4c141f5        redis:3.2.11-alpine                                   "docker-entrypoint..."   3 hours ago         Up 3 hours          6379/tcp                                deploy_redis_1
5d14bd728512        postgres                                              "docker-entrypoint..."   3 hours ago         Up 3 hours          0.0.0.0:15432->5432/tcp                 deploy_postgres_1
b539ade1bf4f        docker.elastic.co/elasticsearch/elasticsearch:5.5.1   "/bin/bash bin/es-..."   3 hours ago         Up 3 hours          0.0.0.0:9200->9200/tcp, 9300/tcp        deploy_elasticsearch_1

$ docker attach <container-id> &

## OR as a one liner:

$ docker ps --format {{.ID}} --filter name=assembler | xargs docker attach &
```
