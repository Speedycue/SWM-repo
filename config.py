# config.py

import os # Import the 'os' module for interacting with the operating system,
           # particularly for path manipulation.

# Define the base directory of the application.
# os.path.abspath(__file__) gets the absolute path of the current file (config.py).
# os.path.dirname(...) then gets the directory name of that path.
# This ensures that file paths are resolved correctly regardless of where the script is run from.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Define the main configuration class for the Flask application.
# This class holds various settings that our application will use.
class Config:
    # SECRET_KEY: A secret key used for cryptographic operations,
    # such as signing session cookies and protecting against Cross Site Request Forgery (CSRF) attacks.
    # It's crucial to change this to a strong, unique, and randomly generated value
    # for production deployments to ensure security.
    SECRET_KEY = 'supersecretkey' 

    # SQLALCHEMY_DATABASE_URI: Specifies the connection string for the database.
    # Here, it's configured to use SQLite, a file-based database.
    # os.path.join(BASE_DIR, 'instance', 'skilled_worker.db') constructs the
    # full path to the database file, placing it inside an 'instance' folder
    # within our application's base directory.
    # This keeps the database file organized and separate from source code.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'skilled_worker.db')

    # SQLALCHEMY_TRACK_MODIFICATIONS: A configuration option for Flask-SQLAlchemy.
    # Setting this to False conserves system resources by disabling the Flask-SQLAlchemy
    # event system, which tracks modifications to objects. While useful for debugging,
    # it's generally recommended to set this to False in production environments
    # unless you explicitly need its features.
    SQLALCHEMY_TRACK_MODIFICATIONS = False