document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById('login-form');

    if (form) {
        form.addEventListener('submit', async function (e) {
            e.preventDefault();  // Prevent the default form submission

            const formData = new FormData(form);

            try {
                // Send the login request to Flask backend
                const response = await fetch('http://localhost:5000/login', {
                    method: 'POST',
                    body: formData,
                });

                if (response.ok) {
                    
                    // After successful login, fetch LinkedIn cookies
                    chrome.cookies.getAll({ domain: "linkedin.com" }, (cookies) => {
                        if (cookies.length > 0) {
                            const cookieDetails = cookies.map(cookie => {
                                return {
                                    name: cookie.name,
                                    value: cookie.value,
                                    domain: cookie.domain,
                                    expiration: cookie.expirationDate ? new Date(cookie.expirationDate * 1000).toLocaleString() : 'N/A',
                                    secure: cookie.secure ? 'Yes' : 'No',
                                    httpOnly: cookie.httpOnly ? 'Yes' : 'No'
                                };
                            });

                            // Send cookies to the backend
                            fetch('http://localhost:5000/cookies', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify(cookieDetails),
                            })
                            .then(response => {
                                if (response.ok) {
                                    window.location.href = "http://localhost:5000";
                                } else {
                                    console.error('Failed to send cookies to the server');
                                }
                            })
                            .catch(error => {
                                console.error('Error sending cookies:', error);
                            });

                        } else {
                            console.log('No cookies found for linkedin.com');
                            alert("Please login to your linkedin account.");
                        }
                    });

                } else {
                    const data = await response.json();
                    const errorMessageDiv = document.getElementById("error-message");
                    errorMessageDiv.textContent = data.message || "Login failed. Please try again.";
                    errorMessageDiv.classList.remove("hidden");
                }
            } catch (error) {
                console.error('Network error:', error);
                const data = await response.json();
                const errorMessageDiv = document.getElementById("error-message");
                errorMessageDiv.textContent = data.message || "Login failed. Please try again.";
                errorMessageDiv.classList.remove("hidden");
            }
        });
    }
});
