// ----------------------------------------------------Logout------------------------------------
document.addEventListener("DOMContentLoaded", function () {
    const logoutButton = document.getElementById('logout');

    if (logoutButton) {
        logoutButton.addEventListener('click', async (e) => {
            e.preventDefault();

            try {
                const response = await fetch('/logout', {
                    method: 'GET',
                });

                if (response.ok) {
                    console.log('Logout successful');
                    window.location.href = window.location.href; 
                } else {
                    console.error('Logout failed');
                }
            } catch (error) {
                console.error('Error during logout:', error);
            }
        });
    }
});

// ------------------------------------------------------Send message button--------------------------------------------

document.addEventListener('DOMContentLoaded', function () {
    const sendButton = document.getElementById('sendButton');
    const cancelButton = document.getElementById('cancelButton');    

    // Add event listeners for the buttons
    if (sendButton) {
        sendButton.addEventListener('click', hideMessageDialog);
    }

    if (cancelButton) {
        cancelButton.addEventListener('click', hideMessageDialog);
    }
});

// Function to show the dialog
function showMessageDialog() {
    const dialog = document.getElementById('messageDialog');
    dialog.classList.remove('hidden'); // Make it visible
    dialog.classList.add('flex', 'opacity-0', 'transition-opacity', 'duration-300'); // Prepare it for the fade-in transition
    setTimeout(() => {
        dialog.classList.remove('opacity-0'); // Make it fully opaque
        dialog.classList.add('opacity-100');
    }, 10); // Small delay for the transition effect
}

// Function to hide the dialog
function hideMessageDialog() {
    const dialog = document.getElementById('messageDialog');
    dialog.classList.add('opacity-0'); // Start the fade-out transition
    setTimeout(() => {
        dialog.classList.add('hidden'); // Hide the dialog after the transition
        dialog.classList.remove('flex', 'opacity-0', 'transition-opacity', 'duration-300'); // Clean up transition classes
    }, 300); // Wait for the duration of the fade-out transition (300ms)
}

// Show loading modal function
function showLoadingModal() {
  console.log("showLoadingModal called");
    const loadingModal = document.getElementById('loadingModal');
    loadingModal.style.display='flex';
    loadingModal.style.opacity=1
    loadingModal.classList.add('show');
}

// Hide loading modal function
function hideLoadingModal() {
    const loadingModal = document.getElementById('loadingModal');
    console.log("hideLoadingModal called");
    loadingModal.style.opacity=0
    loadingModal.style.style='none'
    loadingModal.classList.remove('show');
}


// ------------------------------------------------------batch message button--------------------------------------------
document.addEventListener("DOMContentLoaded", function () {
    const automateButton = document.getElementById('automateButton');
    const messageDialog = document.getElementById('messageDialog');
    const sendButton = document.getElementById('sendButton');
    const cancelButton = document.getElementById('cancelButton');
    const messageText = document.getElementById('messageText');
    const subjectText = document.getElementById('subjectText');
    const loadingModal = document.getElementById('loadingModal');
    const logContainer = document.getElementById('logContainer'); // Ensure this element exists in the DOM

    let sendButtonClicked = false; // Flag to prevent multiple clicks on Send

    // Show the message dialog
    function showMessageDialog() {
        messageDialog.style.display = 'flex';
        messageDialog.classList.add('show');
        logContainer.innerHTML = ''; // Clear logs when dialog is shown
    }

    // Hide the message dialog
    function hideMessageDialog() {
        messageDialog.classList.remove('show');
        setTimeout(() => {
            messageDialog.style.display = 'none';
        }, 300);
    }

    // Show the loading modal
    function showLoadingModal() {
        loadingModal.style.display = 'block';
    }

    // Hide the loading modal
    function hideLoadingModal() {
        loadingModal.style.display = 'none';
    }

    // Update the log container with the latest log
    function updateLog(message) {
        logContainer.innerHTML = ''; // Clear previous log
        const logEntry = document.createElement('p');
        logEntry.textContent = message;
        logContainer.appendChild(logEntry);
    }

    // Automate button click handler
    if (automateButton) {
        automateButton.addEventListener('click', (e) => {
            e.preventDefault();

            const checkboxes = document.querySelectorAll(".user-checkbox:checked");
            const selectedProfileUrls = Array.from(checkboxes).map((checkbox) =>
                checkbox.getAttribute('data-user-id')
            );

            if (selectedProfileUrls.length > 0) {
                showMessageDialog();
            } else {
                alert("Please select at least one profile.");
            }
        });
    }

    // Cancel button click handler
    if (cancelButton) {
        cancelButton.addEventListener('click', hideMessageDialog);
    }

    // Send button click handler
    if (sendButton) {
        sendButton.addEventListener('click', async (e) => {
            e.preventDefault();

            if (sendButtonClicked) return;
            sendButtonClicked = true;

            const message = messageText.value.trim();
            const subject = subjectText.value.trim();

            if (!subject || !message) {
                alert("Please enter both a subject and a message.");
                sendButtonClicked = false;
                return;
            }

            const checkboxes = document.querySelectorAll(".user-checkbox:checked");
            const selectedProfileUrls = Array.from(checkboxes).map((checkbox) =>
                checkbox.getAttribute('data-user-id')
            );

            if (selectedProfileUrls.length === 0) {
                alert("Please select at least one profile.");
                sendButtonClicked = false;
                return;
            }

            const data = {
                subject,
                message,
                profileUrls: selectedProfileUrls,
            };

            try {
                hideMessageDialog();
                showLoadingModal();

                // Start streaming logs
                const eventSource = new EventSource('/stream-logs');

                eventSource.onmessage = function (event) {
                    updateLog(event.data);
                    if (event.data === "done") {
                        eventSource.close(); // Close the log stream when done
                        hideLoadingModal();
                    }
                };

                // Make the POST request to send the message
                const response = await fetch('/send-message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data),
                });

                const result = await response.json();

                if (response.ok) {
                    alert(result.success || 'Messages sent successfully.');
                    window.location.reload(); // Refresh the page to update the state
                } else {
                    alert(result.error || 'An error occurred while sending the messages.');
                }
            } catch (error) {
                console.error('Error during the request:', error);
                alert("An error occurred. Please login to your LinkedIn account and try again.");
            } finally {
                sendButtonClicked = false;
                hideLoadingModal(); // Ensure the loading modal is hidden in case of failure
            }
        });
    }
});
