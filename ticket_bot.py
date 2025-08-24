import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

class TicketBot:
    def __init__(self, config: Dict):
        """
        Initialize the ticket booking bot
        
        Args:
            config: Dictionary containing configuration
                   (user_info, event_url, ticket_count, etc.)
        """
        self.config = config
        self.user_info = config.get('user_info', {})
        self.event_url = config.get('event_url')
        self.ticket_count = config.get('ticket_count', 10)
        self.release_time = datetime.strptime(
            config['release_time'], '%Y-%m-%dT%H:%M'
        )
        self.retry_interval = config.get('retry_interval', 5)  # seconds
        self.max_attempts = config.get('max_attempts', 20)
        self.attempt_count = 0
        self.booked_tickets = 0
        self.is_active = False
        self.proxy = config.get('proxy')
        
        # LLM configuration (using Gemini API as example)
        self.llm_api_key = config.get('llm_api_key')
        self.llm_api_url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'
        
        # Initialize session
        self.session = requests.Session()
        if self.proxy:
            self.session.proxies = {'http': self.proxy, 'https': self.proxy}

    def start_booking_process(self):
        """Start the automated booking process"""
        self.is_active = True
        threading.Thread(target=self._monitor_ticket_release).start()

    def _monitor_ticket_release(self):
        """Monitor ticket release and trigger booking"""
        # Calculate wait time until release
        now = datetime.now()
        if now < self.release_time:
            wait_seconds = (self.release_time - now).total_seconds()
            logging.info(f"Waiting {wait_seconds} seconds until ticket release")
            time.sleep(wait_seconds)
        
        logging.info("Starting ticket booking attempts...")
        while self.is_active and self.attempt_count < self.max_attempts:
            self._attempt_booking()
            time.sleep(self.retry_interval)
        
        if self.booked_tickets >= self.ticket_count:
            logging.info(f"Successfully booked {self.booked_tickets} tickets")
        else:
            logging.warning(f"Only booked {self.booked_tickets}/{self.ticket_count} tickets")

    def _attempt_booking(self):
        """Attempt to book tickets"""
        self.attempt_count += 1
        logging.info(f"Booking attempt {self.attempt_count}")
        
        try:
            # Step 1: Check ticket availability (simulated)
            available = self._check_availability()
            if not available:
                logging.info("Tickets not available yet, retrying...")
                return False
            
            # Step 2: Generate booking form content with LLM assistance
            booking_data = self._generate_booking_data()
            
            # Step 3: Submit booking request (simulated)
            success = self._submit_booking(booking_data)
            
            if success:
                self.booked_tickets += min(2, self.ticket_count - self.booked_tickets)
                logging.info(f"Booked {self.booked_tickets}/{self.ticket_count} tickets")
            else:
                logging.info("Booking failed, retrying...")
            
            return success
            
        except Exception as e:
            logging.error(f"Booking attempt failed: {str(e)}")
            return False

    def _check_availability(self) -> bool:
        """Check ticket availability (simulate API call)"""
        # In a real implementation, this would make an API call to check availability
        time.sleep(0.5)  # Simulate API delay
        return True  # Simulate tickets being available

    def _generate_booking_data(self) -> Dict:
        """Generate booking data using LLM assistance"""
        prompt = f"""
        Generate a ticket booking form submission for:
        - Event URL: {self.event_url}
        - User: {self.user_info.get('name')}
        - Email: {self.user_info.get('email')}
        - Phone: {self.user_info.get('phone')}
        - Tickets: {min(2, self.ticket_count - self.booked_tickets)}  # Book max 2 at a time
        
        Return ONLY a JSON object with form field names and values, nothing else.
        """
        
        try:
            response = self._query_llm(prompt)
            booking_data = json.loads(response)
            return booking_data
        except Exception as e:
            logging.error(f"LLM booking generation failed: {str(e)}")
            # Fallback to default data
            return {
                'name': self.user_info.get('name'),
                'email': self.user_info.get('email'),
                'phone': self.user_info.get('phone'),
                'quantity': min(2, self.ticket_count - self.booked_tickets)
            }

    def _query_llm(self, prompt: str) -> str:
        """Query the LLM API"""
        if not self.llm_api_key:
            raise ValueError("LLM API key not configured")
            
        headers = {
            'Content-Type': 'application/json',
        }
        
        params = {
            'key': self.llm_api_key
        }
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        try:
            response = requests.post(
                self.llm_api_url,
                params=params,
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            content = response.json()
            return content['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            logging.error(f"LLM API request failed: {str(e)}")
            raise

    def _submit_booking(self, booking_data: Dict) -> bool:
        """Submit booking request (simulate API call)"""
        # In real implementation, this would submit to actual ticketing API
        time.sleep(1.5)  # Simulate API delay
        
        # Success rate simulation
        success_rate = 0.8 if self.booked_tickets == 0 else 0.6
        return True if (time.time() % 100) < (100 * success_rate) else False

    def stop_booking(self):
        """Stop the booking process"""
        self.is_active = False
        logging.info("Booking process stopped")