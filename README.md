# 🎫 AI-Powered Ticket Booking Agent

An intelligent, automated ticket booking system that uses AI/LLM capabilities to handle dynamic website interactions, solve CAPTCHAs, and automatically book tickets from various websites.

## ✨ Features

- **🤖 AI-Powered Web Interaction**: Uses LLM APIs (OpenAI, Anthropic, Google Gemini) to intelligently navigate websites and fill forms
- **🔍 CAPTCHA Solving**: Advanced CAPTCHA detection and solving using vision-capable AI models
- **🌐 Multi-Website Support**: Modular design that can be configured for different ticketing websites
- **📧 Email Notifications**: Automatic email confirmations with booking details and receipts
- **🔄 Retry Logic**: Intelligent retry mechanisms with exponential backoff
- **🛡️ Anti-Detection**: Stealth browsing features to avoid detection by anti-bot systems
- **📊 Detailed Reporting**: Comprehensive session reports and booking analytics
- **⚙️ Highly Configurable**: Easy configuration through environment variables

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Chrome or Firefox browser
- Email account with app password (for Gmail, Yahoo, etc.)
- API key for at least one LLM provider (OpenAI, Anthropic, or Google)

### Installation

1. **Clone or download the project**:
   ```bash
   git clone <your-repo-url>
   cd ai-ticket-booking-agent
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.template .env
   # Edit .env with your actual configuration
   ```

4. **Run the agent**:
   ```bash
   python -m src.ticket_booking_agent
   ```

## ⚙️ Configuration

### Environment Variables (.env file)

```bash
# Email Configuration
USER_EMAIL=your-email@example.com
EMAIL_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Target Website Configuration
TARGET_WEBSITE_URL=https://example-tickets.com
TICKET_COUNT=10

# LLM API Configuration (Choose one)
OPENAI_API_KEY=your-openai-api-key-here
# ANTHROPIC_API_KEY=your-anthropic-api-key-here
# GEMINI_API_KEY=your-gemini-api-key-here

# User Information for Booking
USER_NAME=John Doe
USER_PHONE=+1234567890
USER_ADDRESS=123 Main St, City, State, ZIP

# Bot Configuration
MAX_ATTEMPTS=20
RETRY_INTERVAL=5
HEADLESS_BROWSER=true
BROWSER_TIMEOUT=30
```

### Email Setup

#### Gmail Setup
1. Enable 2-factor authentication
2. Generate an app password: [Google App Passwords](https://support.google.com/accounts/answer/185833)
3. Use the app password in `EMAIL_PASSWORD`

#### Other Email Providers
- **Yahoo**: Use app password
- **Outlook**: Use app password or OAuth (app password recommended)
- **Custom SMTP**: Configure `SMTP_SERVER` and `SMTP_PORT`

### LLM API Setup

#### OpenAI (Recommended)
1. Sign up at [OpenAI](https://platform.openai.com/)
2. Create an API key
3. Set `OPENAI_API_KEY` in your .env file

#### Anthropic Claude
1. Sign up at [Anthropic](https://console.anthropic.com/)
2. Create an API key
3. Set `ANTHROPIC_API_KEY` in your .env file

#### Google Gemini
1. Get API key from [Google AI Studio](https://makersuite.google.com/)
2. Set `GEMINI_API_KEY` in your .env file

## 🏗️ Architecture

The system consists of four main components:

### 1. LLM Agent (`src/llm_agent.py`)
- Analyzes webpage content
- Generates form data
- Solves CAPTCHAs using vision models
- Handles dynamic content changes
- Supports multiple LLM providers

### 2. Web Scraper (`src/web_scraper.py`)
- Selenium-based browser automation
- Anti-detection features
- Form filling and submission
- CAPTCHA handling integration
- Retry logic with intelligent delays

### 3. Email Sender (`src/email_sender.py`)
- HTML and text email generation
- Booking confirmation emails
- Failure notifications
- Status updates
- Attachment support (receipts, summaries)

### 4. Main Agent (`src/ticket_booking_agent.py`)
- Orchestrates all components
- Configuration management
- Session tracking
- Error handling
- Reporting and analytics

## 🔧 Usage Examples

### Basic Usage

```python
from src.ticket_booking_agent import TicketBookingAgent, AgentConfig

# Load configuration from .env file
config = AgentConfig.from_env()

# Create and run agent
agent = TicketBookingAgent(config)

# Validate configuration
issues = agent.validate_configuration()
if issues:
    print("Configuration issues:", issues)
    exit(1)

# Test email setup
if not agent.test_email_configuration():
    print("Email configuration failed")
    exit(1)

# Start booking process
agent.start_booking(async_mode=False)
```

### Advanced Usage

```python
from src.ticket_booking_agent import TicketBookingAgent, AgentConfig

# Create custom configuration
config = AgentConfig(
    target_website_url="https://tickets.example.com",
    ticket_count=5,
    user_name="John Doe",
    user_email="john@example.com",
    email_password="app-password",
    openai_api_key="sk-...",
    headless_browser=False,  # Show browser for debugging
    debug_mode=True
)

agent = TicketBookingAgent(config)

# Start booking in background
agent.start_booking(async_mode=True)

# Monitor progress
import time
while agent.is_running:
    status = agent.get_booking_status()
    print(f"Progress: {status['progress_percentage']:.1f}%")
    time.sleep(10)

# Get final results
final_status = agent.get_booking_status()
print(f"Booked {final_status['total_tickets_booked']} tickets")
```

### Programmatic Integration

```python
from src.web_scraper import WebScraper
from src.llm_agent import LLMAgent
from src.email_sender import EmailSender

# Use components individually
llm = LLMAgent(provider="openai", api_key="sk-...")
email = EmailSender({"user_email": "user@example.com", "email_password": "pass"})

with WebScraper(config, llm) as scraper:
    results = scraper.book_tickets(
        "https://tickets.example.com",
        {"name": "John", "email": "john@example.com"},
        5
    )
    
    if any(r.success for r in results):
        email.send_booking_confirmation([r.__dict__ for r in results])
```

## 🛡️ Security Considerations

### API Keys
- Never commit API keys to version control
- Use environment variables or secure secret management
- Rotate API keys regularly
- Monitor API usage and costs

### Browser Security
- Use headless mode in production
- Consider using proxy services for additional anonymity
- Implement rate limiting to avoid triggering anti-bot measures
- Use random delays between actions

### Email Security
- Use app passwords instead of main account passwords
- Enable 2FA on email accounts
- Consider using dedicated email account for automation

## 🎛️ Advanced Configuration

### Browser Options

```python
# Custom browser configuration
scraper_config = {
    'headless_browser': True,
    'browser_timeout': 60,
    'use_proxy': True,
    'proxy_url': 'http://proxy-server:port',
    'max_attempts': 30,
    'retry_interval': 3
}
```

### LLM Customization

```python
# Custom LLM prompts and settings
llm = LLMAgent("openai", api_key="sk-...")

# Custom webpage analysis
analysis = llm.analyze_webpage(
    html_content, 
    url, 
    "find VIP ticket booking section"
)

# Custom form data generation
form_data = llm.generate_form_data(
    ["first_name", "last_name", "email", "vip_level"],
    user_info,
    ticket_count
)
```

### Email Templates

```python
# Custom email configuration
email_config = {
    'user_email': 'noreply@yourcompany.com',
    'email_password': 'app-password',
    'smtp_server': 'smtp.yourcompany.com',
    'smtp_port': 465,
    'use_ssl': True,
    'use_tls': False
}

email_sender = EmailSender(email_config)
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Browser Not Starting
```bash
# Install Chrome/Chromium
sudo apt-get install chromium-browser  # Ubuntu/Debian
brew install chromium  # macOS

# Or install ChromeDriver manually
```

#### 2. CAPTCHA Solving Fails
- Ensure you're using a vision-capable model (Gemini Pro Vision)
- Check API quotas and limits
- Some CAPTCHAs may be unsolvable by AI

#### 3. Email Sending Fails
- Verify SMTP settings
- Check if 2FA is enabled and app password is used
- Test with `agent.test_email_configuration()`

#### 4. Website Changes Not Detected
- Websites frequently change their structure
- LLM analysis helps adapt to changes
- May need manual selector updates for specific sites

### Debug Mode

Enable debug mode for detailed logging:

```bash
DEBUG_MODE=true
```

This will:
- Show browser window (non-headless)
- Enable verbose logging
- Save screenshots on errors
- Provide detailed error messages

### Log Analysis

Check the log file for detailed information:

```bash
tail -f ticket_booking_agent.log
```

Common log patterns:
- `INFO` - Normal operation
- `WARNING` - Recoverable issues
- `ERROR` - Failed operations
- `DEBUG` - Detailed execution info

## 📊 Monitoring and Analytics

### Session Reports

The agent automatically generates detailed session reports:

```json
{
  "session_info": {
    "start_time": "2024-01-15T10:30:00",
    "end_time": "2024-01-15T10:45:00",
    "runtime_seconds": 900,
    "target_website": "https://tickets.example.com",
    "target_ticket_count": 10
  },
  "results": {
    "total_attempts": 15,
    "successful_bookings": 8,
    "total_tickets_booked": 8,
    "success_rate": 0.8
  },
  "booking_details": [...]
}
```

### Email Notifications

You'll receive emails for:
- ✅ Successful bookings with confirmation numbers
- ❌ Booking failures with error details
- 🔄 Status updates during long processes
- 📊 Final session summaries

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Follow the existing code style
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install pytest black flake8

# Run tests
pytest

# Format code
black src/

# Check code style
flake8 src/
```

## ⚖️ Legal and Ethical Considerations

### Important Disclaimers

- **Compliance**: Ensure your use complies with website terms of service
- **Rate Limiting**: Respect website resources and implement appropriate delays
- **Personal Use**: This tool is intended for personal use and learning
- **No Warranty**: Use at your own risk; no guarantees of booking success

### Best Practices

1. **Respect robots.txt**: Check website's robots.txt file
2. **Reasonable Delays**: Don't overwhelm servers with rapid requests
3. **Terms of Service**: Read and comply with website terms
4. **Fair Use**: Don't use for scalping or commercial ticket reselling

## 📄 License

This project is provided for educational and personal use. Please ensure compliance with all applicable laws and website terms of service.

## 🆘 Support

For issues and questions:

1. Check the troubleshooting section
2. Review log files for error details
3. Verify your configuration
4. Test individual components

---

**⚠️ Disclaimer**: This tool is for educational purposes. Users are responsible for ensuring their use complies with website terms of service and applicable laws. The authors are not responsible for any misuse or violations.