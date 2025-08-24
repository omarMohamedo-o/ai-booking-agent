"""
Main AI-Powered Ticket Booking Agent

This is the main orchestrator that coordinates all components to automatically
book tickets from websites and send confirmation emails.
"""

import os
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import threading
from pathlib import Path

from dotenv import load_dotenv

from .llm_agent import LLMAgent, LLMProvider
from .web_scraper import WebScraper, BookingResult
from .email_sender import EmailSender


@dataclass
class AgentConfig:
    """Configuration for the ticket booking agent"""
    # Website and booking settings
    target_website_url: str
    ticket_count: int = 10
    max_attempts: int = 20
    retry_interval: int = 5
    
    # User information
    user_name: str = ""
    user_email: str = ""
    user_phone: str = ""
    user_address: str = ""
    
    # Email settings
    email_password: str = ""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    
    # LLM settings
    llm_provider: str = "openai"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    
    # Browser settings
    headless_browser: bool = True
    browser_timeout: int = 30
    use_proxy: bool = False
    proxy_url: str = ""
    
    # Advanced settings
    debug_mode: bool = False
    captcha_solving_service: str = "none"
    
    @classmethod
    def from_env(cls, env_file: str = ".env") -> "AgentConfig":
        """Create configuration from environment variables"""
        load_dotenv(env_file)
        
        def get_env_bool(key: str, default: bool = False) -> bool:
            value = os.getenv(key, str(default)).lower()
            return value in ('true', '1', 'yes', 'on')
        
        def get_env_int(key: str, default: int = 0) -> int:
            try:
                return int(os.getenv(key, str(default)))
            except ValueError:
                return default
        
        return cls(
            target_website_url=os.getenv("TARGET_WEBSITE_URL", ""),
            ticket_count=get_env_int("TICKET_COUNT", 10),
            max_attempts=get_env_int("MAX_ATTEMPTS", 20),
            retry_interval=get_env_int("RETRY_INTERVAL", 5),
            
            user_name=os.getenv("USER_NAME", ""),
            user_email=os.getenv("USER_EMAIL", ""),
            user_phone=os.getenv("USER_PHONE", ""),
            user_address=os.getenv("USER_ADDRESS", ""),
            
            email_password=os.getenv("EMAIL_PASSWORD", ""),
            smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            smtp_port=get_env_int("SMTP_PORT", 587),
            
            llm_provider=os.getenv("LLM_PROVIDER", "openai").lower(),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            
            headless_browser=get_env_bool("HEADLESS_BROWSER", True),
            browser_timeout=get_env_int("BROWSER_TIMEOUT", 30),
            use_proxy=get_env_bool("USE_PROXY", False),
            proxy_url=os.getenv("PROXY_URL", ""),
            
            debug_mode=get_env_bool("DEBUG_MODE", False),
            captcha_solving_service=os.getenv("CAPTCHA_SOLVING_SERVICE", "none"),
        )


class TicketBookingAgent:
    """Main AI-powered ticket booking agent"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = self._setup_logging()
        
        # Initialize components
        self.llm_agent = self._initialize_llm_agent()
        self.email_sender = self._initialize_email_sender()
        
        # Booking state
        self.is_running = False
        self.booking_results: List[BookingResult] = []
        self.total_tickets_booked = 0
        self.start_time: Optional[datetime] = None
        
        # Thread for background operations
        self.booking_thread: Optional[threading.Thread] = None
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_level = logging.DEBUG if self.config.debug_mode else logging.INFO
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ticket_booking_agent.log'),
                logging.StreamHandler()
            ]
        )
        
        logger = logging.getLogger(__name__)
        logger.info("Ticket Booking Agent initialized")
        return logger
    
    def _initialize_llm_agent(self) -> Optional[LLMAgent]:
        """Initialize LLM agent based on configuration"""
        try:
            provider = self.config.llm_provider
            api_key = None
            
            if provider == "openai":
                api_key = self.config.openai_api_key
            elif provider == "anthropic":
                api_key = self.config.anthropic_api_key
            elif provider == "gemini":
                api_key = self.config.gemini_api_key
            
            if not api_key:
                self.logger.warning(f"No API key found for {provider}, LLM features disabled")
                return None
                
            return LLMAgent(provider=provider, api_key=api_key)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM agent: {e}")
            return None
    
    def _initialize_email_sender(self) -> EmailSender:
        """Initialize email sender"""
        email_config = {
            'user_email': self.config.user_email,
            'email_password': self.config.email_password,
            'smtp_server': self.config.smtp_server,
            'smtp_port': self.config.smtp_port,
        }
        return EmailSender(email_config)
    
    def validate_configuration(self) -> List[str]:
        """Validate agent configuration and return list of issues"""
        issues = []
        
        # Required fields
        if not self.config.target_website_url:
            issues.append("Target website URL is required")
        
        if not self.config.user_email:
            issues.append("User email is required")
            
        if not self.config.email_password:
            issues.append("Email password is required")
        
        if not self.config.user_name:
            issues.append("User name is recommended for booking")
        
        # LLM API key check
        if self.config.llm_provider == "openai" and not self.config.openai_api_key:
            issues.append("OpenAI API key is required for selected provider")
        elif self.config.llm_provider == "anthropic" and not self.config.anthropic_api_key:
            issues.append("Anthropic API key is required for selected provider")
        elif self.config.llm_provider == "gemini" and not self.config.gemini_api_key:
            issues.append("Gemini API key is required for selected provider")
        
        # Validate ticket count
        if self.config.ticket_count <= 0:
            issues.append("Ticket count must be greater than 0")
        elif self.config.ticket_count > 50:
            issues.append("Ticket count should not exceed 50 for practical reasons")
        
        return issues
    
    def test_email_configuration(self) -> bool:
        """Test email configuration"""
        try:
            self.logger.info("Testing email configuration...")
            return self.email_sender.test_email_config()
        except Exception as e:
            self.logger.error(f"Email configuration test failed: {e}")
            return False
    
    def start_booking(self, async_mode: bool = True) -> bool:
        """
        Start the ticket booking process
        
        Args:
            async_mode: If True, run booking in background thread
            
        Returns:
            True if booking started successfully, False otherwise
        """
        # Validate configuration
        issues = self.validate_configuration()
        if issues:
            self.logger.error("Configuration validation failed:")
            for issue in issues:
                self.logger.error(f"  - {issue}")
            return False
        
        if self.is_running:
            self.logger.warning("Booking process is already running")
            return False
        
        self.logger.info("Starting ticket booking process...")
        self.start_time = datetime.now()
        self.is_running = True
        self.booking_results = []
        self.total_tickets_booked = 0
        
        if async_mode:
            self.booking_thread = threading.Thread(target=self._run_booking_process)
            self.booking_thread.start()
            return True
        else:
            return self._run_booking_process()
    
    def stop_booking(self) -> None:
        """Stop the booking process"""
        if self.is_running:
            self.logger.info("Stopping booking process...")
            self.is_running = False
            
            if self.booking_thread and self.booking_thread.is_alive():
                self.booking_thread.join(timeout=10)
    
    def get_booking_status(self) -> Dict[str, Any]:
        """Get current booking status"""
        runtime = None
        if self.start_time:
            runtime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "is_running": self.is_running,
            "total_attempts": len(self.booking_results),
            "successful_bookings": len([r for r in self.booking_results if r.success]),
            "total_tickets_booked": self.total_tickets_booked,
            "target_ticket_count": self.config.ticket_count,
            "progress_percentage": min(100, (self.total_tickets_booked / self.config.ticket_count) * 100),
            "runtime_seconds": runtime,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_attempt_time": datetime.now().isoformat() if self.booking_results else None
        }
    
    def _run_booking_process(self) -> bool:
        """Run the main booking process"""
        try:
            self.logger.info(f"Attempting to book {self.config.ticket_count} tickets from {self.config.target_website_url}")
            
            # Send status update email
            self._send_status_update("Booking Started", {
                "target_website": self.config.target_website_url,
                "ticket_count": self.config.ticket_count,
                "start_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            # Create web scraper and start booking
            with WebScraper(self._get_scraper_config(), self.llm_agent) as scraper:
                user_info = {
                    "name": self.config.user_name,
                    "email": self.config.user_email,
                    "phone": self.config.user_phone,
                    "address": self.config.user_address
                }
                
                # Book tickets
                results = scraper.book_tickets(
                    self.config.target_website_url,
                    user_info,
                    self.config.ticket_count
                )
                
                self.booking_results.extend(results)
                self.total_tickets_booked = sum(r.tickets_booked for r in results)
                
                # Send completion email
                if results:
                    success = any(r.success for r in results)
                    if success:
                        self._send_booking_confirmation(results)
                    else:
                        self._send_failure_notification()
                else:
                    self._send_failure_notification()
                    
                self.logger.info(f"Booking process completed. Total tickets booked: {self.total_tickets_booked}")
                return True
                
        except Exception as e:
            self.logger.error(f"Booking process failed: {e}")
            self._send_failure_notification(str(e))
            return False
        finally:
            self.is_running = False
    
    def _get_scraper_config(self) -> Dict[str, Any]:
        """Get configuration for web scraper"""
        return {
            'headless_browser': self.config.headless_browser,
            'browser_timeout': self.config.browser_timeout,
            'max_attempts': self.config.max_attempts,
            'retry_interval': self.config.retry_interval,
            'use_proxy': self.config.use_proxy,
            'proxy_url': self.config.proxy_url,
        }
    
    def _send_booking_confirmation(self, results: List[BookingResult]) -> None:
        """Send booking confirmation email"""
        try:
            # Convert BookingResult dataclasses to dictionaries
            results_dict = [asdict(result) for result in results]
            self.email_sender.send_booking_confirmation(results_dict)
        except Exception as e:
            self.logger.error(f"Failed to send booking confirmation: {e}")
    
    def _send_failure_notification(self, error_message: str = None) -> None:
        """Send booking failure notification"""
        try:
            error_details = {
                "website_url": self.config.target_website_url,
                "ticket_count": self.config.ticket_count,
                "total_attempts": len(self.booking_results),
                "error_message": error_message or "Booking process failed",
                "runtime_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            }
            self.email_sender.send_booking_failure_notification(error_details)
        except Exception as e:
            self.logger.error(f"Failed to send failure notification: {e}")
    
    def _send_status_update(self, status: str, details: Dict[str, Any]) -> None:
        """Send booking status update"""
        try:
            self.email_sender.send_booking_status_update(status, details)
        except Exception as e:
            self.logger.error(f"Failed to send status update: {e}")
    
    def save_session_report(self, file_path: str = None) -> str:
        """Save detailed session report to file"""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"booking_session_{timestamp}.json"
        
        report = {
            "session_info": {
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": datetime.now().isoformat(),
                "runtime_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
                "target_website": self.config.target_website_url,
                "target_ticket_count": self.config.ticket_count
            },
            "configuration": asdict(self.config),
            "results": {
                "total_attempts": len(self.booking_results),
                "successful_bookings": len([r for r in self.booking_results if r.success]),
                "total_tickets_booked": self.total_tickets_booked,
                "success_rate": self.total_tickets_booked / self.config.ticket_count if self.config.ticket_count > 0 else 0
            },
            "booking_details": [asdict(result) for result in self.booking_results]
        }
        
        try:
            with open(file_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"Session report saved to {file_path}")
            return file_path
        except Exception as e:
            self.logger.error(f"Failed to save session report: {e}")
            return ""


def main():
    """Main entry point for the ticket booking agent"""
    print("🎫 AI-Powered Ticket Booking Agent")
    print("=" * 50)
    
    # Load configuration
    try:
        config = AgentConfig.from_env()
        print(f"Target website: {config.target_website_url}")
        print(f"Tickets to book: {config.ticket_count}")
        print(f"User email: {config.user_email}")
        print()
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        print("Please check your .env file and try again.")
        return
    
    # Create and validate agent
    agent = TicketBookingAgent(config)
    
    issues = agent.validate_configuration()
    if issues:
        print("❌ Configuration validation failed:")
        for issue in issues:
            print(f"   - {issue}")
        print("\nPlease fix these issues and try again.")
        return
    
    # Test email configuration
    print("📧 Testing email configuration...")
    if agent.test_email_configuration():
        print("✅ Email configuration test passed")
    else:
        print("❌ Email configuration test failed")
        return
    
    # Start booking process
    print("\n🚀 Starting ticket booking process...")
    print("Press Ctrl+C to stop the process at any time.\n")
    
    try:
        success = agent.start_booking(async_mode=False)
        
        if success:
            status = agent.get_booking_status()
            print(f"\n📊 Booking Summary:")
            print(f"   Total attempts: {status['total_attempts']}")
            print(f"   Successful bookings: {status['successful_bookings']}")
            print(f"   Tickets booked: {status['total_tickets_booked']}/{config.ticket_count}")
            print(f"   Success rate: {status['progress_percentage']:.1f}%")
            
            # Save session report
            report_file = agent.save_session_report()
            if report_file:
                print(f"   Session report: {report_file}")
            
            print(f"\n📧 Confirmation email sent to {config.user_email}")
        else:
            print("❌ Booking process failed to start")
            
    except KeyboardInterrupt:
        print("\n⏹️  Booking process interrupted by user")
        agent.stop_booking()
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        agent.stop_booking()


if __name__ == "__main__":
    main()