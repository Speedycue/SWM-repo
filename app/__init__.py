# app/__init__.py

# Import the Flask class from the flask package, which is the core of your web application.
from flask import Flask
# Import SQLAlchemy from flask_sqlalchemy, an ORM (Object Relational Mapper)
# that integrates SQLAlchemy with Flask to manage your database.
from flask_sqlalchemy import SQLAlchemy
# Import LoginManager from flask_login, an extension that provides user session management.
from flask_login import LoginManager 
# Import the 'os' module for interacting with the operating system,
# particularly for path manipulation (e.g., for file uploads).
import os

# Initialize the SQLAlchemy database instance.
# This object will be used to define your database models and interact with the database.
# It's initialized here but associated with the Flask app later in create_app.
db = SQLAlchemy()
# Initialize the Flask-Login LoginManager.
# This object handles user sessions, authentication, and user loading.
login_manager = LoginManager() 

# --- Flask-Login: User loader callback ---
# This is a crucial function for Flask-Login. It tells Flask-Login how to load a user
# object from a user ID stored in the session cookie.
# Flask-Login will call this function on each request if a user is logged in,
# providing the 'user_id_and_type' string from the session.
@login_manager.user_loader
def load_user(user_id_and_type):
    """
    Given a user ID and type (e.g., "1_client" or "5_company") retrieved from the session,
    this function queries the database to return the corresponding user object
    (either a Client or a Company instance).

    Args:
        user_id_and_type (str): A string in the format "ID_TYPE" (e.g., "1_client"),
                                 where ID is the user's primary key and TYPE indicates
                                 if it's a 'client' or 'company'.

    Returns:
        Union[Client, Company, None]: The Client or Company object if found, otherwise None.
    """
    # Handle cases where the format might be old or unexpected (e.g., just an ID without type).
    # This acts as a fallback, assuming it's a client for backward compatibility.
    if "_" not in user_id_and_type:
        try:
            client_id = int(user_id_and_type)
            # Import models here to avoid circular dependencies when this file is imported by models.
            from app.models import Client
            return Client.query.get(client_id)
        except ValueError:
            # If conversion to int fails, it's not a valid ID.
            return None

    # Split the incoming string into ID and type (e.g., "1", "client").
    user_id_str, user_type = user_id_and_type.split('_')
    try:
        # Convert the ID part to an integer.
        user_id = int(user_id_str)
    except ValueError:
        # If the ID is not a valid integer, return None.
        return None

    # Import models dynamically here to prevent circular import issues.
    # If app.models was imported at the top, it would cause a circular dependency
    # because models.py also imports db from this __init__.py.
    from app.models import Client, Company 

    # Based on the user type, query the appropriate model for the user.
    if user_type == 'client':
        return Client.query.get(user_id) # Retrieve client by ID.
    elif user_type == 'company':
        return Company.query.get(user_id) # Retrieve company by ID.
    
    # If the user_type is neither 'client' nor 'company', return None.
    return None


# Define the application factory function.
# This function is responsible for creating, configuring, and returning the Flask app instance.
# Using an application factory is a common pattern for larger Flask applications,
# making them more flexible and easier to test.
def create_app():
    # Create the Flask application instance.
    # __name__ tells Flask where to look for templates and static files.
    app = Flask(__name__)
    # Load configuration from the 'Config' class defined in config.py.
    # This sets up secret keys, database URI, and other application-wide settings.
    app.config.from_object('config.Config')

    # --- File Upload Configuration ---
    # Define the absolute path where company profile photos and gallery images will be stored.
    # os.path.join correctly concatenates path components for different operating systems.
    # app.root_path refers to the root directory of your Flask application (the 'app' folder).
    UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'companies')
    # Define a set of allowed file extensions for uploads to prevent malicious file uploads.
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # Add the upload folder and allowed extensions to the Flask app's configuration.
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
    # Optional: Set a maximum content length for uploads (e.g., 16 MB).
    # This helps prevent denial-of-service attacks by large file uploads.
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

    # Create the upload directory if it does not already exist.
    # exist_ok=True prevents an error if the directory already exists.
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    # --- End File Upload Configuration ---

    # --- Jinja2 Global Function Addition ---
    # Make the 'hasattr' Python built-in function available directly within Jinja2 templates.
    # This is useful for conditionally rendering elements based on whether an object has a certain attribute.
    app.jinja_env.globals.update(hasattr=hasattr)
    # --- End Jinja2 Global Addition ---

    # Initialize extensions with the Flask application instance.
    # This connects SQLAlchemy to your app's configuration (like SQLALCHEMY_DATABASE_URI).
    db.init_app(app)
    # This connects Flask-Login to your app, setting up session management.
    login_manager.init_app(app) 
    
    # Set the login view for Flask-Login. If an unauthenticated user tries to access
    # a @login_required route, they will be redirected to this endpoint.
    # 'main.login_choice' refers to the 'login_choice' function within the 'main' blueprint.
    login_manager.login_view = 'main.login_choice' 
    # Set the message category for login redirection messages.
    login_manager.login_message_category = 'info' # Displays a flash message with category 'info'

    # Establish an application context.
    # This is necessary before performing database operations like db.create_all().
    with app.app_context():
        # Import models inside the application context (or after db.init_app).
        # This ensures that models are properly registered with the SQLAlchemy instance 'db'
        # before any database schema creation attempts.
        from app import models

        # Create database tables if they don't exist.
        # This is a convenient way to set up your database schema when the app starts.
        # In production, you'd typically use Flask-Migrate (Alembic) for this.
        db.create_all()

        # Import and register blueprints.
        # Blueprints organize your application into smaller, reusable components.
        # 'main_bp' contains your main routes (e.g., home page, login, registration).
        from app.routes import bp as main_bp
        app.register_blueprint(main_bp)

    # Return the configured Flask application instance.
    return app