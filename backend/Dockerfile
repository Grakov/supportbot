FROM ubuntu:20.04

ENV DEBIAN_FRONTEND="noninteractive"
RUN apt-get update && apt-get install -y \
    python3 \
    python3-dev \
    python-is-python3 \
    python3-pip \
    nginx-full \
    curl \
    systemd \
    sudo \
    libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install wheel && \
    pip3 install gunicorn && \
    pip3 --default-timeout=100 install -r /tmp/requirements.txt

RUN useradd -m supportbot
RUN mkdir -p /var/www/supportbot ; chown -R supportbot:supportbot /var/www/supportbot
VOLUME /var/www/supportbot

ENV HOME="/home/supportbot"
COPY . $HOME/backend
RUN chown -R supportbot:supportbot $HOME/backend
RUN chmod +x $HOME/backend/wait-for-it.sh; chmod +x $HOME/backend/docker-entrypoint.sh

# nginx
RUN rm /etc/nginx/sites-available/* && rm /etc/nginx/sites-enabled/*
COPY nginx/nginx_vhost /etc/nginx/sites-available/default
COPY nginx/upstream.conf /etc/nginx/conf.d/upstream.conf
RUN ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

EXPOSE 80
USER root
WORKDIR $HOME/backend

ENTRYPOINT ["./docker-entrypoint.sh"]