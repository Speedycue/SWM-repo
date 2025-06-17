# seed.py

# Import necessary components:
# - create_app: Factory function to initialize the Flask application.
# - db: The SQLAlchemy database instance, used for database operations.
from app import create_app, db
# Import all database models (tables) that you want to interact with.
# These models define the structure of your data in the database.
from app.models import Client, Company, Service, SavedCompany, Rating, Message
# Import datetime and timezone for handling timestamps, ensuring they are timezone-aware.
from datetime import datetime, timezone
# Import generate_password_hash from werkzeug.security to securely hash passwords before storing them.
from werkzeug.security import generate_password_hash

# Create the Flask application instance.
# This step initializes your Flask app with its configuration.
app = create_app()

# Use app.app_context() to work with the database.
# Database operations like creating tables or adding data require an active
# Flask application context. This 'with' statement ensures that the context
# is properly set up and torn down.
with app.app_context():
    print("Creating database tables if they don't exist...")
    # Call db.create_all() to create all tables defined by your SQLAlchemy models.
    # This is idempotent, meaning it only creates tables if they don't exist,
    # so it's safe to run multiple times without re-creating existing tables.
    db.create_all() 
    print("Tables created.")

    # Check if there's any data in the 'Service' table to prevent re-seeding on every run.
    # This ensures that you don't duplicate data if the script is executed multiple times
    # without clearing the database first.
    # You could choose another model (e.g., Client.query.count()) based on your preference.
    if Service.query.count() == 0:
        print("Database is empty. Starting to seed data...")

        # --- Services Seeding ---
        print("Adding sample services...")
        # Create instances of the Service model with sample service names.
        service_plumbing = Service(service_name='Plumbing')
        service_electrical = Service(service_name='Electrical Services')
        service_cleaning = Service(service_name='Cleaning Services')
        service_carpentry = Service(service_name='Carpentry')
        service_painting = Service(service_name='Painting')
        
        # Add all created service objects to the current database session.
        db.session.add_all([service_plumbing, service_electrical, service_cleaning, service_carpentry, service_painting])
        # Commit the transaction to save these new services to the database.
        # This is important here because subsequent data (like Companies) will link to these services,
        # and committing ensures their IDs are available.
        db.session.commit() 
        print("Services added.")

        # --- Companies Seeding ---
        print("Adding sample companies...")
        # Create instances of the Company model with various details.
        # Passwords for companies are hashed using 'generate_password_hash' for security.
        # 'gallery_images' are stored as comma-separated strings, which can be parsed later.
        # 'service' field directly links to the Service object created above,
        # establishing the relationship automatically.
        company1 = Company(
            name='Elite Plumbing Solutions',
            email='elite.plumbing@example.com',
            password=generate_password_hash('companypass1'), 
            description='Professional plumbing services for homes and businesses.',
            photo_url='images/plumbing1.jpg',
            gallery_images='images/plumbing_work_a.jpg,images/plumbing_work_b.jpg',
            rating=4.8,
            service=service_plumbing # Link to the 'Plumbing' service
        )
        company2 = Company(
            name='Sparky Electricians',
            email='sparky.electricians@example.com',
            password=generate_password_hash('companypass2'),
            description='Certified electricians for all your wiring and repair needs.',
            photo_url='images/electrical1.jpg',
            gallery_images='images/electrical_work_a.jpg,images/electrical_work_b.jpg',
            rating=4.5,
            service=service_electrical # Link to the 'Electrical Services' service
        )
        company3 = Company(
            name='Spotless Cleaning Co.',
            email='spotless.clean@example.com',
            password=generate_password_hash('companypass3'),
            description='Eco-friendly and thorough cleaning services.',
            photo_url='images/cleaning1.jpg',
            gallery_images='images/cleaning_work_a.jpg, images/cleaning_work_b.jpg',
            rating=4.9,
            service=service_cleaning # Link to the 'Cleaning Services' service
        )
        company4 = Company(
            name='WoodCraft Master',
            email='woodcraft.master@example.com',
            password=generate_password_hash('companypass4'),
            description='Custom furniture and carpentry work.',
            photo_url='images/carpentry1.jpg',
            gallery_images='images/carpentry_work_a.jpg,images/carpentry_work_b.jpg, images/carpentry_work_c.jpg',
            rating=4.7,
            service=service_carpentry # Link to the 'Carpentry' service
        )
        company5 = Company(
            name='Bright Walls Painters',
            email='bright.walls@example.com',
            password=generate_password_hash('companypass5'),
            description='Transforming spaces with a fresh coat of paint.',
            photo_url='images/painting1.jpg',
            gallery_images='images/painting_work_a.jpg,images/painting_work_b.jpg',
            rating=4.6,
            service=service_painting # Link to the 'Painting' service
        )
        company6 = Company(
            name='QuickFix Plumbing',
            email='quickfix.plumbing@example.com',
            password=generate_password_hash('companypass6'),
            description='Emergency plumbing services, fast and reliable.',
            photo_url='images/plumbing2.jpg',
            gallery_images='images/plumbing2_work_a.jpg, images/plumbing2_work_b.jpg',
            rating=4.2,
            service=service_plumbing # Link to the 'Plumbing' service
        )
        company7 = Company(
            name='PowerUp Electrical',
            email='powerup.electrical@example.com',
            password=generate_password_hash('companypass7'),
            description='Residential and commercial electrical installations.',
            photo_url='images/electrical2.jpg',
            gallery_images='images/electrical2_work_a.jpg',
            rating=4.3,
            service=service_electrical # Link to the 'Electrical Services' service
        )
        company8 = Company(
            name='Shine & Sparkle Cleaners',
            email='shine.sparkle@example.com',
            password=generate_password_hash('companypass8'),
            description='Deep cleaning and specialized cleaning services.',
            photo_url='images/cleaning2.jpg',
            gallery_images='images/cleaning2_work_a.jpg',
            rating=4.7,
            service=service_cleaning # Link to the 'Cleaning Services' service
        )

        # Add all created company objects to the session and commit to save them.
        db.session.add_all([company1, company2, company3, company4, company5, company6, company7, company8])
        db.session.commit()
        print("Companies added.")

        # --- Clients Seeding ---
        print("Adding sample clients...")
        # Create instances of the Client model.
        client1 = Client(name='Ali Al-Harthy', email='ali@example.com')
        # Use the 'set_password' method (defined in your Client model) to hash and store passwords.
        client1.set_password('password123') 
        
        client2 = Client(name='Fatima Al-Busaidi', email='fatima@example.com')
        client2.set_password('securepass')

        client3 = Client(name='Test User', email='test@example.com')
        client3.set_password('testpass')

        # Add all created client objects and commit.
        db.session.add_all([client1, client2, client3])
        db.session.commit()
        print("Clients added.")

        # --- Saved Companies Seeding ---
        print("Adding sample saved companies...")
        # Create instances of the SavedCompany model, linking clients to companies they've saved.
        # 'saved_at' timestamp is set to the current UTC time.
        saved1 = SavedCompany(client=client1, company=company3, saved_at=datetime.now(timezone.utc))
        saved2 = SavedCompany(client=client1, company=company2, saved_at=datetime.now(timezone.utc))
        saved3 = SavedCompany(client=client2, company=company1, saved_at=datetime.now(timezone.utc))
        
        # Add all and commit.
        db.session.add_all([saved1, saved2, saved3])
        db.session.commit()
        print("Saved companies added.")

        # --- Ratings Seeding ---
        print("Adding sample ratings...")
        # Create instances of the Rating model, linking clients to companies with a rating and review.
        # 'created_at' timestamp is set to the current UTC time.
        rating1 = Rating(client=client1, company=company3, rating=5.0, review="Excellent cleaning service!", created_at=datetime.now(timezone.utc))
        rating2 = Rating(client=client2, company=company1, rating=4.0, review="Good, but a bit pricey.", created_at=datetime.now(timezone.utc))
        rating3 = Rating(client=client1, company=company2, rating=4.5, review="Very professional electricians.", created_at=datetime.now(timezone.utc))
        rating4 = Rating(client=client3, company=company4, rating=4.9, review="Amazing custom shelves, highly recommend!", created_at=datetime.now(timezone.utc))
        rating5 = Rating(client=client2, company=company5, rating=4.6, review="Bright Walls did a fantastic job painting our living room.", created_at=datetime.now(timezone.utc))
        
        # Add all and commit.
        db.session.add_all([rating1, rating2, rating3, rating4, rating5])
        db.session.commit()
        print("Ratings added.")

        # --- Messages Seeding (Optional) ---
        print("Adding sample messages...")
        # Create instances of the Message model for testing communication.
        # Messages can be from a client to a company or vice-versa.
        message1 = Message(
            sender_client_id=client1.client_id, # Sender is client1
            receiver_company_id=company1.company_id, # Receiver is company1
            content="Hi, I need a plumber urgently for a leak.",
            timestamp=datetime.now(timezone.utc)
        )
        message2 = Message(
            sender_company_id=company1.company_id, # Sender is company1
            receiver_client_id=client1.client_id, # Receiver is client1
            content="We can send someone in 2 hours. What's your address?",
            timestamp=datetime.now(timezone.utc)
        )
        message3 = Message(
            sender_client_id=client2.client_id,
            receiver_company_id=company2.company_id,
            content="Can you give me an estimate for outlet installation?",
            timestamp=datetime.now(timezone.utc)
        )
        message4 = Message(
            sender_company_id=company2.company_id,
            receiver_client_id=client2.client_id,
            content="Certainly, please describe the location and any specific requirements.",
            timestamp=datetime.now(timezone.utc)
        )
        
        # Add all and commit.
        db.session.add_all([message1, message2, message3, message4])
        db.session.commit()
        print("Messages added.")

    else:
        # If Service.query.count() was not 0, print that seeding is skipped.
        print("Database already contains data. Skipping seeding.")

    print("Seeding process complete!")