# run.py

# Import necessary components from the 'app' package.
# 'create_app' is a factory function that sets up the Flask application.
# 'db' is the SQLAlchemy database instance, used for database operations.
from app import create_app, db

# Call the create_app factory function to initialize and configure
# the Flask application instance. This instance will be used to run the web server.
app = create_app()

# This block ensures that the code inside it only runs when the script
# is executed directly (e.g., 'python run.py'), not when imported as a module.
if __name__ == '__main__':
    # Flask applications often need an "application context" to perform
    # certain operations, like interacting with the database.
    # 'with app.app_context():' temporarily pushes an application context,
    # making the application's configuration and extensions (like SQLAlchemy)
    # available for use.
    with app.app_context():
        # Create all database tables defined in your SQLAlchemy models.
        # This function looks at all classes that inherit from 'db.Model'
        # and translates them into corresponding database tables if they don't
        # already exist in the database specified by SQLALCHEMY_DATABASE_URI.
        db.create_all()
    
    # Run the Flask development server.
    # 'debug=True': Enables debug mode, which provides detailed error messages
    # and automatically reloads the server when code changes are detected.
    # IMPORTANT: 'debug=True' should NEVER be used in a production environment
    # due to security risks and performance implications.
    # 'port=5000': Specifies that the server should listen for requests on port 5000.
    # You can access your application in a web browser typically at http://127.0.0.1:5000/
    app.run(debug=True, port=5000)