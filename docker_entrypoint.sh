#!/bin/sh

python /app/backend/manage.py makemigrations wdmmgserver
python /app/backend/manage.py makemigrations budgetmapper
python /app/backend/manage.py migrate
python /app/backend/manage.py collectstatic
python /app/backend/manage.py runserver 0.0.0.0:8000
