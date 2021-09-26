#!/bin/bash

# check if all services running
./wait-for-it.sh -t 0 "${MYSQL_HOST}:${MYSQL_PORT}" && echo "MySQL running"
./wait-for-it.sh -t 0 "${RABBITMQ_HOST}:${RABBITMQ_PORT}" && echo "RabbitMQ running"

echo "Checking Django install status"

IS_INSTALLED=$(cat <<EOF | python manage.py shell
from support.views.install import InstallView

if InstallView.is_superuser_exists():
    print('true')
else:
    print('false')
EOF
)

CHECK_EXIT_CODE=$?

echo
echo "IS_INSTALLED == $IS_INSTALLED (exit code: $CHECK_EXIT_CODE)"

if [[ "$IS_INSTALLED" == "false" || "$CHECK_EXIT_CODE" != "0" ]]; then
    echo
    echo "Making migrations"
    python manage.py migrate support zero
    python manage.py makemigrations
    python manage.py migrate
    echo
    echo "Loading fixtures"
    python manage.py loaddata groups
    python manage.py loaddata lines
    python manage.py loaddata settings
    echo "Migrations finished"
fi

export DJANGO_SETTINGS_MODULE=backend.settings
echo "Starting gunicorn"
gunicorn \
    --access-logfile - \
    --workers 5 \
    --bind unix:/run/gunicorn.sock \
    --user=supportbot --group=supportbot \
    --error-logfile /var/log/gunicorn-error.log \
    --capture-output \
    --daemon \
    backend.wsgi:application

# nginx
echo
echo "Starting Nginx"
nginx

sudo --preserve-env -u supportbot bash
cd /home/supportbot/backend

echo
echo "Copying static files"
cp -r $HOME/backend/support/static /var/www/supportbot/
chown -R supportbot:supportbot /var/www/supportbot/static

# Celery
echo
echo "Starting Celery"
celery -A backend worker -l info --pool=solo

