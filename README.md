# Skilled Worker Marketplace

Welcome to the Skilled Worker Marketplace! This platform connects clients seeking various services with skilled companies offering those services. Clients can browse company profiles, view their work, read reviews, and communicate directly with companies. Companies can showcase their services, manage their profiles, and interact with potential clients.

---

## Features

* **User Authentication:** Secure login and registration for both clients and companies.
* **Profile Management:** Clients and companies can view and update their respective profiles.
* **Company Profiles:** Detailed company pages displaying services offered, descriptions, photo galleries, and customer reviews.
* **Company Search & Browse:** Easily find companies based on service type.
* **Rating & Reviews:** Clients can leave ratings and reviews for companies.
* **Direct Messaging:** Clients and companies can communicate through an integrated messaging system.
* **Saved Companies:** Clients can save favorite companies for quick access.

---

## Getting Started

Follow these steps to set up and run the Skilled Worker Marketplace on your local machine.

### Prerequisites

Before you begin, ensure you have the following installed:

* **Python 3.8+**: [Download Python](https://www.python.org/downloads/)
* **pip**: Python's package installer (usually comes with Python).

### Installation

1.  **Clone the Repository (if applicable):**
    If your code is in a Git repository, clone it to your local machine:
    ```bash
    git clone <your-repository-url>
    cd <your-project-folder>
    ```
    If you just have the files, navigate to your project's root directory in your terminal.

2.  **Create a Virtual Environment (Recommended):**
    It's good practice to use a virtual environment to manage dependencies:
    ```bash
    python -m venv venv
    ```

3.  **Activate the Virtual Environment:**
    * **On Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    * **On macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

4.  **Install Dependencies:**
    Install all required Python packages. check the  `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```
    

### Running the Application

Once the prerequisites are met and dependencies are installed, you can start the application:

1.  **Initialize and Seed the Database:**
    This step sets up your database schema and populates it with initial data (like services).
    ```bash
    python seed.py
    ```

2.  **Start the Flask Application:**
    This will run your web server.
    ```bash
    python run.py
    ```

3.  **Access the Application:**
    Open your web browser and navigate to `http://127.0.0.1:5000/` (or the address shown in your terminal after `run.py` starts).

---

## Project Structure 

A brief overview of the main directories and files:

* `app/`: Contains the core application logic (models, routes, templates, static files).
    * `app/__init__.py`: Application factory and configuration.
    * `app/models.py`: Database models (Client, Company, Service, etc.).
    * `app/routes.py`: Defines all web routes and API endpoints.
    * `app/templates/`: HTML templates for rendering web pages.
    * `app/static/`: Static assets like CSS, JavaScript, and uploaded images.
* `config.py`: Application configuration settings.
* `run.py`: Entry point to start the Flask development server.
* `seed.py`: Script to initialize and populate the database.
* `venv/`: Python virtual environment (if created).

---

## Technologies Used

* **Flask:** Web Framework
* **Flask-SQLAlchemy:** ORM for database interaction
* **SQLite:** Default database (can be configured for others)
* **Flask-Login:** User session management
* **Jinja2:** Templating Engine
* **HTML, CSS, JavaScript:** Frontend development

---

## License

[Choose a license, e.g., MIT, Apache 2.0, etc., and add a link here if you have a LICENSE file.]