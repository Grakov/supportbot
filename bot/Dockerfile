FROM ubuntu:20.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-dev \
    python-is-python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install wheel && \
    pip3 --default-timeout=100 install -r /tmp/requirements.txt

RUN useradd -m supportbot
RUN mkdir -p /var/www/supportbot ; chown -R supportbot:supportbot /var/www/supportbot
VOLUME /var/www/supportbot

ENV HOME="/home/supportbot"
COPY . $HOME/supportbot
RUN chown -R supportbot:supportbot $HOME/supportbot
RUN chmod +x $HOME/supportbot/wait-for-it.sh; chmod +x $HOME/supportbot/docker-entrypoint.sh

USER supportbot
WORKDIR $HOME/supportbot

ENTRYPOINT ["./docker-entrypoint.sh"]