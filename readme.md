# SupportBot 

Telegram bot, which allows process support requests from users. Includes Support Portal (django backend) and bot itself.

* [Demo](#demo)
* [Installation and running](#installation-and-running)
    * [Manual](#manual)
        * [Installation](#installation)
        * [Running Bot](#running-bot)
        * [Running Support Portal](#running-support-portal)
    * [Docker](#docker)
        * [docker-compose](#docker-compose) 
        * [MySQL and RabbitMQ](#mysql-and-rabbitmq)
        * [Support Portal](#support-portal)
        * [Bot](#bot)
* [Post-installation steps](#post-installation-steps)
    * [Creating first administrator](#creating-first-administrator)
    * [Location picker support](#location-picker-support)
  

## Demo
Demo Telegram Bot available here: [@NotSupportTestBot](https://t.me/NotSupportTestBot)

Demo Support Portal available at [https://supportbot.sychusha.com/](https://supportbot.sychusha.com/)

Test accounts:
* Support:
```
username: demo_support
password: support_test
```
* Administrator:
```
username: demo_admin
password: administrator_test
```

In order to prevent abusing demo server, it runs in demo mode: some features, like creating new staff users or creating/editing settings, are not available. 

## Installation and running
### Manual
#### Installation
* Download and setup [Mysql](https://dev.mysql.com/doc/refman/8.0/en/installing.html) and [RabbitMQ](https://www.rabbitmq.com/download.html).
* Create separate [virtual environments](https://docs.python.org/3/tutorial/venv.html) for `bot` and `backend`.
* Install via ``pip`` packages listed in ``requirements.txt`` for every matching virtual environment.
* If you don't already have a Telegram bot, [create](https://core.telegram.org/bots#6-botfather) one and obtain authorization token.
* Paste your Telegram bot's token in ``bot/.env`` file: 

```
BOT_TOKEN="TOKEN:GOES_HERE"
```
Alternatively you can paste it in ``docker-compose.yaml`` in ``environment`` section for bot service (Docker only).

Bot and Portal settings are available in ``bot/config.py`` and ``backend/backend/settings.py``.

For Support Portal you should specify your domain:
* Directly in django settings file on `ALLOWED_HOSTS` variable.
* Via environment variable `HTTP_HOSTS`. You can specify multiple domains separated by commas.

Django `SECRET_KEY` should be passed via environment variable `SECRET_KEY`.

MySQL and RabbitMQ connections settings could be also specified via environment variables (for both Bot and Support Portal) or in the `.env` files:

```
MYSQL_HOST='127.0.0.1'
MYSQL_PORT='3306'
MYSQL_DBNAME='support_bot'
MYSQL_USER='root'
MYSQL_PASSWORD='password'

RABBITMQ_PORT='5672'
RABBITMQ_HOST='localhost'
```

#### Running Bot
* On Linux
```
python bot/main.py
```
* On Windows
```
python bot\main.py
```

#### Running Support Portal
Start as usual Django application from `backend` directory:
* [The development server](https://docs.djangoproject.com/en/3.2/intro/tutorial01/#the-development-server)
* [Deploying Django](https://docs.djangoproject.com/en/3.2/howto/deployment/)

If `DEBUG = True`, `django.contrib.staticfiles` will be automatically enabled. Otherwise, you should use webserver (like [Nginx](https://nginx.org/) or [Apache](https://httpd.apache.org/)) to serve static files. 

Before starting server, you should make initial migration and fixtures import:
```
python manage.py migrate support zero
python manage.py makemigrations
python manage.py migrate

python manage.py loaddata groups
python manage.py loaddata lines
python manage.py loaddata settings
```

## Docker
You can use Dockerfiles from this project to run SupportBot in Docker.
Dockerfiles are available separately for all instances: `bot`, `backend` and `mysql`.

Before running any container, you should create three docker volumes for file storage, mysql and rabbitmq data:
```
docker volume create supportbot_file_storage
docker volume create supportbot_mysql_storage
docker volume create supportbot_rabbitmq
```

By default, nginx on `backend` container is configured to be used as ``proxy_pass`` backend. So webserver on your host is required.

In these examples environmental variables are passed into containers via `-e` argument of `docker` command. But you can also place `.env` files with them on the subdirectories of the components. These files will be placed directly in the containers.

### docker-compose
This is the simplest way to deploy the bot:
```
docker-compose up -d
```
Or you can start services separately via ``docker-compose start <service-name>``.

You can edit some settings, like `BOT_TOKEN` or other, from the previous section, in environment variables in `docker-compose.yaml`. Or you can build containers with `.env` files (only for `bot` and `backend`).

Outgoing port for Nginx should be also described in the `backend` section in `docker-compose.yaml`:
```
services:
  ...
  backend:
    ...
    ports:
      - "127.0.0.1:PORT:80"
```
Where `PORT` should be replaced with a port, which would be used as outgoing from container.

### MySQL and RabbitMQ
```
docker image build -t supportbot_mysql mysql/
docker container run -d --name supportbot_mysql -p 127.0.0.1:3306:3306 -e 'MYSQL_ROOT_PASSWORD=password' \
    -v supportbot_mysql_storage:/var/lib/mysql supportbot_mysql
docker run -d --name supportbot_rabbitmq -p 127.0.0.1:5672:5672 \
    -v supportbot_rabbitmq:/var/lib/rabbitmq rabbitmq:3
```
Where `password` should be replaced with selected MySQL root password

### Support Portal
Make Docker image via ``Dockerfile`` and run container based on it:
```
docker image build -t supportbot_backend backend/
docker container run -d --name supportbot_backend -p 127.0.0.1:PORT:80 \
    -v supportbot_file_storage:/var/www/supportbot supportbot_backend \
    -e 'SECRET_KEY=DJANGO_SECRET_KEY' \
    -e 'MYSQL_HOST=localhost' \
    -e 'MYSQL_PORT=3306' \
    -e 'MYSQL_USER=root' \
    -e 'MYSQL_PASSWORD=password' \
    -e 'MYSQL_DB=support_bot' \
    -e 'RABBITMQ_HOST=localhost' \
    -e 'RABBITMQ_PORT=5672' \
    -e 'DEBUG=false'
```

Replace `PORT` with host server port, which would be used to access webserver on the container via HTTP.

Also replace `password` from `MYSQL_PASSWORD` with password from previous section. 

If you are using your own MySQL server, then change values of `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD` and `MYSQL_DBMANE` variables.

### Bot
Make Docker image via ``Dockerfile`` and run container based on it:
```
docker image build -t supportbot_bot backend/
docker container run -d --name supportbot_bot \
    -v supportbot_file_storage:/var/www/supportbot supportbot_bot \
    -e 'BOT_TOKEN=BOT_TOKEN' \
    -e 'MYSQL_HOST=localhost' \
    -e 'MYSQL_PORT=3306' \
    -e 'MYSQL_USER=root' \
    -e 'MYSQL_PASSWORD=password' \
    -e 'MYSQL_DB=support_bot' \
    -e 'RABBITMQ_HOST=localhost' \
    -e 'RABBITMQ_PORT=5672' \
    -e 'BACKEND_HOST=localhost' \ 
    -e 'BACKEND_PORT=PORT' \
    -e 'DEBUG=false'
```
Bot container should wait for Nginx on the `backend` container. So you should pass variables `BACKEND_HOST` and `BACKEND_PORT`.

Like in the previous section, `MYSQL_PASSWORD` should be set with password of mysql `root` user.

## Post-installation steps
### Creating first administrator
For creating first administrator staff user, you should open this URL:
```
http://yourdomain.ru/install/
```
Installation page will request `APP_SETUP_PASSWORD`. You can find it in server output (after requesting installation page) or in the MySQL database in the `support_settings` table:
```
SELECT * FROM support_settings WHERE key='APP_SETUP_PASSWORD';
```

If you deployed Support Bot via default docker-compose config, you can run this command:
```
sudo docker exec -it supportbot_backend grep 'APP_SETUP_PASSWORD' /var/log/gunicorn-error.log | tail -n 1
```

### Location picker support
Support Portal uses [MapBox API](https://mapbox.com/) for location picker dialog on the chats interface. In order to use it, you should:
* Create account on [MapBox](https://account.mapbox.com/).
* [Create](https://account.mapbox.com/access-tokens/) a new access token or copy `Default public token`.
* Edit `mapbox.api_token` setting on Settings page of your Support Portal: paste access token to setting value and save it.
