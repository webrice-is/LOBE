# L.O.B.E.
LOBE is a recording client made specifically for TTS data collections. It supports multiple collections, single and multi-speaker, and can prompt sentences based on phonetic coverage.

# Setup
Install the project
```
pip install .
```

For additional dependencies for development, run
```
pip install -e .[dev]
```

* ffmpeg is required for audio recording and processing

## Postgresql
LOBE uses a Postgresql database.
A simple setup is provided in the `docker-compose.yaml` file. To start the database, run
```
docker-compose up -d
```
Note that the LOBE application is commented out in the docker-compose file as the application should be run via flask during development.

## Configuration
A Flask instance path is expected to be set in the environment variable `FLASK_INSTANCE_PATH`.
This path should contain a `config.py` file.
Take a look at `instance_folder_dev/config.py` for an example.

## Database migrations
LOBE uses [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/) for database migrations.
Since the application relies on the FLASK_INSTANCE_PATH environment variable, it is useful to set it and export it for other commands.
```
export FLASK_INSTANCE_PATH=(pwd)/instance_folder_dev/
```
To create a new migration, run
```
flask --app lobe db migrate -m "message"
```

To apply the migration, run
```
flask --app lobe db upgrade
```

## Creating initial data
To create the initial roles and configuration, run

```
flask --app lobe user add_default_roles
flask --app lobe configuration add_default
flask --app lobe user add  # this is interactive
```

## Running the application
LOBE is a Flask application. To run it, run
```
flask --app lobe run  # for debugging add --debug and --reload
```
```

# Known bugs
- Playing audio in sessions does not work in Safari
- Greining, does not work. So it is not possible to verify recordings.

