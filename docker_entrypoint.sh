#!/bin/sh

python /app/backend/manage.py makemigrations
python /app/backend/manage.py makemigrations budgetmapper
python /app/backend/manage.py migrate
python /app/backend/manage.py loaddata /app/backend/budgetmapper/fixtures/budget_xlsx_template.json
python /app/backend/manage.py loaddata /app/backend/budgetmapper/fixtures/iconimages.json

python /app/backend/manage.py collectstatic --no-input
rm -rf /app/static/*
mkdir -p /app/static
cp -a /app/backend/staticfiles/* /app/static

python /app/backend/manage.py runserver 0.0.0.0:8000
