# setup_db.py

# Import necessary components from the 'app' package.
# 'create_app' is the factory function to initialize the Flask application.
# 'db' is the SQLAlchemy database instance, used to interact with the database.
from app import create_app, db

# Initialize the Flask application by calling the create_app factory function.
# This sets up your application with its configurations and extensions.
app = create_app()

# Establish an application context.
# This is crucial because database operations (like creating tables)
# require the Flask application to be configured and active.
# 'with app.app_context():' temporarily pushes this context,
# allowing database commands to run correctly outside of a running web server.
with app.app_context():
    # Create all database tables.
    # This command inspects all models defined in your application (that inherit from db.Model)
    # and generates the corresponding tables in the database specified in your config (e.g., skilled_worker.db).
    # If the tables already exist, this command typically does nothing, it won't overwrite them.
    db.create_all()
    
    # Print a confirmation message to the console once the tables are created.
    # This confirms that the script has run successfully and the database schema is set up.
    print("Database tables created!")