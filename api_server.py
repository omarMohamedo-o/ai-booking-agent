import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ticket_demo.log'),
        logging.StreamHandler()
    ]
)

class TicketDemoBot:
    """
    DEMONSTRATION ONLY - This is a simulated ticket booking bot for educational purposes.
    This does NOT actually book real tickets from real websites.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the demo ticket booking bot
        
        Args:
            config: Dictionary containing configuration
        """
        self.config = config
        self.user_info = config.get('user_info', {})
        self.website_url = config.get('website_url')
        self.ticket_count = config.get('ticket_count', 1)
        self.email_config = config.get('email_config', {})
        self.retry_interval = config.get('retry_interval', 2)
        self.max_attempts = config.get('max_attempts', 10)
        self.attempt_count = 0
        self.booked_tickets = 0
        self.is_active = False
        
        # Simulated website data
        self.available_tickets = random.randint(1, 20)
        
        logging.info("Demo Ticket Bot initialized")
        logging.info(f"Target website: {self.website_url}")
        logging.info(f"Requested tickets: {self.ticket_count}")

    def start_demo_booking(self):
        """Start the demo booking process"""
        self.is_active = True
        logging.info("Starting demo ticket booking process...")
        threading.Thread(target=self._demo_booking_process).start()

    def _demo_booking_process(self):
        """Main demo booking process"""
        while self.is_active and self.attempt_count < self.max_attempts:
            if self.booked_tickets >= self.ticket_count:
                break
                
            success = self._attempt_demo_booking()
            if success:
                # Send email notification
                self._send_success_email()
            else:
                time.sleep(self.retry_interval)
        
        # Final status
        if self.booked_tickets >= self.ticket_count:
            logging.info(f"✅ Demo completed! Successfully 'booked' {self.booked_tickets} tickets")
            self._send_final_report()
        else:
            logging.warning(f"❌ Demo ended with only {self.booked_tickets}/{self.ticket_count} tickets")

    def _attempt_demo_booking(self):
        """Simulate a booking attempt"""
        self.attempt_count += 1
        logging.info(f"Demo booking attempt {self.attempt_count}")
        
        try:
            # Step 1: Simulate checking website availability
            if not self._simulate_check_availability():
                logging.info("Simulated: Tickets not available, retrying...")
                return False
            
            # Step 2: Simulate form filling
            booking_data = self._simulate_form_data()
            logging.info(f"Simulated form data: {booking_data}")
            
            # Step 3: Simulate booking submission
            success = self._simulate_booking_submission(booking_data)
            
            if success:
                tickets_to_book = min(2, self.ticket_count - self.booked_tickets)
                self.booked_tickets += tickets_to_book
                self.available_tickets -= tickets_to_book
                logging.info(f"✅ Simulated booking success! Booked {tickets_to_book} tickets")
                return True
            else:
                logging.info("❌ Simulated booking failed")
                return False
            
        except Exception as e:
            logging.error(f"Demo booking attempt error: {str(e)}")
            return False

    def _simulate_check_availability(self) -> bool:
        """Simulate checking ticket availability on website"""
        # Simulate network delay
        time.sleep(random.uniform(0.5, 1.5))
        
        # Simulate availability check
        if self.available_tickets <= 0:
            return False
        
        # Random chance of website being overloaded
        return random.random() > 0.3  # 70% success rate

    def _simulate_form_data(self) -> Dict:
        """Simulate generating form data for booking"""
        return {
            'name': self.user_info.get('name', 'Demo User'),
            'email': self.user_info.get('email', 'demo@example.com'),
            'phone': self.user_info.get('phone', '+1-555-0123'),
            'quantity': min(2, self.ticket_count - self.booked_tickets),
            'event_url': self.website_url,
            'timestamp': datetime.now().isoformat(),
            'user_agent': 'Demo-Bot/1.0'
        }

    def _simulate_booking_submission(self, booking_data: Dict) -> bool:
        """Simulate submitting booking to website"""
        # Simulate form submission delay
        time.sleep(random.uniform(1.0, 3.0))
        
        # Simulate various failure scenarios
        failure_scenarios = [
            (0.2, "Server overload"),
            (0.1, "Payment processing error"),
            (0.1, "Tickets sold out"),
            (0.05, "Network timeout")
        ]
        
        for probability, reason in failure_scenarios:
            if random.random() < probability:
                logging.info(f"Simulated failure: {reason}")
                return False
        
        return True  # Success!

    def _send_success_email(self):
        """Send email notification for successful booking"""
        try:
            subject = f"🎟️ Demo Ticket Booking Success!"
            body = f"""
            Demo Ticket Booking Successful!
            
            Website: {self.website_url}
            Tickets Booked: {self.booked_tickets}/{self.ticket_count}
            Booking Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Attempt Number: {self.attempt_count}
            
            ⚠️ NOTE: This is a DEMONSTRATION only. No real tickets were purchased.
            
            User Details:
            - Name: {self.user_info.get('name', 'Demo User')}
            - Email: {self.user_info.get('email', 'Not provided')}
            - Phone: {self.user_info.get('phone', 'Not provided')}
            
            Happy booking! 🎉
            """
            
            self._send_email(subject, body)
            logging.info("Success email sent!")
            
        except Exception as e:
            logging.error(f"Failed to send success email: {str(e)}")

    def _send_final_report(self):
        """Send final booking report via email"""
        try:
            if self.booked_tickets >= self.ticket_count:
                subject = "✅ Demo Ticket Booking Complete - SUCCESS!"
                status = "COMPLETED SUCCESSFULLY"
                emoji = "🎉"
            else:
                subject = "⚠️ Demo Ticket Booking Complete - PARTIAL"
                status = "PARTIALLY COMPLETED"
                emoji = "⚠️"
            
            body = f"""
            {emoji} Demo Ticket Booking Final Report
            
            Status: {status}
            
            Booking Summary:
            - Target Website: {self.website_url}
            - Requested Tickets: {self.ticket_count}
            - Successfully 'Booked': {self.booked_tickets}
            - Total Attempts: {self.attempt_count}
            - Remaining Available: {self.available_tickets}
            
            User Information:
            - Name: {self.user_info.get('name', 'Demo User')}
            - Email: {self.user_info.get('email', 'Not provided')}
            - Phone: {self.user_info.get('phone', 'Not provided')}
            
            Completion Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            ⚠️ IMPORTANT: This was a DEMONSTRATION only. 
            No real tickets were purchased from any website.
            
            Thank you for testing the demo! 🎟️
            """
            
            self._send_email(subject, body)
            logging.info("Final report email sent!")
            
        except Exception as e:
            logging.error(f"Failed to send final report: {str(e)}")

    def _send_email(self, subject: str, body: str):
        """Send email using configured email settings"""
        email_config = self.email_config
        
        if not email_config.get('smtp_server') or not email_config.get('smtp_port'):
            logging.warning("Email not configured, skipping email send")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = email_config.get('from_email')
            msg['To'] = email_config.get('to_email')
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            if email_config.get('use_tls', True):
                server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(email_config['smtp_server'], email_config['smtp_port'])
            
            # Login if credentials provided
            if email_config.get('username') and email_config.get('password'):
                server.login(email_config['username'], email_config['password'])
            
            # Send email
            text = msg.as_string()
            server.sendmail(email_config['from_email'], email_config['to_email'], text)
            server.quit()
            
        except Exception as e:
            logging.error(f"Email sending failed: {str(e)}")
            # For demo purposes, just log the email content
            logging.info(f"EMAIL CONTENT:\nSubject: {subject}\n\n{body}")

    def stop_booking(self):
        """Stop the booking process"""
        self.is_active = False
        logging.info("Demo booking process stopped")

    def get_status(self) -> Dict:
        """Get current booking status"""
        return {
            'is_active': self.is_active,
            'attempts': self.attempt_count,
            'booked_tickets': self.booked_tickets,
            'target_tickets': self.ticket_count,
            'available_tickets': self.available_tickets
        }


# Example usage and configuration
def create_demo_config():
    """Create a sample configuration for the demo bot"""
    return {
        'user_info': {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '+1-555-0123'
        },
        'website_url': 'https://example-tickets.com/concert',
        'ticket_count': 4,  # Number of tickets to book
        'retry_interval': 2,  # seconds between attempts
        'max_attempts': 15,
        'email_config': {
            'smtp_server': 'smtp.gmail.com',  # For Gmail
            'smtp_port': 587,
            'use_tls': True,
            'from_email': 'your.email@gmail.com',
            'to_email': 'your.email@gmail.com',  # Where to send notifications
            'username': 'your.email@gmail.com',  # For Gmail authentication
            'password': 'your_app_password'  # Gmail app password
        }
    }

if __name__ == "__main__":
    # Demo usage
    print("🎟️ Starting Demo Ticket Booking Bot")
    print("⚠️ This is a DEMONSTRATION only - no real tickets will be purchased!")
    print("=" * 60)
    
    # Create demo configuration
    demo_config = create_demo_config()
    
    # Initialize and start the demo bot
    bot = TicketDemoBot(demo_config)
    bot.start_demo_booking()
    
    # Monitor status (in real usage, this might be in a separate thread/process)
    try:
        while bot.is_active:
            time.sleep(5)
            status = bot.get_status()
            print(f"Status: {status['booked_tickets']}/{status['target_tickets']} tickets, "
                  f"Attempt #{status['attempts']}")
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        bot.stop_booking()
    
    print("Demo completed!")