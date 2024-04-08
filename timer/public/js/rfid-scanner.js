document.addEventListener('DOMContentLoaded', function() {
    const rfidInput = document.getElementById('rfidtag');

    // Function to simulate RFID scanning (replace with actual scanning logic)
    function scanRFID() {
        // Simulated RFID tag - replace with actual RFID reading logic
        const simulatedRFID = 'CCFFFF20051000-3400E200470BFEA06821E2B00115-BC0D';
        rfidInput.value = simulatedRFID;
    }

    // Simulate an RFID scan on page load
    scanRFID();
});
