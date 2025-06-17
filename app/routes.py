# app/routes.py

# Import uuid for generating unique identifiers, though not explicitly used in the provided snippet,
# it's often useful in web applications for creating unique file names or IDs.
import uuid 
# Import core Flask functionalities:
# - Blueprint: Organizes a set of routes, templates, and static files into a reusable component.
# - render_template: Renders Jinja2 templates (HTML files).
# - request: Object containing incoming request data (form data, query parameters, etc.).
# - jsonify: Converts Python dictionaries to JSON responses.
# - redirect: Redirects the user to a different URL.
# - url_for: Generates URLs for specific functions, handling dynamic parts.
# - flash: Sends a one-time message to the next request (e.g., for success/error notifications).
# - current_app: Proxy to the current application instance, useful for accessing app configuration.
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
# Import all database models from app.models, which define your database schema.
from app.models import Client, Company, Service, SavedCompany, Rating, Message
# Import the database instance (db) and login manager (login_manager) from the main app package.
# These objects are initialized in app/__init__.py and used here to interact with the database
# and manage user sessions.
from app import db, login_manager 
# Import joinedload from SQLAlchemy ORM for eager loading of related data,
# which can improve query performance by fetching related objects in one go.
from sqlalchemy.orm import joinedload
# Import or_ for OR conditions in SQLAlchemy queries (e.g., searching multiple fields)
# and func for calling SQL functions like AVG().
from sqlalchemy import or_, func 

# Flask-Login specific imports:
# - login_user: Logs a user into the session.
# - logout_user: Logs a user out of the session.
# - login_required: Decorator to restrict access to authenticated users.
# - current_user: Proxy to the currently logged-in user object.
from flask_login import login_user, logout_user, login_required, current_user

# Datetime utilities:
# - datetime: For working with dates and times.
# - timezone: For creating timezone-aware datetime objects (important for consistency).
from datetime import datetime, timezone 

# Password hashing utilities from Werkzeug:
# - generate_password_hash: Hashes a plaintext password for storage.
# - check_password_hash: Verifies a plaintext password against a hash.
from werkzeug.security import generate_password_hash, check_password_hash

# File upload utilities:
# - os: For interacting with the operating system, particularly file paths.
# - secure_filename: Secures a filename for use in file storage to prevent path traversal vulnerabilities.
import os
from werkzeug.utils import secure_filename

# Create a Blueprint instance.
# Blueprints help organize your Flask application into modular components.
# 'main' is the name of this blueprint, and '__name__' is used to locate resources
# relative to this blueprint (e.g., templates).
bp = Blueprint('main', __name__)

# --- NOTE: login_manager.user_loader is now in app/__init__.py to prevent circular imports ---
# This comment serves as a reminder that the user loading logic for Flask-Login
# has been moved to __init__.py to resolve potential circular import issues
# that can arise when models, database, and login manager are all intertwined.

# Helper function for file uploads
def allowed_file(filename):
    """
    Checks if the provided filename has an allowed extension for file uploads.
    The allowed extensions are configured in `current_app.config['ALLOWED_EXTENSIONS']`.

    Args:
        filename (str): The name of the file to check.

    Returns:
        bool: True if the file extension is allowed, False otherwise.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_uploaded_file(file):
    """
    Saves an uploaded file to the designated upload folder and returns its
    relative path, suitable for database storage and `url_for('static', ...)` in templates.
    It generates a unique filename to prevent collisions and secures the original filename.

    Args:
        file (werkzeug.datastructures.FileStorage): The uploaded file object from `request.files`.

    Returns:
        str or None: The relative path to the saved file (e.g., 'uploads/companies/unique_name.jpg')
                     or None if the file is not valid or not allowed.
    """
    if file and allowed_file(file.filename):
        # Secure the original filename to prevent directory traversal attacks.
        filename = secure_filename(file.filename)
        # Generate a unique filename using UUID to avoid name collisions,
        # prepending it to the secured original filename.
        unique_filename = str(uuid.uuid4()) + '_' + filename
        # Construct the absolute path where the file will be saved on the server.
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        # Save the uploaded file to the constructed path.
        file.save(filepath)
        # Return the path relative to the 'static/' folder.
        # .replace(os.sep, '/') ensures consistent path separators across OS.
        return os.path.join('uploads', 'companies', unique_filename).replace(os.sep, '/')
    return None

# Helper to delete a file from the filesystem
def delete_file_from_filesystem(filepath_relative_to_static):
    """
    Deletes a file from the server's filesystem given its path relative to the static folder.
    This is important for cleaning up old profile photos or gallery images when they are updated or removed.

    Args:
        filepath_relative_to_static (str): The path of the file relative to the 'static/' folder
                                           (e.g., 'uploads/companies/image.jpg').

    Returns:
        bool: True if the file was successfully deleted, False otherwise (e.g., file not found, error).
    """
    if filepath_relative_to_static:
        # Construct the absolute path to the file on the server.
        abs_filepath = os.path.join(current_app.root_path, 'static', filepath_relative_to_static)
        # Check if the file actually exists before attempting to delete it.
        if os.path.exists(abs_filepath):
            try:
                # Remove the file from the filesystem.
                os.remove(abs_filepath)
                # Log the successful deletion for debugging/monitoring.
                current_app.logger.info(f"Deleted file: {abs_filepath}") 
                return True
            except Exception as e:
                # Log any errors that occur during file deletion.
                current_app.logger.error(f"Error deleting file {abs_filepath}: {e}")
                return False
    return False

# --- Frontend Routes (Now with Flask-Login Integration for two user types) ---

@bp.route('/')
def index():
    """
    Renders the homepage of the application.
    It fetches and displays dynamic categories (services) and a list of
    recommended companies (currently based on rating).
    """
    # Query all available services, ordered alphabetically by name.
    categories = Service.query.order_by(Service.service_name).all()
    
    # Fetch recommended companies. Here, it retrieves the top 6 companies
    # ordered by their rating in descending order. Companies with no rating
    # (or null rating) are placed last.
    recommended_companies = Company.query.order_by(Company.rating.desc().nulls_last()).limit(6).all()
    
    # Render the 'index.html' template, passing the fetched categories and
    # recommended companies as context variables.
    return render_template(
        'index.html',
        categories=categories,
        recommended_companies=recommended_companies
    )

@bp.route('/listings')
def listings():
    """
    Renders the companies listings page. This page allows users to browse
    companies, apply search queries, and filter by service type. It also
    implements pagination for managing large sets of results.
    """
    # Get the search query from the URL's query parameters (e.g., ?q=plumber).
    # .strip() removes leading/trailing whitespace.
    query = request.args.get('q', '').strip()
    # Get the service ID for filtering from the URL (e.g., ?service_id=1).
    # type=int automatically converts the parameter to an integer.
    service_id = request.args.get('service_id', type=int)
    # Get the current page number for pagination, defaulting to 1.
    page = request.args.get('page', 1, type=int)
    # Define the number of companies to display per page.
    per_page = 9 

    # Start building the query for companies.
    # .options(joinedload(Company.service)) is used for eager loading:
    # it fetches the associated 'Service' object for each Company in the same
    # database query, preventing N+1 query problems in the template.
    company_query = Company.query.options(joinedload(Company.service)) 

    # Apply search filter if a search query is provided.
    if query:
        company_query = company_query.filter(
            # Use 'or_' to search for the query string in either the company's name
            # or its description (case-insensitive with .ilike()).
            or_(
                Company.name.ilike(f"%{query}%"),
                Company.description.ilike(f"%{query}%")
            )
            # Note: For searching across related tables (like Service names),
            # a more complex query or a dedicated search API endpoint would be needed.
            # The /api/search route typically handles cross-model searches.
        )
    
    # Apply service ID filter if a service_id is provided.
    if service_id:
        company_query = company_query.filter_by(service_id=service_id)

    # Order the companies: first by rating (descending, nulls last), then alphabetically by name.
    company_query = company_query.order_by(Company.rating.desc().nulls_last(), Company.name.asc())

    # Paginate the results:
    # - page: Current page number.
    # - per_page: Items per page.
    # - error_out=False: If an invalid page number is requested, it won't raise an error
    #   but will instead return an empty page or the last valid page.
    pagination = company_query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Extract the list of Company objects for the current page.
    companies = pagination.items 
    
    # Fetch all services to populate the filter dropdown menu on the page.
    all_services = Service.query.order_by(Service.service_name).all()

    # Render the 'listings.html' template, passing all necessary data for display,
    # filters, and pagination controls.
    return render_template(
        'listings.html',
        companies=companies, # Companies for the current page.
        pagination=pagination, # The pagination object (contains page numbers, next/prev links).
        query=query, # The current search query (to pre-fill the search box).
        service_id=service_id, # The currently selected service ID (to keep dropdown selected).
        services=all_services, # All services for the filter dropdown options.
        selected_service_id=service_id # Used to mark the active service in the dropdown.
    )

@bp.route('/company/<int:company_id>') 
def company_profile(company_id):
    """
    Renders a single company's detailed profile page.
    It fetches company details, associated ratings and clients, and determines
    if the current user can edit the profile or has saved this company.

    Args:
        company_id (int): The ID of the company whose profile is to be displayed.
    """
    # Query the Company by its ID. .get_or_404() automatically returns a 404 error
    # if the company is not found.
    # Eager load related data to optimize database queries:
    # - Company.service: Loads the associated service in the same query.
    # - Company.ratings: Loads all ratings for this company.
    # - Rating.client: For each rating, also loads the client who made the rating.
    company = Company.query.options(
        joinedload(Company.service), 
        joinedload(Company.ratings).joinedload(Rating.client) 
    ).get_or_404(company_id)

    # Prepare a list of image URLs for the company's gallery.
    # The main photo_url is added first.
    company_photos = []
    if company.photo_url:
        company_photos.append(company.photo_url)
    # If gallery_images exist (comma-separated string), split them and add to the list.
    if company.gallery_images:
        # Split the comma-separated string, strip whitespace, and filter out any empty strings.
        gallery_paths = [path.strip() for path in company.gallery_images.split(',') if path.strip()]
        company_photos.extend(gallery_paths) # Add gallery paths to the list

    # Determine if the currently logged-in user is authorized to edit this company's profile.
    can_edit = False
    # Check if a user is authenticated, if they are a 'company' type,
    # and if their company_id matches the profile's company_id.
    if current_user.is_authenticated and current_user.is_company and current_user.company_id == company_id:
        can_edit = True

    # Determine if the currently logged-in client has saved this company.
    is_saved = False
    # This check is only relevant if a user is authenticated AND is a 'client' type.
    if current_user.is_authenticated and current_user.is_client:
        # Query the SavedCompany table to find an entry where the client_id matches
        # the current client's ID and the company_id matches the profile's company_id.
        saved_entry = SavedCompany.query.filter_by(
            client_id=current_user.client_id,
            company_id=company_id
        ).first()
        # If such an entry is found, the company is considered "saved".
        if saved_entry:
            is_saved = True

    # Render the 'company_profile.html' template, passing all collected data.
    return render_template(
        'company_profile.html',
        company=company, # The Company object with all its details.
        company_photos=company_photos, # List of all photo URLs for the gallery.
        can_edit=can_edit, # Boolean indicating if the current user can edit.
        is_saved=is_saved # Boolean indicating if the current client has saved this company.
    )

# --- Your edit_company_profile route (modified to use helpers) ---
@bp.route('/company/<int:company_id>/edit', methods=['GET', 'POST'])
@login_required # Decorator: Ensures only authenticated users can access this route.
def edit_company_profile(company_id):
    """
    Handles the editing of a company's profile.
    - GET request: Renders the edit form, pre-populating it with existing data.
    - POST request: Processes form submissions, validates data, handles file uploads/deletions,
                    updates company information, and securely changes passwords.
    Only the company owner can edit their profile.
    """
    # Fetch the company by ID, or return 404 if not found.
    company = Company.query.get_or_404(company_id)

    # Authorization Check:
    # Ensure that the currently logged-in user is a company AND their company_id
    # matches the company_id of the profile being edited.
    if not current_user.is_company or current_user.company_id != company.company_id:
        # If unauthorized, flash an error message and redirect.
        flash("You are not authorized to edit this company profile.", "danger")
        if current_user.is_authenticated:
            # Redirect based on the authenticated user's type.
            if current_user.is_client:
                return redirect(url_for('main.client_profile', client_id=current_user.client_id))
            elif current_user.is_company:
                return redirect(url_for('main.company_profile', company_id=current_user.company_id))
        else:
            # If not authenticated at all (shouldn't happen with @login_required, but as fallback).
            return redirect(url_for('main.index'))

    # Fetch all services to populate the service type dropdown in the edit form.
    services = Service.query.all()

    if request.method == 'POST':
        # Retrieve form data from the POST request.
        name = request.form.get('name')
        email = request.form.get('email')
        description = request.form.get('description')
        service_id = request.form.get('service_id')

        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')

        # --- File Uploads (Existing Logic for new uploads) ---
        # Get the main profile photo file from the request.
        photo_url_file = request.files.get('photo_url_file')
        # Get a list of all files uploaded for the gallery.
        gallery_files = request.files.getlist('gallery_files')

        # --- Photo Deletion (NEW Logic for existing photos) ---
        # Check if the 'remove main photo' checkbox was ticked.
        remove_main_photo = request.form.get('remove_main_photo') 
        # Get a list of paths for gallery images marked for deletion.
        delete_gallery_images = request.form.getlist('delete_gallery_image') 

        # 1. Validate Current Password:
        # This is a critical security step: require the user to re-enter their current
        # password before allowing any profile updates.
        if not current_password or not company.check_password(current_password):
            flash('Incorrect current password. All changes require current password confirmation.', 'danger')
            return redirect(url_for('main.edit_company_profile', company_id=company.company_id))

        # 2. Update Basic Fields (Name, Email, Description, Service ID) if they have changed.
        if name and name != company.name:
            company.name = name

        if email and email != company.email:
            # Check for email uniqueness among other companies.
            if Company.query.filter(Company.email == email, Company.company_id != company_id).first():
                flash('Email already registered by another company.', 'danger')
                return redirect(url_for('main.edit_company_profile', company_id=company.company_id))
            company.email = email

        if description and description != company.description:
            company.description = description

        if service_id and int(service_id) != company.service_id:
            try:
                company.service_id = int(service_id)
            except ValueError:
                flash('Invalid service selected.', 'danger')
                return redirect(url_for('main.edit_company_profile', company_id=company.company_id))

        # 3. Update Password:
        # Only proceed if a new password was provided.
        if new_password:
            # Validate new password length.
            if len(new_password) < 6:
                flash('New password must be at least 6 characters long.', 'danger')
                return redirect(url_for('main.edit_company_profile', company_id=company.company_id))
            # Check if new password and confirmation match.
            if new_password != confirm_new_password:
                flash('New passwords do not match.', 'danger')
                return redirect(url_for('main.edit_company_profile', company_id=company.company_id))
            # Set the new password (this hashes it internally using the model's method).
            company.set_password(new_password)

        # 4. Handle Main Company Photo (photo_url):
        # This logic prioritizes a new upload, then checks for a 'remove' request,
        # otherwise keeps the existing photo.
        if photo_url_file and photo_url_file.filename != '': 
            # If a new photo is uploaded, delete the old one first to avoid orphaned files.
            if company.photo_url:
                delete_file_from_filesystem(company.photo_url)
            # Save the new uploaded file.
            saved_path = save_uploaded_file(photo_url_file)
            if saved_path:
                company.photo_url = saved_path # Update database field with new path.
            else:
                flash('Invalid main photo file type. Allowed types: png, jpg, jpeg, gif', 'danger')
                return redirect(url_for('main.edit_company_profile', company_id=company.company_id))
        elif remove_main_photo == '1': # If 'remove' checkbox is checked AND no new file was uploaded.
            if company.photo_url:
                delete_file_from_filesystem(company.photo_url) # Delete the existing file.
                company.photo_url = None # Set the database field to None.
            else:
                flash('No main photo to remove.', 'info') # Inform the user if nothing was there.

        # 5. Handle Gallery Images (gallery_images):
        # This involves two steps: first process deletions of existing images,
        # then process uploads of new images.
        
        # Get the current list of gallery image paths from the database, split by comma.
        # Filter out any empty strings that might result from splitting.
        current_gallery_paths = company.gallery_images.split(',') if company.gallery_images else []
        current_gallery_paths = [p.strip() for p in current_gallery_paths if p.strip()] 

        # Process deletions:
        if delete_gallery_images: # This list contains paths of images to be deleted.
            images_to_keep = []
            for path in current_gallery_paths:
                if path in delete_gallery_images: # If the current image's path is in the deletion list.
                    delete_file_from_filesystem(path) # Delete it from the server.
                else:
                    images_to_keep.append(path) # Otherwise, keep it.
            current_gallery_paths = images_to_keep # Update the list of paths to only include kept images.

        # Process new uploads:
        new_gallery_paths = []
        for file in gallery_files: # Iterate through each file in the gallery upload.
            if file and file.filename != '': # If a file was actually uploaded.
                saved_path = save_uploaded_file(file) # Save the new file.
                if saved_path:
                    new_gallery_paths.append(saved_path) # Add its path to the list of new paths.
                else:
                    flash(f'Invalid gallery file type for {file.filename}. Allowed types: png, jpg, jpeg, gif', 'danger')
                    return redirect(url_for('main.edit_company_profile', company_id=company.company_id))

        # Combine the images that were kept and the newly uploaded images.
        updated_gallery = current_gallery_paths + new_gallery_paths
        # Update the database field: join the paths back into a comma-separated string.
        # If no images are left, set it to None.
        company.gallery_images = ','.join(updated_gallery) if updated_gallery else None 

        # --- Commit Changes to Database ---
        try:
            db.session.commit() # Commit all changes (profile updates, password, photo URLs) to the database.
            flash('Profile updated successfully!', 'success') # Success message.
            # Redirect to the updated company profile page.
            return redirect(url_for('main.company_profile', company_id=company.company_id))
        except Exception as e:
            # If any error occurs during commit, rollback the session to undo changes
            # and prevent partial updates.
            db.session.rollback()
            # Log the error for server-side debugging.
            current_app.logger.error(f"Error updating company profile: {e}") 
            # Flash an error message to the user.
            flash(f'An error occurred while updating profile: {str(e)}', 'danger')
            # Redirect back to the edit page to allow re-submission.
            return redirect(url_for('main.edit_company_profile', company_id=company.company_id))

    # For GET requests or if POST fails validation and redirects back, render the edit form.
    return render_template('edit_company_profile.html', company=company, services=services)


@bp.route('/client/<int:client_id>')
@login_required # This decorator ensures that only logged-in users can access this route.
def client_profile(client_id):
    """
    Renders a client's dashboard/profile page.
    This page displays information specific to the client, such as their saved companies.
    A crucial security measure is implemented: a logged-in user can only view their own profile.

    Args:
        client_id (int): The ID of the client whose profile is being requested.
    """
    # Security check:
    # 1. Ensure the currently logged-in user's type (determined by __tablename__) is 'clients'.
    # 2. Ensure the logged-in client's ID matches the client_id requested in the URL.
    if current_user.__tablename__ != 'clients' or current_user.client_id != client_id:
        flash("You are not authorized to view this client profile.", "danger")
        # Redirect unauthorized users:
        # If authenticated, redirect to their own profile (client or company).
        # If not authenticated (shouldn't happen with @login_required, but as a fallback), redirect to index.
        if current_user.is_authenticated:
            if current_user.__tablename__ == 'clients':
                return redirect(url_for('main.client_profile', client_id=current_user.client_id))
            elif current_user.__tablename__ == 'companies':
                return redirect(url_for('main.company_profile', company_id=current_user.company_id))
        else:
            return redirect(url_for('main.index'))

    # Eager load related data for the client's profile page to avoid N+1 queries.
    # It loads the Client object by ID, and for that client, it loads their
    # 'saved_companies' relationships, and for each SavedCompany, it also loads
    # the associated 'company' details.
    client = Client.query.options(
        joinedload(Client.saved_companies).joinedload(SavedCompany.company), # Saved companies and their details
    ).get_or_404(client_id) # Fetches the client or returns a 404 error if not found.

    # Render the 'client_profile.html' template, passing the fetched client object.
    return render_template('client_profile.html', client=client)



# --- New Login Choice Page ---
@bp.route('/login_choice')
def login_choice():
    """
    Renders a page where the user can choose whether to log in/register as a Client or a Company.
    If a user is already authenticated, they are redirected to their respective profile page,
    preventing them from seeing this choice page when already logged in.
    """
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        # Redirect based on the user's type.
        if current_user.__tablename__ == 'clients':
            return redirect(url_for('main.client_profile', client_id=current_user.client_id))
        elif current_user.__tablename__ == 'companies':
            return redirect(url_for('main.company_profile', company_id=current_user.company_id))
    # If not authenticated, render the login choice page.
    return render_template('login_choice.html') # This new template needs to be created



# --- Client Login/Registration Routes (from old /login) ---
@bp.route('/client_login')
def client_login():
    """
    Renders the client login and registration page.
    Similar to `login_choice`, it redirects already authenticated users away.
    """
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        if current_user.__tablename__ == 'clients':
            return redirect(url_for('main.client_profile', client_id=current_user.client_id))
        elif current_user.__tablename__ == 'companies':
            return redirect(url_for('main.company_profile', company_id=current_user.company_id))
    # If not authenticated, display the client login/registration form.
    return render_template('login.html') # Still using the original login.html for clients

@bp.route('/handle_login', methods=['POST'])
def handle_login():
    """
    Handles the submission of the client login form.
    It verifies credentials and uses Flask-Login to log the user into the session.
    """
    # Retrieve email, password, and 'remember me' status from the submitted form.
    email = request.form.get('email')
    password = request.form.get('password')
    remember_me = bool(request.form.get('remember_me')) # Convert checkbox value to boolean

    # Query the database for a client with the provided email.
    client = Client.query.filter_by(email=email).first()

    # Verify password using the `check_password` method defined in the Client model.
    if client and client.check_password(password):
        # If credentials are valid, log the client in using Flask-Login's `login_user` function.
        # `remember=remember_me` persists the session across browser restarts if checked.
        login_user(client, remember=remember_me)
        flash(f'Login successful! Welcome, {client.name}.', 'success')
        
        # Redirect logic:
        # If there's a 'next' URL parameter (often set by @login_required when access was denied),
        # redirect to that URL. Otherwise, redirect to the client's profile page.
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.client_profile', client_id=client.client_id))
    else:
        # If login fails, flash an error message and redirect back to the client login page.
        flash('Invalid email or password.', 'danger')
        return redirect(url_for('main.client_login')) 

@bp.route('/handle_register', methods=['POST'])
def handle_register():
    """
    Handles the submission of the client registration form.
    It validates input, hashes the password, and adds the new client to the database.
    """
    # Retrieve registration form data.
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    # Basic validation: Check if all required fields are filled.
    if not all([name, email, password, confirm_password]):
        flash('Please fill in all fields.', 'danger')
        return redirect(url_for('main.client_login'))

    # Validate if passwords match.
    if password != confirm_password:
        flash('Passwords do not match.', 'danger')
        return redirect(url_for('main.client_login'))

    # Check if the email is already registered by another client.
    if Client.query.filter_by(email=email).first():
        flash('Email already registered. Please use a different email.', 'danger')
        return redirect(url_for('main.client_login'))

    # Hash the password before storing it in the database for security.
    hashed_password = generate_password_hash(password)
    # Create a new Client object.
    new_client = Client(name=name, email=email, password=hashed_password)

    try:
        # Add the new client to the database session and commit.
        db.session.add(new_client)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        # Redirect to the client login page after successful registration.
        return redirect(url_for('main.client_login'))
    except Exception as e:
        # If an error occurs (e.g., database error), rollback the session
        # and flash an error message.
        db.session.rollback()
        flash(f'An error occurred during registration: {str(e)}', 'danger')
        return redirect(url_for('main.client_login'))



# --- Company Login/Registration Routes ---
@bp.route('/company_login')
def company_login():
    """
    Renders the company login and registration page.
    Redirects authenticated users. Also fetches services to populate a dropdown
    for company registration (e.g., specifying the company's service type).
    """
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        if current_user.__tablename__ == 'clients':
            return redirect(url_for('main.client_profile', client_id=current_user.client_id))
        elif current_user.__tablename__ == 'companies':
            return redirect(url_for('main.company_profile', company_id=current_user.company_id))
    
    # Fetch all services, ordered alphabetically, for the registration form's dropdown.
    services = Service.query.order_by(Service.service_name).all()
    # Render the new 'company_login.html' template, passing the services.
    return render_template('company_login.html', services=services) 

@bp.route('/handle_company_login', methods=['POST'])
def handle_company_login():
    """
    Handles the submission of the company login form, similar to client login.
    """
    email = request.form.get('email')
    password = request.form.get('password')
    remember_me = bool(request.form.get('remember_me')) 

    # Query for a company with the given email.
    company = Company.query.filter_by(email=email).first()

    # Verify credentials.
    if company and company.check_password(password):
        # Log in the company user.
        login_user(company, remember=remember_me)
        flash(f'Login successful! Welcome, {company.name}.', 'success')
        
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.company_profile', company_id=company.company_id))
    else:
        flash('Invalid email or password for company.', 'danger')
        return redirect(url_for('main.company_login'))

@bp.route('/handle_company_register', methods=['POST'])
def handle_company_register():
    """
    Handles the submission of the company registration form.
    It includes new fields specific to companies like description and service_id.
    """
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    description = request.form.get('description') # New field for company
    service_id = request.form.get('service_id', type=int) # New field for company service

    # Basic validation for all required fields. `description` can be an empty string,
    # so `is not None` is used.
    if not all([name, email, password, confirm_password, description is not None, service_id is not None]): 
        flash('Please fill in all company registration fields.', 'danger')
        return redirect(url_for('main.company_login'))

    # Password match validation.
    if password != confirm_password:
        flash('Passwords do not match.', 'danger')
        return redirect(url_for('main.company_login'))

    # Check for unique company email.
    if Company.query.filter_by(email=email).first():
        flash('Company email already registered. Please use a different email.', 'danger')
        return redirect(url_for('main.company_login'))
            
    # Validate if the selected service_id is valid (exists in the Service table).
    if not Service.query.get(service_id):
        flash('Invalid service selected.', 'danger')
        return redirect(url_for('main.company_login'))

    # Hash the password.
    hashed_password = generate_password_hash(password)
    # Create a new Company object with all its specific details.
    new_company = Company(
        name=name,
        email=email,
        password=hashed_password,
        description=description,
        service_id=service_id,
        photo_url='/static/images/default_company.png' # Provide a default profile picture for new companies
    )

    try:
        # Add and commit the new company to the database.
        db.session.add(new_company)
        db.session.commit()
        flash('Company registration successful! You can now log in.', 'success')
        # Redirect to the company login page.
        return redirect(url_for('main.company_login'))
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred during registration: {str(e)}', 'danger')
        return redirect(url_for('main.company_login'))



@bp.route('/logout')
@login_required # User must be logged in to log out.
def logout():
    """
    Logs out the current user (whether a client or a company) from the session
    using Flask-Login's `logout_user()` function.
    """
    logout_user() # This clears the user's session.
    flash('You have been logged out.', 'info') # Inform the user.
    return redirect(url_for('main.index')) # Redirect to the homepage after logout.



@bp.route('/about')
def about():
    """
    Renders the static About Us page.
    """
    return render_template('about.html')


@bp.route('/client/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required # This route requires the user to be logged in to access.
def edit_client_profile(client_id):
    """
    Allows a logged-in client to edit their own profile.
    It handles both displaying the edit form (GET request) and processing
    the submitted updates (POST request), including password changes and
    profile picture uploads.
    """
    # Authorization check:
    # Ensures that the current user is a client and that they are trying to edit their own profile.
    if not current_user.is_client or current_user.client_id != client_id:
        flash("You are not authorized to edit this client profile.", "danger")
        # Redirect unauthorized attempts, similar to the client_profile route.
        if current_user.is_authenticated:
            if current_user.is_client:
                return redirect(url_for('main.client_profile', client_id=current_user.client_id))
            elif current_user.is_company:
                return redirect(url_for('main.company_profile', company_id=current_user.company_id))
        else:
            return redirect(url_for('main.index'))
    
    # Fetch the client object to pre-populate the form for GET requests
    # and to update for POST requests.
    client = Client.query.get_or_404(client_id)

    if request.method == 'POST':
        # Retrieve data from the submitted form.
        name = request.form.get('name')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')
        profile_picture = request.files.get('profile_picture') # Get the uploaded file object.

        # Update name if provided.
        if name:
            client.name = name

        # Update email with a uniqueness check.
        if email and email != client.email:
            # Check if the new email is already used by another client.
            if Client.query.filter_by(email=email).first():
                flash('Email already registered by another client.', 'danger')
                return redirect(url_for('main.edit_client_profile', client_id=client.client_id))
            client.email = email
        elif not email: 
            # If the email field is left empty in the form, assume the user intends
            # to keep the existing email and do nothing.
            pass 
        
        # Handle password update:
        # Only proceed if a new password is provided.
        if new_password:
            # Crucial: Verify the `current_password` before allowing a password change.
            if not current_password or not client.check_password(current_password):
                flash('Incorrect current password.', 'danger')
                return redirect(url_for('main.edit_client_profile', client_id=client.client_id))
            
            # Check if new passwords match.
            if new_password != confirm_new_password:
                flash('New passwords do not match.', 'danger')
                return redirect(url_for('main.edit_client_profile', client_id=client.client_id))
            
            # Set the new password using the model's method, which handles hashing.
            client.set_password(new_password) 
        
        # Handle profile picture upload:
        if profile_picture and profile_picture.filename != '':
            # Define the upload directory for client profile pictures.
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'clients')
            # Create the directory if it doesn't exist.
            os.makedirs(upload_folder, exist_ok=True)
            
            # Secure the filename before saving to prevent security issues.
            filename = secure_filename(profile_picture.filename)
            # Construct the full path where the file will be saved.
            filepath = os.path.join(upload_folder, filename)
            
            # Save the new profile picture.
            profile_picture.save(filepath)
            
            # Update the client's `profile_picture_url` in the database.
            # `url_for('static', ...)` generates the correct URL for accessing the image.
            client.profile_picture_url = url_for('static', filename=f'uploads/clients/{filename}')
        
        try:
            # Commit all changes to the database.
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            # Redirect to the updated client profile page.
            return redirect(url_for('main.client_profile', client_id=client.client_id))
        except Exception as e:
            # On error, rollback database changes and flash an error message.
            db.session.rollback()
            flash(f'An error occurred while updating profile: {str(e)}', 'danger')
            return redirect(url_for('main.edit_client_profile', client_id=client.client_id))

    # For GET requests, render the edit profile template, pre-populating it with current client data.
    return render_template('edit_profile.html', client=client)


@bp.route('/toggle_saved_company/<int:company_id>', methods=['POST'])
@login_required # This action requires a logged-in user.
def toggle_saved_company(company_id):
    """
    Allows a client to save or un-save a company.
    This route handles the logic of adding or removing a company from a client's
    saved list in the `SavedCompany` database table.
    """
    # Authorization check: Only clients are allowed to save/un-save companies.
    if not current_user.is_client:
        flash('Only clients can save/un-save companies.', 'danger')
        return redirect(url_for('main.company_profile', company_id=company_id))

    # Get the company to be saved/unsaved, or return 404 if not found.
    company = Company.query.get_or_404(company_id)
    
    # Check if the company is already saved by the current client.
    # Query the `SavedCompany` table for an existing entry.
    saved_entry = SavedCompany.query.filter_by(
        client_id=current_user.client_id,
        company_id=company_id
    ).first()

    if saved_entry:
        # If an entry exists, the company is already saved, so delete it (un-save).
        db.session.delete(saved_entry)
        db.session.commit()
        flash(f'"{company.name}" has been un-saved from your list.', 'info')
    else:
        # If no entry exists, the company is not saved, so create a new entry (save).
        new_saved_entry = SavedCompany(client_id=current_user.client_id, company_id=company.company_id)
        db.session.add(new_saved_entry)
        db.session.commit()
        flash(f'"{company.name}" has been saved to your list!', 'success')
    
    # Redirect back to the company profile page after the action.
    return redirect(url_for('main.company_profile', company_id=company_id))


# --- API Routes ---

@bp.route('/api/search')
def search_companies_api(): # Renamed for clarity versus the frontend 'listings' route.
    """
    API endpoint for searching companies.
    This endpoint returns JSON data, allowing frontend JavaScript to dynamically
    fetch search results without full page reloads.
    It supports searching by company name, description, or associated service name.
    """
    # Get search query, page number, and items per page from URL parameters.
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # If no query is provided, return an empty result set immediately.
    if not query:
        return jsonify({
            "results": [], 
            "total": 0, 
            "page": 1, 
            "pages": 0, 
            "per_page": per_page, 
            "has_next": False, 
            "has_prev": False
        }), 200

    # Construct the search filter using `or_` to search across multiple fields.
    # It joins `Company` with `Service` to allow searching by `Service.service_name`.
    search_filter = or_(
        Company.name.ilike(f"%{query}%"),
        Company.description.ilike(f"%{query}%"),
        Service.service_name.ilike(f"%{query}%")
    )

    # Perform the database query with join and filter, then paginate the results.
    pagination = (
        Company.query.join(Service, Company.service_id == Service.service_id) # Join with Service table.
        .filter(search_filter) # Apply the search filter.
        .options(joinedload(Company.service)) # Eager load service data for each company.
        .paginate(page=page, per_page=per_page, error_out=False) # Paginate results.
    )

    # Format the results into a list of dictionaries for JSON output.
    results = []
    for c in pagination.items:
        company_data = {
            "company_id": c.company_id,
            "name": c.name,
            "description": c.description,
            "photo_url": c.photo_url,
            "rating": c.rating,
            # Include service details if available.
            "service": {
                "service_id": c.service.service_id,
                "service_name": c.service.service_name
            } if c.service else None
        }
        results.append(company_data)

    # Return the paginated search results in JSON format.
    return jsonify({
        "results": results,
        "total": pagination.total, # Total number of items matching the query.
        "page": pagination.page, # Current page number.
        "pages": pagination.pages, # Total number of pages.
        "per_page": pagination.per_page, # Items per page.
        "has_next": pagination.has_next, # Boolean: Is there a next page?
        "has_prev": pagination.has_prev # Boolean: Is there a previous page?
    })

# --- Client API (Backend Endpoints) ---
@bp.route('/api/clients', methods=['POST'])
def register_client_api():
    """
    API endpoint for clients to register a new account.
    It expects JSON data containing 'name', 'email', and 'password'.
    Performs validation for missing fields and existing emails.
    Returns: JSON response with success/error message and client_id (if successful).
    """
    data = request.get_json() # Get JSON data from the request body.
    # Validate if all required fields are present in the JSON data.
    if not data or not all(k in data for k in ('name', 'email', 'password')):
        return jsonify({"error": "Missing required fields (name, email, password)"}), 400

    # Check if a client with the provided email already exists.
    if Client.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already registered"}), 400

    # Hash the password for secure storage.
    hashed_password = generate_password_hash(data['password'])
    # Create a new Client instance.
    client = Client(name=data['name'], email=data['email'], password=hashed_password)
    # Add the new client to the database session and commit.
    db.session.add(client)
    db.session.commit()
    # Return a success JSON response with the new client's ID.
    return jsonify({"message": "Client registered successfully", "client_id": client.client_id}), 201

@bp.route('/api/clients/<int:client_id>', methods=['GET'])
@login_required # Requires the user to be logged in to access this API.
def get_client_api(client_id):
    """
    API endpoint to retrieve a client's details by their ID.
    Authorization: The `current_user` (logged-in user) must be the specific client
                   whose details are being requested.
    Returns: JSON response with client details or an error if unauthorized/not found.
    """
    # Authorization check: Ensure the logged-in user is a client and their ID matches the requested ID.
    if not current_user.is_client or current_user.client_id != client_id:
        return jsonify({"error": "You are not authorized to view this client's details."}), 403
    
    # Fetch the client by ID or return a 404 error if not found.
    client = Client.query.get_or_404(client_id)
    # Return client details as a JSON object.
    return jsonify({
        "client_id": client.client_id,
        "name": client.name,
        "email": client.email,
        "profile_picture_url": client.profile_picture_url # Include profile picture URL
    })

@bp.route('/api/clients/<int:client_id>', methods=['PUT'])
@login_required # Requires the user to be logged in to access this API.
def update_client_api(client_id):
    """
    API endpoint to update an existing client's details.
    Authorization: The `current_user` must be the specific client whose details
                   are being updated.
    Expects JSON data with fields to update (name, email, password).
    Returns: JSON response with success/error message.
    """
    # Authorization check: Ensure the logged-in user is a client and their ID matches the requested ID.
    if not current_user.is_client or current_user.client_id != client_id:
        return jsonify({"error": "You are not authorized to update this client's details."}), 403

    # Fetch the client to update or return a 404 error.
    client = Client.query.get_or_404(client_id)
    # Get JSON data from the request body.
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    # Update fields if they are present in the provided JSON data.
    if 'name' in data:
        client.name = data['name']
    if 'email' in data and data['email'] != client.email:
        # Check for email uniqueness if the email is being changed.
        if Client.query.filter(Client.email == data['email'], Client.client_id != client_id).first():
            return jsonify({"error": "Email already in use"}), 400
        client.email = data['email']
    if 'password' in data:
        # Use the `set_password` method to hash the new password.
        client.set_password(data['password']) 

    # Commit the changes to the database.
    db.session.commit()
    return jsonify({"message": "Client updated successfully"})

# --- Company API (Backend Endpoints) ---
@bp.route('/api/companies', methods=['POST'])
@login_required # Typically, only an admin or system process creates companies via API
def create_company_api():
    """
    API endpoint to create a new company.
    This route is typically restricted to authorized users (e.g., administrators)
    or used for internal system processes, indicated by `@login_required`.
    It expects JSON data with company details.
    Returns: JSON response with success/error message and company_id (if successful).
    """
    # CONSIDER: Add a more specific role check here if only admins can create companies via API.
    # Example: if not current_user.is_admin: return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json() # Get JSON data from the request body.
    # Validate if essential fields are provided.
    if not data or not all(k in data for k in ('name', 'description', 'service_id')):
        return jsonify({"error": "Missing required fields (name, description, service_id)"}), 400
    
    # Check if a company with the provided email (if given) already exists.
    if 'email' in data and Company.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already registered for a company"}), 400
    
    # Hash the password if provided; otherwise, set to None.
    hashed_password = generate_password_hash(data['password']) if 'password' in data else None

    # Create a new Company instance with provided or default data.
    company = Company(
        name=data['name'],
        email=data.get('email'), # Use .get() for optional fields.
        password=hashed_password,
        description=data['description'],
        photo_url=data.get('photo_url', '/static/images/default_company.png'), # Allow photo_url or use default
        rating=data.get('rating', 0), # Default rating to 0 if not provided.
        service_id=data['service_id']
    )
    try:
        # Add and commit the new company to the database.
        db.session.add(company)
        db.session.commit()
        # Return a success JSON response with the new company's ID.
        return jsonify({"message": "Company created successfully", "company_id": company.company_id}), 201
    except Exception as e:
        # On error, rollback database changes and return an error message.
        db.session.rollback()
        return jsonify({"error": f"Failed to create company: {str(e)}"}), 500


@bp.route('/api/companies', methods=['GET'])
def get_companies_api():
    """
    API endpoint to retrieve a list of all companies.
    Supports pagination for managing large datasets.
    Returns: JSON response containing a list of companies and pagination metadata.
    """
    # Get pagination parameters from query arguments, defaulting to page 1, 10 items per page.
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Paginate the query for all companies.
    pagination = Company.query.paginate(page=page, per_page=per_page, error_out=False)
    # Format the company data into a list of dictionaries for JSON output.
    output = [{
        "company_id": c.company_id,
        "name": c.name,
        "email": c.email, # Include email if it exists
        "description": c.description,
        "photo_url": c.photo_url,
        "rating": c.rating,
        "service_id": c.service_id
    } for c in pagination.items]

    # Return the paginated results as JSON.
    return jsonify({
        "companies": output,
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
        "per_page": pagination.per_page,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    })

@bp.route('/api/companies/<int:company_id>', methods=['GET'])
def get_company_api(company_id):
    """
    API endpoint to retrieve details for a single company by its ID.
    Returns: JSON response with the company's details or a 404 error if not found.
    """
    # Fetch the company by ID or return a 404 error.
    company = Company.query.get_or_404(company_id)
    # Return the company's details as a JSON object.
    return jsonify({
        "company_id": company.company_id,
        "name": company.name,
        "email": company.email, # Include email if it exists
        "description": company.description,
        "photo_url": company.photo_url,
        "rating": company.rating,
        "service_id": company.service_id
    })

@bp.route('/api/companies/<int:company_id>', methods=['PUT'])
@login_required # Requires the user to be logged in to access this API.
def update_company_api(company_id):
    """
    API endpoint to update an existing company's details.
    Authorization: The `current_user` must be the specific company whose details
                   are being updated.
    Expects JSON data with fields to update.
    Returns: JSON response with success/error message.
    """
    # Authorization check: Ensure the logged-in user is a company and their ID matches the requested ID.
    if not current_user.is_company or current_user.company_id != company_id:
        return jsonify({"error": "You are not authorized to update this company's details."}), 403

    # Fetch the company to update or return a 404 error.
    company = Company.query.get_or_404(company_id)
    # Get JSON data from the request body.
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    # Iterate through specified fields and update the company object if the field is present in data.
    for field in ('name', 'description', 'photo_url', 'rating', 'service_id'):
        if field in data:
            setattr(company, field, data[field]) # setattr allows setting attribute by string name.
    
    # Handle email update with uniqueness check if email is changed.
    if 'email' in data and data['email'] != company.email:
        if Company.query.filter(Company.email == data['email'], Company.company_id != company_id).first():
            return jsonify({"error": "Email already in use by another company"}), 400
        company.email = data['email']
    # Handle password update if provided, hashing it.
    if 'password' in data:
        company.set_password(data['password'])

    try:
        # Commit the changes to the database.
        db.session.commit()
        return jsonify({"message": "Company updated successfully"})
    except Exception as e:
        # On error, rollback changes and return an error message.
        db.session.rollback()
        return jsonify({"error": f"Failed to update company: {str(e)}"}), 500


@bp.route('/api/companies/<int:company_id>', methods=['DELETE'])
@login_required # Requires a logged-in user (typically the company owner or an admin).
def delete_company_api(company_id):
    """
    API endpoint to delete a company by its ID.
    Authorization: The `current_user` must be the specific company being deleted.
    Returns: JSON response with success/error message.
    """
    # Authorization check: Ensure the logged-in user is a company and their ID matches the requested ID.
    if not current_user.is_company or current_user.company_id != company_id:
        return jsonify({"error": "You are not authorized to delete this company."}), 403
    
    # Fetch the company to delete or return a 404 error.
    company = Company.query.get_or_404(company_id)
    try:
        # Delete the company from the database and commit.
        db.session.delete(company)
        db.session.commit()
        return jsonify({"message": "Company deleted successfully"})
    except Exception as e:
        # On error, rollback and return an error message.
        db.session.rollback()
        return jsonify({"error": f"Failed to delete company: {str(e)}"}), 500


@bp.route('/api/services/<int:service_id>/companies', methods=['GET'])
def get_companies_by_service_api(service_id):
    """
    API endpoint to retrieve companies filtered by a specific service ID.
    Supports pagination.
    Returns: JSON response with a list of companies offering the specified service and pagination metadata.
    """
    # Get pagination parameters.
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Query companies filtered by the provided service_id and paginate.
    pagination = Company.query.filter_by(service_id=service_id).paginate(page=page, per_page=per_page, error_out=False)
    # Format results for JSON output.
    output = [{
        "company_id": c.company_id,
        "name": c.name,
        "description": c.description,
        "photo_url": c.photo_url,
        "rating": c.rating,
        "service_id": c.service_id
    } for c in pagination.items]

    # Return paginated results as JSON.
    return jsonify({
        "companies": output,
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
        "per_page": pagination.per_page,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    })

# --- Service API (Backend Endpoints) ---
@bp.route('/api/services', methods=['POST'])
@login_required # Only authorized users (e.g., admin) can create services.
def create_service_api():
    """
    API endpoint to create a new service.
    This route typically requires administrative privileges.
    Expects JSON data with 'service_name'.
    Returns: JSON response with success/error message and service_id.
    """
    # CONSIDER: Add a more specific role check here if only admins can create services via API.
    # Example: if not current_user.is_admin: return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json() # Get JSON data from the request.
    # Validate for missing 'service_name'.
    if not data or not data.get('service_name'):
        return jsonify({"error": "Missing required field: service_name"}), 400

    # Create a new Service instance.
    service = Service(service_name=data['service_name'])
    try:
        # Add and commit the new service.
        db.session.add(service)
        db.session.commit()
        return jsonify({"message": "Service created successfully", "service_id": service.service_id}), 201
    except Exception as e:
        # On error, rollback and return error message.
        db.session.rollback()
        return jsonify({"error": f"Failed to create service: {str(e)}"}), 500


@bp.route('/api/services', methods=['GET'])
def get_services_api():
    """
    API endpoint to retrieve a list of all services.
    Supports pagination.
    Returns: JSON response with a list of services and pagination metadata.
    """
    # Get pagination parameters.
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Paginate the query for all services.
    pagination = Service.query.paginate(page=page, per_page=per_page, error_out=False)
    # Format results for JSON output.
    output = [{"service_id": s.service_id, "service_name": s.service_name} for s in pagination.items]

    # Return paginated results as JSON.
    return jsonify({
        "services": output,
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
        "per_page": pagination.per_page,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    })

@bp.route('/api/services/<int:service_id>', methods=['GET'])
def get_service_api(service_id):
    """
    API endpoint to retrieve details for a single service by its ID.
    Returns: JSON response with the service's details or a 404 error if not found.
    """
    # Fetch the service by ID or return a 404 error.
    service = Service.query.get_or_404(service_id)
    # Return service details as JSON.
    return jsonify({
        "service_id": service.service_id,
        "service_name": service.service_name
    })

@bp.route('/api/services/<int:service_id>', methods=['PUT'])
@login_required # Only authorized users (e.g., admin) can update services.
def update_service_api(service_id):
    """
    API endpoint to update an existing service's details.
    This route typically requires administrative privileges.
    Expects JSON data with 'service_name'.
    Returns: JSON response with success/error message.
    """
    # CONSIDER: Add a more specific role check here if only admins can update services via API.
    # Example: if not current_user.is_admin: return jsonify({"error": "Unauthorized"}), 403

    # Fetch the service to update or return a 404 error.
    service = Service.query.get_or_404(service_id)
    # Get JSON data from the request.
    data = request.get_json()
    # Validate for missing 'service_name'.
    if not data or not data.get('service_name'):
        return jsonify({"error": "Missing required field: service_name"}), 400

    service.service_name = data['service_name'] # Update the service name.
    try:
        # Commit the change.
        db.session.commit()
        return jsonify({"message": "Service updated successfully"})
    except Exception as e:
        # On error, rollback and return error message.
        db.session.rollback()
        return jsonify({"error": f"Failed to update service: {str(e)}"}), 500


@bp.route('/api/services/<int:service_id>', methods=['DELETE'])
@login_required # Only authorized users (e.g., admin) can delete services.
def delete_service_api(service_id):
    """
    API endpoint to delete a service by its ID.
    This route typically requires administrative privileges.
    Returns: JSON response with success/error message.
    """
    # CONSIDER: Add a more specific role check here if only admins can delete services via API.
    # Example: if not current_user.is_admin: return jsonify({"error": "Unauthorized"}), 403

    # Fetch the service to delete or return a 404 error.
    service = Service.query.get_or_404(service_id)
    try:
        # Delete the service from the database and commit.
        db.session.delete(service)
        db.session.commit()
        return jsonify({"message": "Service deleted successfully"})
    except Exception as e:
        # On error, rollback and return error message.
        db.session.rollback()
        return jsonify({"error": f"Failed to delete service: {str(e)}"}), 500
    

# --- Saved Companies API (Backend Endpoints) ---
@bp.route('/api/saved_companies', methods=['POST'])
@login_required # This API endpoint requires a user to be logged in.
def save_company_api():
    """
    API endpoint to save a company to the current client's saved list.
    Authorization: Only logged-in users who are 'clients' can use this endpoint.
    Expects JSON data containing 'company_id'.
    Returns: JSON response with success/error message and the ID of the new saved entry.
    """
    if not current_user.is_client:
        # If the logged-in user is not a client, return a 403 Forbidden error.
        return jsonify({"error": "Only clients can save companies."}), 403

    data = request.get_json() # Get JSON data from the request body.
    # Validate if 'company_id' is present in the JSON data.
    # Note: `client_id` is derived from `current_user.client_id` for security, not from request data.
    if not data or not data.get('company_id'):
        return jsonify({"error": "Missing required 'company_id' field"}), 400

    company_id = data['company_id']
    
    # Ensure the company being saved actually exists in the database.
    if not Company.query.get(company_id):
        return jsonify({"error": "Company not found."}), 404

    # Check if the company is already saved by the current client to prevent duplicates.
    if SavedCompany.query.filter_by(client_id=current_user.client_id, company_id=company_id).first():
        # If already saved, return a message indicating this. A 200 OK or 409 Conflict can be used.
        return jsonify({"message": "Company already saved."}), 200 

    # Create a new SavedCompany instance, linking the current client to the specified company.
    saved = SavedCompany(client_id=current_user.client_id, company_id=company_id)
    try:
        # Add the new entry to the database session and commit.
        db.session.add(saved)
        db.session.commit()
        # Return a success JSON response with the ID of the newly created saved entry.
        return jsonify({"message": "Company saved successfully", "saved_id": saved.saved_id}), 201
    except Exception as e:
        # If an error occurs, rollback the session and return an error message.
        db.session.rollback()
        return jsonify({"error": f"Failed to save company: {str(e)}"}), 500


@bp.route('/api/saved_companies/<int:saved_id>', methods=['DELETE'])
@login_required # This API endpoint requires a user to be logged in.
def delete_saved_company_api(saved_id):
    """
    API endpoint to delete a specific saved company entry by its ID.
    Authorization: The `current_user` must be the 'client' who originally created
                   this saved entry.
    Returns: JSON response with success/error message.
    """
    # Fetch the SavedCompany entry by its ID or return 404 if not found.
    saved_entry = SavedCompany.query.get_or_404(saved_id)
    
    # Authorization check: Ensure the logged-in user is a client AND they are the one
    # who originally saved this specific entry.
    if not current_user.is_client or current_user.client_id != saved_entry.client_id:
        return jsonify({"error": "You are not authorized to delete this saved company entry."}), 403

    try:
        # Delete the saved entry from the database and commit.
        db.session.delete(saved_entry)
        db.session.commit()
        return jsonify({"message": "Saved company entry deleted successfully"}), 200
    except Exception as e:
        # If an error occurs, rollback the session and return an error message.
        db.session.rollback()
        return jsonify({"error": f"Failed to delete saved company entry: {str(e)}"}), 500


# --- Ratings API (Backend Endpoints) ---
@bp.route('/api/companies/<int:company_id>/ratings', methods=['POST'])
@login_required # This API endpoint requires a user to be logged in.
def add_rating_api(company_id):
    """
    API endpoint to add a new rating for a specific company.
    Authorization: Only logged-in users who are 'clients' can submit ratings.
    Expects JSON data containing 'rating' (and optionally 'review').
    After adding, it recalculates and updates the company's average rating.
    Returns: JSON response with success/error message and the new rating's ID.
    """
    # Ensure only clients can submit ratings.
    if not current_user.is_client:
        return jsonify({"error": "Only clients can submit ratings."}), 403 # Forbidden

    data = request.get_json() # Get JSON data from the request.
    # Validate if the 'rating' field is present.
    if not data or 'rating' not in data: 
        return jsonify({"error": "Missing required 'rating' field"}), 400

    # Validate the rating value: it must be a number between 1.0 and 5.0.
    try:
        rating_value = float(data['rating']) 
        if not (1.0 <= rating_value <= 5.0): 
            return jsonify({"error": "Rating must be between 1 and 5"}), 400
    except ValueError:
        # If 'rating' cannot be converted to a float.
        return jsonify({"error": "Rating must be a number"}), 400

    # Ensure the company being rated exists.
    company = Company.query.get(company_id)
    if not company:
        return jsonify({"error": "Company not found."}), 404

    # Create a new Rating instance.
    # CRITICAL CHANGE: Use `current_user.client_id` for security, ensuring the rating
    # is attributed to the authenticated client, not a client ID passed from the frontend.
    rating = Rating(
        client_id=current_user.client_id, 
        company_id=company_id,
        rating=rating_value, 
        review=data.get('review', "").strip() # Get review, default to empty string if not provided, then strip whitespace.
    )
    try:
        # Add and commit the new rating.
        db.session.add(rating)
        db.session.commit()

        # After a new rating is added, recalculate and update the company's average rating.
        update_company_average_rating(company_id) 

        return jsonify({"message": "Rating added successfully", "rating_id": rating.rating_id}), 201
    except Exception as e:
        # On error, rollback and return error message.
        db.session.rollback()
        return jsonify({"error": f"Failed to add rating: {str(e)}"}), 500

# --- Helper function to update company's average rating ---
def update_company_average_rating(company_id):
    """
    Helper function to recalculate and update a company's average rating in the database.
    This is typically called after a new rating is added or an existing one is modified/deleted.
    
    Args:
        company_id (int): The ID of the company whose average rating needs to be updated.
    """
    company = Company.query.get(company_id)
    if company:
        # Query the database to calculate the average of all ratings for this company.
        # `func.avg(Rating.rating)` uses the SQL AVG aggregate function.
        # `.scalar()` retrieves a single value (the average) from the query result.
        avg_rating = db.session.query(func.avg(Rating.rating)).filter(Rating.company_id == company_id).scalar()
        
        # Update the company's 'rating' field in the Company model.
        # If `avg_rating` is None (no ratings yet), default to 0.0.
        # `round(avg_rating, 2)` rounds the average to two decimal places for cleaner display.
        company.rating = round(avg_rating, 2) if avg_rating is not None else 0.0 
        db.session.commit() # Commit the updated average rating to the database.
    # else: If the company is not found (which should ideally not happen if called correctly),
    #       you might want to log an error here.


@bp.route('/api/companies/<int:company_id>/ratings', methods=['GET'])
def get_ratings_api(company_id):
    """
    API endpoint to retrieve all ratings for a specific company.
    Supports pagination.
    Returns: JSON response with a list of ratings for the specified company and pagination metadata.
    """
    # Get pagination parameters.
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Query ratings for the specified company and paginate.
    pagination = Rating.query.filter_by(company_id=company_id).paginate(page=page, per_page=per_page, error_out=False)
    # Format the ratings data into a list of dictionaries for JSON output.
    output = [{
        "rating_id": r.rating_id,
        "client_id": r.client_id,
        "company_id": r.company_id,
        "rating": r.rating,
        "review": r.review,
        # Convert timestamp to ISO format string for consistent JSON representation.
        "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        "client_name": r.client.name if r.client else 'N/A' # Include client's name for display (assuming client relationship loaded)
    } for r in pagination.items]

    # Return the paginated results as JSON.
    return jsonify({
        "ratings": output,
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
        "per_page": pagination.per_page,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    })

@bp.route('/chats')
@login_required # This route requires the user to be logged in to view their chats.
def all_chats():
    """
    Renders the chat list page, showing all conversations (unique chat partners)
    for the currently logged-in user (client or company).
    It identifies unique conversation partners and retrieves the last message for each.
    """
    conversations = [] # List to store formatted conversation data.
    
    # Fetch all messages related to the current user.
    # Eager loading is crucial here to prevent N+1 queries when accessing
    # sender/receiver details in the loop.
    # We load the opposite party's details based on whether the current user is a client or company.
    if current_user.is_client:
        all_related_messages = Message.query.filter(
            or_(
                Message.sender_client_id == current_user.client_id,
                Message.receiver_client_id == current_user.client_id
            )
        ).options(
            joinedload(Message.sender_company), # If current user is client, the other party is a company
            joinedload(Message.receiver_company) # or another company they sent/received from
        ).all()
    elif current_user.is_company:
        all_related_messages = Message.query.filter(
            or_(
                Message.sender_company_id == current_user.company_id,
                Message.receiver_company_id == current_user.company_id
            )
        ).options(
            joinedload(Message.sender_client), # If current user is company, the other party is a client
            joinedload(Message.receiver_client) # or another client they sent/received from
        ).all()
    else:
        # This case should ideally not be reached due to `@login_required`,
        # but provides a safe fallback.
        all_related_messages = [] 

    unique_chat_partners = {} # Dictionary to store the latest message for each unique conversation partner.
                               # Key format: (other_party_id, other_party_type)
    for msg in all_related_messages:
        # Determine the other party in this specific message conversation.
        other_party_id = None
        other_party_type = None
        other_party_obj = None

        if current_user.is_client:
            # If the current user is a client and they sent the message to a company:
            if msg.sender_client_id == current_user.client_id and msg.receiver_company_id:
                other_party_id = msg.receiver_company_id
                other_party_type = 'company'
                other_party_obj = msg.receiver_company 
            # If the current user is a client and they received the message from a company:
            elif msg.receiver_client_id == current_user.client_id and msg.sender_company_id:
                other_party_id = msg.sender_company_id
                other_party_type = 'company'
                other_party_obj = msg.sender_company 
        elif current_user.is_company:
            # If the current user is a company and they sent the message to a client:
            if msg.sender_company_id == current_user.company_id and msg.receiver_client_id:
                other_party_id = msg.receiver_client_id
                other_party_type = 'client'
                other_party_obj = msg.receiver_client 
            # If the current user is a company and they received the message from a client:
            elif msg.receiver_company_id == current_user.company_id and msg.sender_client_id:
                other_party_id = msg.sender_client_id
                other_party_type = 'client'
                other_party_obj = msg.sender_client 
        
        # If an 'other party' is successfully identified:
        if other_party_id and other_party_obj:
            key = (other_party_id, other_party_type)
            # Store the message if it's the first message found for this partner,
            # or if it's a newer message than the one already stored for this partner.
            if key not in unique_chat_partners or msg.timestamp > unique_chat_partners[key]['last_message'].timestamp:
                unique_chat_partners[key] = {
                    'other_party': other_party_obj,
                    'last_message': msg,
                    'other_party_type': other_party_type,
                    # Store both client_id and company_id for `url_for('main.view_chat')`
                    # The current user's ID will be the one matching their type,
                    # the other party's ID will be the one matching their type.
                    'client_id': current_user.client_id if current_user.is_client else (other_party_obj.client_id if other_party_type == 'client' else None),
                    'company_id': current_user.company_id if current_user.is_company else (other_party_obj.company_id if other_party_type == 'company' else None)
                }
    
    # Iterate through the collected unique chat partners to prepare data for the template.
    for key, conv_data in unique_chat_partners.items():
        other_party = conv_data['other_party']
        last_message = conv_data['last_message']
        
        # Construct the chat URL. This requires both a client_id and a company_id.
        if conv_data['client_id'] and conv_data['company_id']: 
            chat_url = url_for('main.view_chat', client_id=conv_data['client_id'], company_id=conv_data['company_id'])
        else:
            chat_url = '#' # Fallback if necessary IDs are missing (should not occur if logic is correct).

        # Determine the display name for the other party in the chat list.
        other_party_display_name = ''
        if conv_data['other_party_type'] == 'company':
            # Check if 'name' attribute exists and is not empty.
            other_party_display_name = other_party.name if hasattr(other_party, 'name') and other_party.name else 'Unknown Company'
        elif conv_data['other_party_type'] == 'client':
            # Check for 'name' first, then 'username' (if it were a field), otherwise 'Unknown Client'.
            other_party_display_name = other_party.name if hasattr(other_party, 'name') and other_party.name else (other_party.username if hasattr(other_party, 'username') and other_party.username else 'Unknown Client')

        conversations.append({
            'other_party': other_party, # The Client or Company object of the other participant.
            'last_message': last_message, # The latest message in this conversation.
            'chat_url': chat_url, # The URL to view this specific chat.
            'other_party_display_name': other_party_display_name # The name to display for the other participant.
        })

    # Sort conversations by the timestamp of their last message, in reverse (most recent first).
    # Uses `datetime.min.replace(tzinfo=timezone.utc)` as a safe fallback for comparison if a message has no timestamp.
    conversations.sort(key=lambda x: x['last_message'].timestamp if x['last_message'] else datetime.min.replace(tzinfo=timezone.utc), reverse=True) 

    # Render the chat list template, passing the sorted conversations.
    return render_template('chat_list.html', title='Your Chats', conversations=conversations)

# --- Messaging API (Backend Endpoints) ---
@bp.route('/api/messages/<int:client_id>/<int:company_id>', methods=['GET'])
@login_required # CRITICAL: This API endpoint requires a user to be logged in.
def get_messages_api(client_id, company_id):
    """
    API endpoint to retrieve all messages exchanged between a specific client and a specific company.
    Authorization: The `current_user` must be either the client or the company participant
                   in the conversation.
    Returns: JSON response containing a list of messages and pagination metadata.
    """
    # Authorization check:
    # Verify that the logged-in user is one of the two participants in this chat.
    is_client_participant = current_user.is_client and current_user.client_id == client_id
    is_company_participant = current_user.is_company and current_user.company_id == company_id

    if not (is_client_participant or is_company_participant):
        return jsonify({"error": "You are not authorized to view these messages."}), 403

    # Get pagination parameters from query arguments.
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Filter for messages where the client_id and company_id match the sender/receiver roles.
    # Uses `or_` to cover messages sent from client to company AND messages sent from company to client.
    pagination = (
        Message.query.filter(
            or_(
                (Message.sender_client_id == client_id and Message.receiver_company_id == company_id),
                (Message.sender_company_id == company_id and Message.receiver_client_id == client_id)
            )
        )
        .order_by(Message.timestamp.asc()) # Order messages by timestamp ascending for chronological chat display.
        .paginate(page=page, per_page=per_page, error_out=False) # Paginate the results.
    )

    # Format the messages into a list of dictionaries for JSON output.
    output = [{
        "message_id": m.message_id,
        "sender_client_id": m.sender_client_id,
        "sender_company_id": m.sender_company_id,
        "receiver_client_id": m.receiver_client_id,
        "receiver_company_id": m.receiver_company_id,
        "content": m.content,
        # Convert timestamp to ISO format string for consistent JSON.
        "timestamp": m.timestamp.isoformat() if m.timestamp else None,
        "is_read": m.is_read
    } for m in pagination.items]

    # Return the paginated messages as JSON.
    return jsonify({
        "messages": output,
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
        "per_page": pagination.per_page,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    })


# --- Messaging API (Backend Endpoints) ---
@bp.route('/api/messages', methods=['POST'])
@login_required # CRITICAL: This API endpoint requires a user to be logged in to send messages.
def send_message_api():
    """
    API endpoint to send a new message between a client and a company.
    Authorization: The sender (either client or company) must be the `current_user`.
    It intelligently determines the sender based on the `current_user`'s type
    and expects the corresponding receiver ID.
    Returns: JSON response with success/error message, new message ID, and timestamp.
    """
    data = request.get_json() # Get JSON data from the request body.
    
    content = data.get('content') # The message text content.
    receiver_client_id = data.get('receiver_client_id') # Expected if a company is sending to a client.
    receiver_company_id = data.get('receiver_company_id') # Expected if a client is sending to a company.

    if not content:
        return jsonify({"error": "Message content is required"}), 400

    sender_client_id = None # Initialize sender IDs to None.
    sender_company_id = None
    
    # Determine the sender's ID based on the `current_user`'s type.
    if current_user.is_client:
        sender_client_id = current_user.client_id
    elif current_user.is_company:
        sender_company_id = current_user.company_id
    else:
        # This case should ideally be caught by `@login_required`, but it's a defensive check.
        return jsonify({"error": "Unauthorized sender type. Must be a client or company."}), 403 
    
    # Validate the receiver based on the sender's type to ensure messages are sent correctly.
    if sender_client_id: # If the current user is a client, they must send to a company.
        # Check if `receiver_company_id` is provided and `receiver_client_id` is NOT.
        if not receiver_company_id or receiver_client_id: 
            return jsonify({"error": "Client can only send messages to a company. Provide 'receiver_company_id'."}), 400
        # Ensure the target company exists.
        if not Company.query.get(receiver_company_id):
            return jsonify({"error": "Receiver company not found."}), 404
        receiver_client_id = None # Explicitly ensure client receiver ID is null for client-to-company messages.
    elif sender_company_id: # If the current user is a company, they must send to a client.
        # Check if `receiver_client_id` is provided and `receiver_company_id` is NOT.
        if not receiver_client_id or receiver_company_id: 
            return jsonify({"error": "Company can only send messages to a client. Provide 'receiver_client_id'."}), 400
        # Ensure the target client exists.
        if not Client.query.get(receiver_client_id):
            return jsonify({"error": "Receiver client not found."}), 404
        receiver_company_id = None # Explicitly ensure company receiver ID is null for company-to-client messages.

    # Create a new Message instance with the determined sender and receiver IDs, and content.
    message = Message(
        sender_client_id=sender_client_id,
        sender_company_id=sender_company_id,
        receiver_client_id=receiver_client_id,
        receiver_company_id=receiver_company_id,
        content=content
    )
    try:
        # Add the message to the database session and commit.
        db.session.add(message)
        db.session.commit()
        # Return a success JSON response including the new message ID and its timestamp.
        return jsonify({"message": "Message sent successfully", "message_id": message.message_id, "timestamp": message.timestamp.isoformat()}), 201
    except Exception as e:
        # On database error, rollback the session and return an error message.
        db.session.rollback()
        return jsonify({"error": f"Failed to send message: {str(e)}"}), 500


# --- Individual Chat View Route ---
@bp.route('/chat/<int:client_id>/<int:company_id>', methods=['GET', 'POST'])
@login_required # Requires the user to be logged in to view or send messages in a chat.
def view_chat(client_id, company_id):
    """
    Renders the individual chat conversation page between a specific client and company.
    It handles both displaying existing messages (GET request) and processing new
    messages sent by the current user (POST request).
    Authorization: The `current_user` must be one of the two participants (either the client or the company)
                   in the chat being viewed.

    Args:
        client_id (int): The ID of the client involved in the conversation.
        company_id (int): The ID of the company involved in the conversation.
    """
    # First, ensure both the client and company involved in the chat actually exist.
    client_obj = Client.query.get_or_404(client_id)
    company_obj = Company.query.get_or_404(company_id)

    # Authorization check:
    # Verify that the currently logged-in user is one of the participants in this specific chat.
    is_client_participant = current_user.is_client and current_user.client_id == client_id
    is_company_participant = current_user.is_company and current_user.company_id == company_id

    # If the current user is neither the client nor the company in this chat, deny access.
    if not (is_client_participant or is_company_participant):
        flash('You are not authorized to view this chat.', 'danger')
        return redirect(url_for('main.index'))

    # Determine the sender and receiver IDs for database operations based on who `current_user` is.
    # Also determine the 'other party' object for display in the template.
    if current_user.is_client:
        sender_id_for_db_client = current_user.client_id
        sender_id_for_db_company = None # A client cannot be a company sender.
        receiver_id_for_db_client = None # A client cannot be a client receiver when sending to a company.
        receiver_id_for_db_company = company_obj.company_id # The company is the receiver.
        other_party = company_obj # The other participant in the chat is the company.
        chat_title = f'Chat with {company_obj.name or 'Unknown Company'}' # Title for the chat page.
    else: # `current_user` must be a company.
        sender_id_for_db_client = None # A company cannot be a client sender.
        sender_id_for_db_company = current_user.company_id # The company is the sender.
        receiver_id_for_db_client = client_obj.client_id # The client is the receiver.
        receiver_id_for_db_company = None # A company cannot be a company receiver when sending to a client.
        other_party = client_obj # The other participant in the chat is the client.
        chat_title = f'Chat with {client_obj.name or client_obj.username or 'Unknown Client'}' # Title for the chat page.

    # Fetch existing messages between this specific client and company.
    # The `or_` condition ensures we fetch messages regardless of who was the sender/receiver.
    # `order_by(Message.timestamp.asc())` ensures messages are displayed in chronological order.
    messages = Message.query.filter(
        or_(
            (Message.sender_client_id == client_id) & (Message.receiver_company_id == company_id),
            (Message.sender_company_id == company_id) & (Message.receiver_client_id == client_id)
        )
    ).order_by(Message.timestamp.asc()).all() 

    # Handle sending a new message if the form is submitted via a POST request.
    if request.method == 'POST':
        content = request.form.get('message_content') # Get message content from the form.
        # Validate that the message content is not empty after stripping whitespace.
        if content and content.strip(): 
            new_message = Message(
                sender_client_id=sender_id_for_db_client,
                sender_company_id=sender_id_for_db_company,
                receiver_client_id=receiver_id_for_db_client,
                receiver_company_id=receiver_id_for_db_company,
                content=content.strip() # Store stripped content.
            )
            try:
                # Add the new message to the database and commit.
                db.session.add(new_message)
                db.session.commit()
                flash('Message sent!', 'success')
                # Redirect to the GET route of the same page. This is a common pattern
                # (Post/Redirect/Get) to prevent form re-submission on refresh.
                return redirect(url_for('main.view_chat', client_id=client_id, company_id=company_id))
            except Exception as e:
                # On error, rollback database changes and flash an error message.
                db.session.rollback()
                flash(f'An error occurred while sending message: {str(e)}', 'danger')
        else:
            # If message content is empty, flash an error.
            flash('Message content cannot be empty.', 'danger')

    # For GET requests (or after a POST redirect), render the chat template.
    return render_template('chat.html',
                           title=chat_title, # The title displayed on the chat page.
                           messages=messages, # List of all messages in the conversation.
                           recipient=other_party, # The object representing the other chat participant.
                           current_user=current_user, # The logged-in user object, needed for conditional rendering (e.g., message alignment).
                           client_id=client_id, # Passed to the template, useful for form actions or JS.
                           company_id=company_id # Passed to the template, useful for form actions or JS.
                          )