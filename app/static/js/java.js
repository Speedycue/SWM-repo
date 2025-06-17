// app/static/js/java.js

// Select the main container for the login/register forms.
// This is the element whose classes will be toggled to switch between forms.
const project = document.querySelector('.project');
// Select the "Register" link that, when clicked, reveals the registration form.
const registerlink = document.querySelector('.register-link');
// Select the "Login" link that, when clicked, reveals the login form.
const loginlink = document.querySelector('.login-link');

// Determine if the current page's 'project' container is specifically for company login/registration.
// This is inferred by checking for the presence of a <select> element with `name="service_id"`
// inside the register form, which is unique to the company registration form.
const isCompanyLoginPage = document.querySelector('.project .form-box.register select[name="service_id"]') !== null;

// Event listener for the "Register" link.
// Ensures both `registerlink` and `project` elements exist on the page before adding the listener.
if (registerlink && project) {
    registerlink.addEventListener('click', (e) => {
        e.preventDefault(); // Prevent the default link behavior (e.g., navigating to '#').
        project.classList.add('active'); // Add the 'active' class to the `.project` container.
                                         // This triggers CSS rules to slide the login form out
                                         // and the register form into view.

        // If it's the company login/register page, add a specific class to the `.project` container.
        // This class (`project-company-register`) is used in CSS to adjust the container's
        // height and width specifically for the larger company registration form.
        if (isCompanyLoginPage) {
            project.classList.add('project-company-register');
        }
    });
}

// Event listener for the "Login" link.
// Ensures both `loginlink` and `project` elements exist on the page before adding the listener.
if (loginlink && project) {
    loginlink.addEventListener('click', (e) => {
        e.preventDefault(); // Prevent default link behavior.
        project.classList.remove('active'); // Remove the 'active' class from the `.project` container.
                                            // This triggers CSS rules to slide the register form out
                                            // and the login form back into view.

        // If it's the company login/register page, remove the specific class.
        // This reverts the container's height and width back to its default login form size.
        if (isCompanyLoginPage) {
            project.classList.remove('project-company-register');
        }
    });
}


// --- NEW: JavaScript for Review Submission (AJAX) ---
// This ensures the script runs only after the entire HTML document has been loaded and parsed.
document.addEventListener('DOMContentLoaded', function() {
    // Select the review submission form by its ID.
    const reviewForm = document.getElementById('reviewForm');
    // Select the div where messages (success/error) related to the review submission will be displayed.
    const reviewMessageDiv = document.getElementById('reviewMessage');

    // Check if the review form exists on the page. It will only exist for logged-in clients
    // on a company's profile page where they can submit a review.
    if (reviewForm) { 
        // Add an event listener for the form's 'submit' event.
        reviewForm.addEventListener('submit', async function(event) {
            event.preventDefault(); // Prevent the browser's default form submission behavior,
                                    // allowing us to handle it via JavaScript (AJAX).

            // Get the company ID from a `data-company-id` attribute on the form element.
            const companyId = this.dataset.companyId;
            // Get the input field for the rating.
            const ratingInput = document.getElementById('rating');
            // Get the textarea for the review content.
            const reviewTextarea = document.getElementById('review');

            // Parse the rating input value as a floating-point number.
            const rating = parseFloat(ratingInput.value);
            // Get the review content, removing any leading/trailing whitespace.
            const reviewContent = reviewTextarea.value.trim();

            // Client-side validation for the rating: check if it's a number and within the valid range (1-5).
            if (isNaN(rating) || rating < 1 || rating > 5) {
                reviewMessageDiv.innerHTML = '<p style="color: red;">Please enter a rating between 1 and 5.</p>';
                return; // Stop the function if validation fails.
            }

            // Display a "submitting" message to the user.
            reviewMessageDiv.innerHTML = '<p style="color: grey;">Submitting review...</p>';

            try {
                // Send an asynchronous POST request to the API endpoint for adding ratings.
                const response = await fetch(`/api/companies/${companyId}/ratings`, {
                    method: 'POST', // Specify HTTP method as POST.
                    headers: {
                        'Content-Type': 'application/json', // Indicate that the request body is JSON.
                    },
                    body: JSON.stringify({ // Convert the JavaScript object to a JSON string for the request body.
                        rating: rating,
                        review: reviewContent 
                    })
                });

                // Parse the JSON response from the server.
                const data = await response.json();

                // Check if the HTTP response status code indicates success (2xx range).
                if (response.ok) {
                    reviewMessageDiv.innerHTML = `<p style="color: green;">${data.message}</p>`;
                    // Clear the form fields after successful submission.
                    ratingInput.value = '';
                    reviewTextarea.value = '';
                    // Reload the page after a short delay to display the newly added review
                    // and the updated average rating (which is recalculated on the server).
                    setTimeout(() => {
                        window.location.reload(); 
                    }, 1500); // Reload after 1.5 seconds.
                } else {
                    // If the response indicates an error, display the error message from the server.
                    reviewMessageDiv.innerHTML = `<p style="color: red;">Error: ${data.error || 'Failed to submit review.'}</p>`;
                }
            } catch (error) {
                // Catch any network errors or issues during the fetch operation.
                console.error('Error submitting review:', error); // Log the detailed error to the console.
                reviewMessageDiv.innerHTML = '<p style="color: red;">An unexpected error occurred. Please try again.</p>';
            }
        });
    }
});