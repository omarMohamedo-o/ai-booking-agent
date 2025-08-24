# 🧪 Testing Guide for AI-Powered Ticket Booking Agent

This guide will help you verify that your ticket booking agent is working correctly before using it for actual ticket booking.

## 🚀 Quick Start Testing

### 1. **Environment Setup Test**

First, make sure you have the basic setup:

```bash
# Check Python version (3.8+ required)
python --version

# Install dependencies
pip install -r requirements.txt

# Copy configuration template
cp .env.template .env
```

### 2. **Configure Your .env File**

Edit `.env` with your actual values:

```bash
# REQUIRED - Email settings
USER_EMAIL=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# REQUIRED - Target website
TARGET_WEBSITE_URL=https://example-tickets.com

# REQUIRED - At least one LLM API key
OPENAI_API_KEY=sk-your-key-here
# OR
ANTHROPIC_API_KEY=your-key-here
# OR  
GEMINI_API_KEY=your-key-here

# REQUIRED - User info
USER_NAME=Your Name
USER_PHONE=+1234567890
```

### 3. **Run Basic Tests**

```bash
# Quick test (essential components only)
python test_agent.py

# Full comprehensive test
python test_agent.py --full
```

## 🔍 Detailed Testing Steps

### Step 1: Package Import Test

Verify all required packages are installed:

```python
python -c "
import selenium, requests, dotenv, bs4, PIL
print('✅ All required packages imported successfully')
"
```

**If this fails:**
- Run: `pip install -r requirements.txt`
- For Ubuntu/Debian: `sudo apt-get install chromium-browser`
- For macOS: `brew install chromium`

### Step 2: Configuration Test

```bash
python -c "
from src.ticket_booking_agent import AgentConfig
config = AgentConfig.from_env()
print(f'Target: {config.target_website_url}')
print(f'Email: {config.user_email}')
print('✅ Configuration loaded successfully')
"
```

### Step 3: Email Configuration Test

```python
from src.ticket_booking_agent import TicketBookingAgent, AgentConfig

config = AgentConfig.from_env()
agent = TicketBookingAgent(config)

# This will send a test email
if agent.test_email_configuration():
    print("✅ Email test passed - check your inbox!")
else:
    print("❌ Email test failed")
```

### Step 4: Browser Test

```python
from src.web_scraper import WebScraper

config = {
    'headless_browser': False,  # Set to False to see browser
    'browser_timeout': 30
}

with WebScraper(config) as scraper:
    scraper.driver.get("https://httpbin.org/html")
    print(f"✅ Browser test passed - Title: {scraper.driver.title}")
```

### Step 5: LLM Integration Test

```python
from src.llm_agent import LLMAgent

# Test with your configured provider
llm = LLMAgent(provider="openai", api_key="your-key")
response = llm._query_llm("Say hello", max_tokens=10)
print(f"✅ LLM response: {response}")
```

## 🛠️ Troubleshooting Common Issues

### ❌ **"ModuleNotFoundError: No module named 'selenium'"**

**Solution:**
```bash
pip install -r requirements.txt
```

### ❌ **"selenium.common.exceptions.WebDriverException: 'chromedriver' executable needs to be in PATH"**

**Solutions:**

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install chromium-browser chromium-chromedriver
```

**macOS:**
```bash
brew install chromium
```

**Manual Installation:**
```bash
# Download ChromeDriver from https://chromedriver.chromium.org/
# Add to PATH or place in project directory
```

### ❌ **Email Authentication Failed**

**Solutions:**

**For Gmail:**
1. Enable 2-Factor Authentication
2. Generate App Password: https://support.google.com/accounts/answer/185833
3. Use the app password, not your regular password

**For Other Providers:**
- Yahoo: Enable "Less secure app access" or use app password
- Outlook: Use app password
- Custom SMTP: Verify server settings

### ❌ **LLM API Errors**

**OpenAI:**
```bash
# Check your API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Anthropic:**
```bash
# Verify API key format
echo "API key should start with 'sk-'"
```

**Google Gemini:**
```bash
# Test API key
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

### ❌ **Website Access Issues**

**Check if website is accessible:**
```bash
curl -I https://your-target-website.com
```

**Common solutions:**
- Use VPN if website is geo-blocked
- Check if website has anti-bot protection
- Verify URL is correct and accessible

## 🎯 Test with Safe Websites First

Before using on actual ticket sites, test with safe practice websites:

### Test Configuration:

```bash
# .env for testing
TARGET_WEBSITE_URL=https://httpbin.org/forms/post
TICKET_COUNT=1
```

### Safe Test Sites:

1. **httpbin.org** - HTTP testing service
2. **example.com** - Safe example website
3. **quotes.toscrape.com** - Scraping practice site

## 🚦 Production Readiness Checklist

Before using for real ticket booking:

- [ ] ✅ All tests pass
- [ ] ✅ Email notifications received
- [ ] ✅ Browser automation working
- [ ] ✅ LLM responses are reasonable
- [ ] ✅ Configuration is correct
- [ ] ✅ Target website is accessible
- [ ] ✅ User information is accurate
- [ ] ✅ API quotas are sufficient

## 🔄 Automated Testing

Run the automated test suite:

```bash
# Basic health check
python test_agent.py

# Full comprehensive test
python test_agent.py --full

# Test specific component
python -c "
from src.email_sender import EmailSender
config = {'user_email': 'test@example.com', 'email_password': 'pass'}
emailer = EmailSender(config)
print('✅ Email component works')
"
```

## 📊 Test Results Interpretation

### ✅ **All Tests Pass**
```
🎉 All tests passed! Your agent is ready to use.

🚀 To run the agent:
   python run_agent.py
```

### ⚠️ **Some Tests Fail**
```
⚠️ 2/6 test(s) failed. Please fix the issues before running the agent.

🔧 Common solutions:
   - Install missing packages: pip install -r requirements.txt
   - Configure .env file with your settings
   - Check API keys and email credentials
   - Install Chrome/Chromium browser
```

## 🛡️ Security Testing

### Test with Minimal Permissions:

1. **Test Email Isolation:**
   ```bash
   # Use a dedicated email for testing
   USER_EMAIL=ticketbot+test@gmail.com
   ```

2. **Test API Rate Limits:**
   ```python
   # Check API quotas before heavy usage
   llm = LLMAgent("openai", "your-key")
   for i in range(5):
       response = llm._query_llm("Test query")
       print(f"Request {i}: Success")
   ```

3. **Test Browser Safety:**
   ```python
   # Test with headless mode
   config = {'headless_browser': True}
   # Verify no sensitive data in logs
   ```

## 📈 Performance Testing

### Test Response Times:

```python
import time
from src.ticket_booking_agent import TicketBookingAgent, AgentConfig

config = AgentConfig.from_env()
agent = TicketBookingAgent(config)

start_time = time.time()
# Run component tests
end_time = time.time()

print(f"Total test time: {end_time - start_time:.2f} seconds")
```

### Monitor Resource Usage:

```bash
# Monitor during testing
top -p $(pgrep -f "python.*test_agent")
```

## 🎯 Final Validation

Before production use:

1. **Dry Run Test:**
   ```bash
   # Test everything except actual booking
   TICKET_COUNT=0 python run_agent.py
   ```

2. **Single Ticket Test:**
   ```bash
   # Try booking just 1 ticket first
   TICKET_COUNT=1 python run_agent.py
   ```

3. **Monitor First Run:**
   ```bash
   # Watch logs in real-time
   tail -f ticket_booking_agent.log
   ```

Remember: Always test responsibly and ensure compliance with website terms of service!