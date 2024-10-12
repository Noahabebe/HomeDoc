// Toggle privacy
document.getElementById('toggle-privacy').addEventListener('click', function() {
    fetch('/toggle_privacy', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
        .then(response => response.json())
        .then(data => alert('Privacy is now ' + (data.privacy ? 'ON' : 'OFF')));
});

// Check privacy status before messaging
document.querySelectorAll('.message-btn').forEach(button => {
    button.addEventListener('click', function() {
        const recipient = this.getAttribute('data-recipient');

        fetch('/check_privacy_status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sender: '', recipient: recipient }) // Replace 'YourUsername' dynamically
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'unlocked') {
                // Redirect to real messaging page
                window.location.href = '/message/' + recipient;
            } else {
                alert('Privacy is still enabled. Anonymous messaging will be used.');
                window.location.href = '/message/' + data.details.id; // Redirect using anonymous ID
            }
        });
    });
});

// Enable video call when privacy is off
document.querySelectorAll('.video-call-btn').forEach(button => {
    button.addEventListener('click', function() {
        const recipient = this.getAttribute('data-recipient');

        fetch('/start_video_call', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sender: 'YourUsername', recipient: recipient })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.location.href = '/video_call/' + recipient;
            } else {
                alert('Both parties must disable privacy for the video call.');
            }
        });
    });
});
