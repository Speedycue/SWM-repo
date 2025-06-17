# app/models.py

# Import the SQLAlchemy database instance from the main application package.
# This 'db' object is used to define your database models.
from app import db
# Import datetime for handling date and time objects, and timezone for making them timezone-aware.
from datetime import datetime, timezone
# Import UserMixin from Flask-Login. This class provides generic implementations
# for properties and methods that Flask-Login expects from your user model.
from flask_login import UserMixin
# Import password hashing utilities from Werkzeug, used for secure password storage.
from werkzeug.security import generate_password_hash, check_password_hash

# --- Client Model ---
# Represents individual clients who use the platform to find services.
# Inherits from UserMixin for Flask-Login integration and db.Model for SQLAlchemy ORM functionality.
class Client(UserMixin, db.Model):
    # Defines the table name in the database.
    __tablename__ = 'clients'
    # Primary key: Unique identifier for each client.
    client_id = db.Column(db.Integer, primary_key=True)
    # Client's name: A string up to 100 characters, cannot be null.
    name = db.Column(db.String(100), nullable=False)
    # Client's email: A string up to 120 characters, must be unique, cannot be null.
    # Used for login and contact.
    email = db.Column(db.String(120), unique=True, nullable=False)
    # Hashed password: Stores the secure hash of the client's password.
    password = db.Column(db.String(128), nullable=False)

    # Relationships: Define how Client records relate to other tables.
    # 'saved_companies': A list of companies this client has saved.
    #   - 'SavedCompany': The related model.
    #   - 'backref='client'': Creates a 'client' attribute on SavedCompany, linking back to the Client.
    #   - 'lazy=True': Loads related objects only when they are accessed (improves performance).
    saved_companies = db.relationship('SavedCompany', backref='client', lazy=True)
    # 'ratings': A list of ratings this client has given to companies.
    ratings = db.relationship('Rating', backref='client', lazy=True)
    # 'sent_messages': Messages sent by this client.
    #   - 'foreign_keys': Explicitly tells SQLAlchemy which foreign key to use for this relationship.
    #     This is needed because the Message table has two foreign keys pointing back to Client.
    #   - 'backref='sender_client'': Creates a 'sender_client' attribute on Message.
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_client_id', backref='sender_client', lazy=True)
    # 'received_messages': Messages received by this client.
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_client_id', backref='receiver_client', lazy=True)

    def set_password(self, password):
        """Hashes the given password and stores it securely."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the given plain password matches the stored hashed password."""
        return check_password_hash(self.password, password)

    # --- CRITICAL CHANGE 1: Return ID with type for Flask-Login ---
    # Flask-Login's `user_loader` needs a way to distinguish between different types of users
    # (Client vs. Company) if both can log in. This method returns a unique ID string
    # that includes both the user's primary key and their type.
    def get_id(self):
        """
        Returns a unique identifier for the user session, combining client_id and type.
        Example: "1_client"
        """
        return f"{self.client_id}_client"

    # --- CRITICAL CHANGE 2: Helper properties for template logic and authorization ---
    # These properties make it easier to check the user type in templates or route logic.
    @property
    def is_client(self):
        """Returns True if the user is a client."""
        return True

    @property
    def is_company(self):
        """Returns False if the user is a client (i.e., not a company)."""
        return False

    def __repr__(self):
        """Provides a helpful string representation for debugging."""
        return f"<Client {self.name}>"

# --- Company Model ---
# Represents companies or service providers on the platform.
# Inherits from UserMixin for Flask-Login and db.Model for SQLAlchemy.
class Company(UserMixin, db.Model):
    # Defines the table name in the database.
    __tablename__ = 'companies'
    # Primary key: Unique identifier for each company.
    company_id = db.Column(db.Integer, primary_key=True)
    # Company's name: A string up to 100 characters, cannot be null.
    name = db.Column(db.String(100), nullable=False)
    # Company's email: A string up to 120 characters, must be unique. Nullable if some companies
    # might not have a direct login email initially, but typically set.
    email = db.Column(db.String(120), unique=True, nullable=True)
    # Hashed password for company login. Nullable if company accounts are created externally
    # or login is not required for all companies.
    password = db.Column(db.String(128), nullable=True)
    # Company description: A text field for longer descriptions of services.
    description = db.Column(db.Text, nullable=True)
    # URL to the company's main profile photo.
    photo_url = db.Column(db.String(255), nullable=True)
    # Company's average rating (float, defaults to 0.0).
    rating = db.Column(db.Float, default=0.0)
    # Foreign key linking to the Service table, indicating the primary service type.
    service_id = db.Column(db.Integer, db.ForeignKey('services.service_id'), nullable=False)

    # NEW FIELD FOR GALLERY IMAGES
    # Stores comma-separated relative paths to images showcasing the company's work.
    # This allows multiple images to be stored in a single database field.
    gallery_images = db.Column(db.Text, nullable=True)

    # Relationships: Define how Company records relate to other tables.
    # 'service': The specific Service object this company provides.
    #   - 'backref='companies'': Creates a 'companies' attribute on Service, linking back to Companies.
    service = db.relationship('Service', backref='companies', lazy=True)
    # 'saved_by_clients': A list of SavedCompany entries where this company has been saved by clients.
    saved_by_clients = db.relationship('SavedCompany', backref='company', lazy=True)
    # 'ratings': A list of ratings given to this company by clients.
    ratings = db.relationship('Rating', backref='company', lazy=True)
    # 'received_messages': Messages received by this company.
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_company_id', backref='receiver_company', lazy=True)
    # 'sent_messages': Messages sent by this company.
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_company_id', backref='sender_company', lazy=True)

    def set_password(self, password):
        """Hashes the given password and stores it securely."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the given plain password matches the stored hashed password."""
        return check_password_hash(self.password, password)

    # --- CRITICAL CHANGE 3: Return ID with type for Flask-Login ---
    # Similar to Client.get_id(), this method provides a unique ID string for company users
    # to be used by Flask-Login's `user_loader`.
    def get_id(self):
        """
        Returns a unique identifier for the user session, combining company_id and type.
        Example: "5_company"
        """
        return f"{self.company_id}_company"

    # --- CRITICAL CHANGE 4: Helper properties for template logic and authorization ---
    # These properties help distinguish user types in templates and authentication checks.
    @property
    def is_client(self):
        """Returns False if the user is a company (i.e., not a client)."""
        return False

    @property
    def is_company(self):
        """Returns True if the user is a company."""
        return True

    def __repr__(self):
        """Provides a helpful string representation for debugging."""
        return f"<Company {self.name}>"

# --- Service Model ---
# Represents the different types of services available on the platform (e.g., Plumbing, Electrical).
class Service(db.Model):
    # Defines the table name.
    __tablename__ = 'services'
    # Primary key for services.
    service_id = db.Column(db.Integer, primary_key=True)
    # Name of the service: A string up to 100 characters, must be unique, cannot be null.
    service_name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        """Provides a helpful string representation for debugging."""
        return f"<Service {self.service_name}>"

# --- SavedCompany Model ---
# Represents a client's saved list of companies (a many-to-many relationship with extra data).
# This is an "association table" for clients saving companies.
class SavedCompany(db.Model):
    # Defines the table name.
    __tablename__ = 'saved_companies'
    # Primary key for each saved entry.
    saved_id = db.Column(db.Integer, primary_key=True)
    # Foreign key to the Client table, indicating which client saved the company.
    client_id = db.Column(db.Integer, db.ForeignKey('clients.client_id'), nullable=False)
    # Foreign key to the Company table, indicating which company was saved.
    company_id = db.Column(db.Integer, db.ForeignKey('companies.company_id'), nullable=False)
    # Timestamp when the company was saved, defaults to the current UTC time.
    saved_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    def __repr__(self):
        """Provides a helpful string representation for debugging."""
        return f"<SavedCompany {self.saved_id} by Client {self.client_id} for Company {self.company_id}>"

# --- Rating Model ---
# Represents a rating and review given by a client to a company.
class Rating(db.Model):
    # Defines the table name.
    __tablename__ = 'ratings'
    # Primary key for each rating entry.
    rating_id = db.Column(db.Integer, primary_key=True)
    # Foreign key to the Client who gave the rating.
    client_id = db.Column(db.Integer, db.ForeignKey('clients.client_id'), nullable=False)
    # Foreign key to the Company that received the rating.
    company_id = db.Column(db.Integer, db.ForeignKey('companies.company_id'), nullable=False)
    # The numerical rating (e.g., 4.5, 5.0), cannot be null.
    rating = db.Column(db.Float, nullable=False)
    # Optional text review associated with the rating.
    review = db.Column(db.Text, nullable=True)
    # Timestamp when the rating was created, defaults to the current UTC time.
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    def __repr__(self):
        """Provides a helpful string representation for debugging."""
        return f"<Rating {self.rating} by Client {self.client_id} for Company {self.company_id}>"

# --- Message Model ---
# Represents a message exchanged between a client and a company.
# Designed to handle messages sent from client to company OR company to client.
class Message(db.Model):
    # Defines the table name.
    __tablename__ = 'messages'
    # Primary key for each message.
    message_id = db.Column(db.Integer, primary_key=True)
    # Foreign key for the client who sent the message (nullable if sender is a company).
    sender_client_id = db.Column(db.Integer, db.ForeignKey('clients.client_id'), nullable=True)
    # Foreign key for the company who sent the message (nullable if sender is a client).
    sender_company_id = db.Column(db.Integer, db.ForeignKey('companies.company_id'), nullable=True)
    # Foreign key for the client who received the message (nullable if receiver is a company).
    receiver_client_id = db.Column(db.Integer, db.ForeignKey('clients.client_id'), nullable=True)
    # Foreign key for the company who received the message (nullable if receiver is a client).
    receiver_company_id = db.Column(db.Integer, db.ForeignKey('companies.company_id'), nullable=True)

    # Content of the message, cannot be null.
    content = db.Column(db.Text, nullable=False)
    # Timestamp when the message was sent, defaults to the current UTC time.
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    # Boolean flag indicating if the message has been read by the receiver.
    is_read = db.Column(db.Boolean, default=False)

    def __repr__(self):
        """Provides a helpful string representation for debugging."""
        # This representation helps identify sender and receiver roles quickly.
        return f"<Message {self.message_id} from C:{self.sender_client_id}/Co:{self.sender_company_id} to C:{self.receiver_client_id}/Co:{self.receiver_company_id}>"