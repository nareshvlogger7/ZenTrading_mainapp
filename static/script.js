document.getElementById('stopLossForm').addEventListener('submit', function(e) {
    e.preventDefault();  // Prevent the default form submission behavior

    // Get the stop-loss value from the form input
    const stopLossValue = document.getElementById('stopLoss').value;

    // Send the stop-loss value to the backend using a POST request
    fetch('/set_stop_loss', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'stopLoss': stopLossValue
        })
    })
    .then(response => response.json())
    .then(data => {
        // Update the response message on the frontend
        document.getElementById('responseMessage').innerText = data.message || data.error;
    })
    .catch(error => {
        // Handle errors by displaying an error message
        document.getElementById('responseMessage').innerText = 'Error setting stop loss';
    });
});
