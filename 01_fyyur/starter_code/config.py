import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database


# TODO IMPLEMENT DATABASE URL
DATABASE_NAME = "fyyur"
username = 'postgres'
password = '123456'
url = 'localhost:5432'
SQLALCHEMY_DATABASE_URI = "postgres://{}:{}@{}/{}".format(username, password, url, DATABASE_NAME)
