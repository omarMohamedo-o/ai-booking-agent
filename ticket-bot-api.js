class TicketBotApi {
    constructor(baseUrl = 'http://localhost:5000') {
        this.apiBase = baseUrl;
    }

    async startBot(config) {
        const response = await fetch(`${this.apiBase}/api/bot/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config)
        });
        return await response.json();
    }

    async getBotStatus(botId) {
        const response = await fetch(`${this.apiBase}/api/bot/status/${botId}`);
        return await response.json();
    }

    async stopBot(botId) {
        const response = await fetch(`${this.apiBase}/api/bot/stop/${botId}`, {
            method: 'POST'
        });
        return await response.json();
    }
}

// Example usage in your existing interface
const botApi = new TicketBotApi();

// Modify your existing setup button click handler
setupBotBtn.addEventListener('click', async () => {
    const userName = document.getElementById('userName').value;
    const userEmail = document.getElementById('userEmail').value;
    const userPhone = document.getElementById('userPhone').value;
    const eventUrl = document.getElementById('eventUrl').value;
    const releaseTime = document.getElementById('ticketReleaseTime').value;
    const ticketCount = parseInt(document.getElementById('ticketCount').value);
    
    const config = {
        user_info: {
            name: userName,
            email: userEmail,
            phone: userPhone
        },
        event_url: eventUrl,
        release_time: releaseTime,
        ticket_count: ticketCount,
        llm_api_key: 'YOUR_GEMINI_API_KEY'  // Replace with your actual API key
    };
    
    const result = await botApi.startBot(config);
    if (result.bot_id) {
        // Start polling for status updates
        startStatusPolling(result.bot_id);
    }
});

let pollingInterval;
function startStatusPolling(botId) {
    pollingInterval = setInterval(async () => {
        const status = await botApi.getBotStatus(botId);
        updateUIWithStatus(status);
        
        if (!status.is_active || status.booked_tickets >= status.target_tickets) {
            clearInterval(pollingInterval);
        }
    }, 2000);
}

function updateUIWithStatus(status) {
    // Update your interface with the current status
    if (status.error) {
        addLog(`Error: ${status.error}`);
    } else {
        addLog(`Status: Booked ${status.booked_tickets}/${status.target_tickets} tickets`);
        // Update other UI elements as needed
    }
}