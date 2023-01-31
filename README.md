# DoMG
Web based docker container manager. And `/etc/hosts` updater.

[![Build](https://github.com/talpah/domg/actions/workflows/makefile.yml/badge.svg)](https://github.com/talpah/domg/actions/workflows/makefile.yml)

## Logic
This app will update the `/etc/hosts` file in realtime based on the Docker events of starting/stopping docker containers.

It needs to be running at the time the new containers are started to be able to see the docker events.

It looks at each new started container for 2 values: `hostname` and `domainname`. It will use those 2 values to provide a FQDN in the `hosts` file so you can access local containers by hostname instead of ip address.

### Example:

Start a docker container with the hostname `apache-local` and domain name `local-dev`. DoMG will create an entry in the hosts file:
```
172.xx.xx.xx apache-local.local-dev
```
You can now access the container's port 80 via http://apache-local.local-dev/


## Running

### Docker-Compose
 1. Create a `docker-compose.yml` file somewhere.
 2. Put this in it:
```yaml
apps:
  image: talpah/domg
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
    - /etc/hosts:/host_hosts
  hostname: containers
  domainname: domg
```
 3. Run `docker-compose up -d`
 4. Access [http://containers.domg/](http://containers.domg/)

### Docker Run

1. Run it directly:
```shell
docker run --rm --name containers -v /var/run/docker.sock:/var/run/docker.sock -v /etc/hosts:/host_hosts --hostname containers --domainname domg talpah/domg
```
