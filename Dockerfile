FROM python:3.10-slim-buster
# create a virtual environment
RUN python -m venv /venv
# setup the directory for the project in /lobe
RUN mkdir /lobe
# set the working directory
WORKDIR /lobe
# add the necessary files
ADD migrations migrations
ADD src src
ADD pyproject.toml pyproject.toml
# install the dependencies from the pyproject.toml file
RUN /venv/bin/pip install .
# set the entrypoint
ENTRYPOINT ["/venv/bin/python", "-m", "flask", "--app", "lobe", "run", "--host", "0.0.0.0"]
