import requests # Import the 'requests' library, which is used to make HTTP requests
                 # (like GET, POST, PUT, DELETE) to web services and APIs.

# Define the base URL for the API endpoints.
# This makes it easy to change the server address if your application moves
# or is deployed elsewhere. It points to the local Flask development server.
BASE_URL = 'http://127.0.0.1:5000'

def safe_print_json(response, prefix):
    """
    Safely prints the HTTP response status code and its JSON content.
    If the response content is not valid JSON, it prints the raw text
    and an error message, preventing the script from crashing.

    Args:
        response (requests.Response): The response object received from an HTTP request.
        prefix (str): A string to prepend to the output (e.g., "Register Client:").
    """
    print(f"{prefix} Status Code: {response.status_code}") # Print the descriptive prefix and HTTP status code.
    try:
        print("Response JSON:", response.json()) # Attempt to parse and print the response body as JSON.
    except Exception as e:
        # If JSON parsing fails (e.g., response is not JSON or is empty),
        # print an error and the raw response text for debugging.
        print(f"Error parsing JSON: {e}")
        print("Response Text:", response.text)


def test_register_client():
    """
    Tests the client registration API endpoint by sending a POST request
    with new client data.
    """
    url = f"{BASE_URL}/api/clients" # Construct the full URL for the client registration endpoint.
    data = { # Define the data payload (user details) to be sent in the request body.
        "name": "Bob",
        "email": "bob@example.com",
        "password": "bob123"
    }
    # Send a POST request to the API with the data as JSON.
    response = requests.post(url, json=data)
    safe_print_json(response, "Test Register Client:") # Print the response using the safe helper function.


def test_create_service():
    """
    Tests the service creation API endpoint by sending a POST request
    to add a new service type.
    """
    url = f"{BASE_URL}/api/services" # URL for the services endpoint.
    data = { # Data for the new service.
        "service_name": "Electrical Work"
    }
    response = requests.post(url, json=data) # Send POST request.
    safe_print_json(response, "Test Create Service:") # Print response.


def test_get_services():
    """
    Tests retrieving all available services by sending a GET request.
    """
    url = f"{BASE_URL}/api/services" # URL to get all services.
    response = requests.get(url) # Send GET request.
    safe_print_json(response, "Test Get Services:") # Print response.


def test_update_service(service_id):
    """
    Tests updating an existing service by sending a PUT request.
    Requires a valid 'service_id' to specify which service to update.

    Args:
        service_id (int): The ID of the service to be updated.
    """
    url = f"{BASE_URL}/api/services/{service_id}" # URL includes the specific service ID.
    data = { # Data to update the service name.
        "service_name": "Plumbing"
    }
    response = requests.put(url, json=data) # Send PUT request with updated data.
    safe_print_json(response, f"Test Update Service (ID: {service_id}):") # Print response.


def test_delete_service(service_id):
    """
    Tests deleting an existing service by sending a DELETE request.
    Requires a valid 'service_id' to specify which service to delete.

    Args:
        service_id (int): The ID of the service to be deleted.
    """
    url = f"{BASE_URL}/api/services/{service_id}" # URL includes the specific service ID.
    response = requests.delete(url) # Send DELETE request.
    safe_print_json(response, f"Test Delete Service (ID: {service_id}):") # Print response.


def test_save_company():
    """
    Tests saving a company to a client's saved list by sending a POST request.
    This simulates a client "bookmarking" a company.
    """
    url = f"{BASE_URL}/api/saved_companies" # URL for the saved companies endpoint.
    data = { # Data specifying which client saves which company.
        "client_id": 1,  # Assuming a client with ID 1 exists.
        "company_id": 1  # Assuming a company with ID 1 exists.
    }
    response = requests.post(url, json=data) # Send POST request.
    safe_print_json(response, "Test Save Company:") # Print response.


def test_get_saved_companies():
    """
    Tests retrieving all companies saved by a specific client by sending a GET request
    with a client ID as a query parameter.
    """
    url = f"{BASE_URL}/api/saved_companies?client_id=1" # URL with query parameter for client ID.
    response = requests.get(url) # Send GET request.
    safe_print_json(response, "Test Get Saved Companies:") # Print response.


def test_delete_saved_company(saved_id):
    """
    Tests deleting a saved company entry by its unique saved ID (e.g., the ID of the
    saved_companies table entry), sending a DELETE request.

    Args:
        saved_id (int): The ID of the specific saved company entry to be deleted.
    """
    url = f"{BASE_URL}/api/saved_companies/{saved_id}" # URL with the specific saved company entry ID.
    response = requests.delete(url) # Send DELETE request.
    safe_print_json(response, f"Test Delete Saved Company (ID: {saved_id}):") # Print response.


def test_create_company():
    """
    Tests creating a new company entry by sending a POST request with company details.
    """
    url = f"{BASE_URL}/api/companies" # URL for the companies endpoint.
    data = { # Data for the new company.
        "name": "Test Plumbing Co.",
        "description": "Professional plumbing services for homes and businesses.",
        "photo_url": "https://placehold.co/600x400/000000/FFFFFF?text=Company+Photo", # Placeholder URL
        "rating": 4.5,
        "service_id": 1 # Assuming a service with ID 1 exists (e.g., 'Plumbing').
    }
    response = requests.post(url, json=data) # Send POST request.
    safe_print_json(response, "Test Create Company:") # Print response.


def test_get_all_companies():
    """
    Tests retrieving all registered companies by sending a GET request.
    """
    url = f"{BASE_URL}/api/companies" # URL to get all companies.
    response = requests.get(url) # Send GET request.
    safe_print_json(response, "Test Get All Companies:") # Print response.


def test_update_company(company_id):
    """
    Tests updating an existing company's details by sending a PUT request.
    Requires a valid 'company_id'.

    Args:
        company_id (int): The ID of the company to be updated.
    """
    url = f"{BASE_URL}/api/companies/{company_id}" # URL includes the specific company ID.
    data = {"description": "Updated description: We now offer emergency services 24/7!"} # Data to update.
    response = requests.put(url, json=data) # Send PUT request with updated data.
    safe_print_json(response, f"Test Update Company (ID: {company_id}):") # Print response.


def test_get_single_company(company_id):
    """
    Tests retrieving details for a single company by its ID, using a GET request.

    Args:
        company_id (int): The ID of the company to retrieve.
    """
    url = f"{BASE_URL}/api/companies/{company_id}" # URL includes the specific company ID.
    response = requests.get(url) # Send GET request.
    safe_print_json(response, f"Test Get Single Company (ID: {company_id}):") # Print response.


def test_delete_company(company_id):
    """
    Tests deleting a company by its ID, using a DELETE request.
    Requires a valid 'company_id'.

    Args:
        company_id (int): The ID of the company to be deleted.
    """
    url = f"{BASE_URL}/api/companies/{company_id}" # URL includes the specific company ID.
    response = requests.delete(url) # Send DELETE request.
    safe_print_json(response, f"Test Delete Company (ID: {company_id}):") # Print response.


# This block executes when the script is run directly.
if __name__ == "__main__":
    print("--- Starting API Tests ---")

    # --- Client API Tests ---
    print("\n--- Client Registration Test ---")
    test_register_client() # Register a new client.

    # --- Service API Tests ---
    print("\n--- Service Management Tests ---")
    # Note: These tests assume your database is cleared or handles duplicates gracefully.
    # For robust testing, you might need to check for existing IDs or use dummy data.
    
    # Create a new service.
    test_create_service() 
    # Retrieve all services to verify the creation.
    test_get_services()

    # NOTE: For the following update/delete tests, 'service_id' must be an ID
    # of an existing service in your database (e.g., from a previous 'test_create_service' run).
    # You might need to manually check your database or modify this ID if tests fail.
    service_id = 1 # Example ID; adjust if your actual service ID is different.
    test_update_service(service_id) # Update an existing service.
    test_delete_service(service_id) # Delete that service.

    # --- Saved Companies API Tests ---
    print("\n--- Saved Companies Tests ---")
    # These tests assume client_id=1 and company_id=1 exist.
    test_save_company() # Save a company for a client.
    test_get_saved_companies() # Retrieve saved companies for a client.

    # NOTE: 'saved_id' needs to be the ID of the 'saved_companies' entry,
    # which is usually an auto-incrementing ID generated upon saving.
    # You might need to manually get this ID from your database or from a previous test run's output.
    saved_id = 1 # Example ID; adjust if your actual saved entry ID is different.
    test_delete_saved_company(saved_id) # Delete the saved company entry.

    # --- Company API Tests ---
    print("\n--- Company Management Tests ---")
    test_create_company() # Create a new company.
    test_get_all_companies() # Get all companies to verify creation.

    # NOTE: 'company_id' needs to be the ID of an existing company.
    # You might need to manually get this ID from your database or from the output of 'test_create_company'.
    company_id = 1 # Example ID; adjust if your actual company ID is different.
    test_update_company(company_id) # Update details of an existing company.
    test_get_single_company(company_id) # Retrieve details of a single company.
    test_delete_company(company_id) # Delete the company.

    # --- Additional API Tests (Service Companies, Ratings, Search) ---
    print("\n--- Additional API Functionality Tests ---")
    # Test: List companies offering a specific service.
    # Ensure 'service_id' corresponds to an existing service that has companies linked to it.
    service_id = 1  # Replace with an actual service ID from your database
    res = requests.get(f"{BASE_URL}/api/services/{service_id}/companies")
    print(f"Companies for Service ID {service_id}: Status Code: {res.status_code}")
    safe_print_json(res, "") # Use safe_print_json for consistent output.

    # Test: Add a rating to a company.
    # Ensure 'company_id' and 'client_id' are valid and exist.
    company_id = 1 # Replace with an actual company ID
    rating_data = {
        "client_id": 1, # Replace with an actual client ID
        "rating": 4,
        "review": "Very good service! Prompt and efficient."
    }
    res = requests.post(f"{BASE_URL}/api/companies/{company_id}/ratings", json=rating_data)
    print(f"Add Rating for Company ID {company_id}: Status Code: {res.status_code}")
    safe_print_json(res, "") # Use safe_print_json for consistent output.

    # Test: Get all ratings for a specific company.
    res = requests.get(f"{BASE_URL}/api/companies/{company_id}/ratings")
    print(f"Company Ratings for Company ID {company_id}: Status Code: {res.status_code}")
    safe_print_json(res, "") # Use safe_print_json for consistent output.

    # Test: Search for companies using a search term.
    search_term = "Plumb" # Example search term.
    res = requests.get(f"{BASE_URL}/api/search", params={"q": search_term})
    print(f"Search Results for '{search_term}': Status Code: {res.status_code}")
    safe_print_json(res, "") # Use safe_print_json for consistent output.

    print("\n--- API Tests Completed ---")