# openspending-backend API Server

## Development

### How to run the development server

#### Environment variables

In order to start the development server, you need to set at least the following two environment variables: `APPLICATION_SECRET_KEY` and `APPLICATION_DATABASE_PASSWORD`.
The convinient way is to place `.env` file in this directory and write these values in it.

#### Setup the database

By default, the PostgreSQL server listening on `localhost:5432` will be used.
You can setup it manually or via the following command:

```
docker-compose -f docker-compose-devel.yml up -d
```

#### Install required Python packages

To setup python packages for development, the following command does the job.
It is highly recommended to use `venv` before you run it.

```
pip install -e ".[dev]"
```

#### Migration

```
python manage.py migrate
```

#### Setup initial data for the database

Run the commands below and you should keep the order of the commands.

```
python ../misc/setup_data/tsukuba_nested.py ../misc/setup_data/tsukuba_nested.json
python ../misc/setup_data/cofog_nested.py ../misc/setup_data/cofog_nested.json
python ../misc/setup_data/tsukuba.py ../misc/setup_data/tsukuba.json

```

#### Run the development server

```
python manage.py runserver
```

## Appendix

### Use of vscode setting file

The vscode setting file for python development file is located in `.vscode/settings.json` from the root of this repository.
With this setting, `black` and `isort` are fired on save.
To take advantage of it, you should install `venv` in `backend/.venv/bin/python`.

### List of supported environmental variables

...
