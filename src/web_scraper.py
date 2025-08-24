"""
Web Scraping Module for Ticket Booking Agent

This module handles all web scraping and browser automation tasks using Selenium.
It includes intelligent form filling, CAPTCHA handling, and retry mechanisms.
"""

import os
import time
import logging
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, ElementClickInterceptedException,
    ElementNotInteractableException, StaleElementReferenceException
)
from selenium.webdriver.common.action_chains import ActionChains

try:
    import undetected_chromedriver as uc
except ImportError:
    uc = None

from fake_useragent import UserAgent
from bs4 import BeautifulSoup

from .llm_agent import LLMAgent


@dataclass
class BookingResult:
    """Result of a ticket booking attempt"""
    success: bool
    tickets_booked: int
    confirmation_number: str = ""
    error_message: str = ""
    booking_details: Dict[str, Any] = None
    total_cost: float = 0.0


class WebScraper:
    """Advanced web scraper for ticket booking with AI assistance"""
    
    def __init__(self, config: Dict[str, Any], llm_agent: LLMAgent = None):
        self.config = config
        self.llm_agent = llm_agent
        self.logger = logging.getLogger(__name__)
        
        # Browser settings
        self.headless = config.get('headless_browser', True)
        self.timeout = config.get('browser_timeout', 30)
        self.user_agent = UserAgent()
        
        # Retry settings
        self.max_retries = config.get('max_attempts', 20)
        self.retry_delay = config.get('retry_interval', 5)
        
        # Browser instance
        self.driver = None
        self.wait = None
        
        # Booking state
        self.booking_attempts = 0
        self.successful_bookings = 0
        
    def __enter__(self):
        self.start_browser()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_browser()
    
    def start_browser(self, browser_type: str = "chrome") -> None:
        """Initialize browser with optimal settings for ticket booking"""
        try:
            if browser_type.lower() == "chrome":
                self.driver = self._setup_chrome()
            elif browser_type.lower() == "firefox":
                self.driver = self._setup_firefox()
            else:
                raise ValueError(f"Unsupported browser: {browser_type}")
                
            self.wait = WebDriverWait(self.driver, self.timeout)
            self.logger.info("Browser started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start browser: {e}")
            raise
    
    def _setup_chrome(self) -> webdriver.Chrome:
        """Setup Chrome browser with anti-detection features"""
        options = ChromeOptions()
        
        if self.headless:
            options.add_argument("--headless")
            
        # Anti-detection arguments
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument(f"--user-agent={self.user_agent.random}")
        
        # Performance optimizations
        options.add_argument("--disable-images")
        options.add_argument("--disable-javascript")  # Can be enabled if needed
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-extensions")
        
        # Use undetected chromedriver if available
        if uc:
            driver = uc.Chrome(options=options)
        else:
            driver = webdriver.Chrome(options=options)
            
        # Remove automation indicators
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def _setup_firefox(self) -> webdriver.Firefox:
        """Setup Firefox browser"""
        options = FirefoxOptions()
        
        if self.headless:
            options.add_argument("--headless")
            
        options.set_preference("general.useragent.override", self.user_agent.random)
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        
        return webdriver.Firefox(options=options)
    
    def close_browser(self) -> None:
        """Close browser and cleanup"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Browser closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing browser: {e}")
    
    def book_tickets(self, website_url: str, user_info: Dict[str, str], 
                    ticket_count: int) -> List[BookingResult]:
        """
        Main method to book tickets from a website
        
        Args:
            website_url: Target website URL
            user_info: User information for booking
            ticket_count: Number of tickets to book
            
        Returns:
            List of booking results
        """
        results = []
        remaining_tickets = ticket_count
        
        while remaining_tickets > 0 and self.booking_attempts < self.max_retries:
            self.booking_attempts += 1
            self.logger.info(f"Booking attempt {self.booking_attempts}/{self.max_retries}")
            
            try:
                # Load the website
                self.driver.get(website_url)
                self._wait_for_page_load()
                
                # Analyze page with LLM if available
                page_analysis = self._analyze_current_page(website_url)
                
                # Handle different page types
                if self._is_ticket_page():
                    result = self._attempt_booking(user_info, min(remaining_tickets, 4))
                    results.append(result)
                    
                    if result.success:
                        remaining_tickets -= result.tickets_booked
                        self.successful_bookings += result.tickets_booked
                        self.logger.info(f"Successfully booked {result.tickets_booked} tickets")
                    else:
                        self.logger.warning(f"Booking failed: {result.error_message}")
                        
                elif self._needs_navigation():
                    self._navigate_to_booking_page(page_analysis)
                    
                else:
                    self.logger.error("Unable to identify page type or find booking interface")
                    break
                    
            except Exception as e:
                self.logger.error(f"Booking attempt failed: {e}")
                results.append(BookingResult(
                    success=False,
                    tickets_booked=0,
                    error_message=str(e)
                ))
                
            # Wait before retry
            if remaining_tickets > 0:
                self._random_delay()
                
        return results
    
    def _analyze_current_page(self, url: str) -> Dict[str, Any]:
        """Analyze current page content using LLM"""
        if not self.llm_agent:
            return {}
            
        try:
            html_content = self.driver.page_source
            return self.llm_agent.analyze_webpage(
                html_content, url, "find ticket booking elements"
            )
        except Exception as e:
            self.logger.error(f"Page analysis failed: {e}")
            return {}
    
    def _is_ticket_page(self) -> bool:
        """Check if current page has ticket booking functionality"""
        ticket_indicators = [
            "ticket", "book", "purchase", "buy", "order", "reserve",
            "quantity", "seats", "checkout", "cart"
        ]
        
        page_text = self.driver.page_source.lower()
        return any(indicator in page_text for indicator in ticket_indicators)
    
    def _needs_navigation(self) -> bool:
        """Check if we need to navigate to a different page"""
        # Look for navigation links or buttons
        nav_elements = self.driver.find_elements(By.CSS_SELECTOR, 
            "a[href*='ticket'], a[href*='book'], button[onclick*='ticket']")
        return len(nav_elements) > 0
    
    def _navigate_to_booking_page(self, page_analysis: Dict[str, Any]) -> bool:
        """Navigate to the actual booking page"""
        try:
            # Use LLM analysis if available
            if page_analysis and "next_steps" in page_analysis:
                for step in page_analysis["next_steps"]:
                    if "click" in step.lower():
                        # Extract selector and click
                        pass
                        
            # Fallback: look for common booking links
            booking_selectors = [
                "a[href*='ticket']", "a[href*='book']", "a[href*='buy']",
                "button[onclick*='book']", ".book-now", ".buy-tickets",
                "[data-action*='book']"
            ]
            
            for selector in booking_selectors:
                try:
                    element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    self._safe_click(element)
                    self._wait_for_page_load()
                    return True
                except TimeoutException:
                    continue
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            return False
    
    def _attempt_booking(self, user_info: Dict[str, str], ticket_count: int) -> BookingResult:
        """Attempt to book tickets on current page"""
        try:
            # Find and fill booking form
            form_data = self._extract_form_fields()
            if not form_data:
                return BookingResult(
                    success=False,
                    tickets_booked=0,
                    error_message="No booking form found"
                )
            
            # Fill form with user data
            filled_data = self._fill_booking_form(form_data, user_info, ticket_count)
            
            # Handle CAPTCHA if present
            captcha_solved = self._handle_captcha()
            if not captcha_solved:
                return BookingResult(
                    success=False,
                    tickets_booked=0,
                    error_message="CAPTCHA solving failed"
                )
            
            # Submit form
            success = self._submit_booking_form()
            
            if success:
                # Extract confirmation details
                confirmation = self._extract_confirmation_details()
                return BookingResult(
                    success=True,
                    tickets_booked=ticket_count,
                    confirmation_number=confirmation.get("number", ""),
                    booking_details=confirmation,
                    total_cost=confirmation.get("total_cost", 0.0)
                )
            else:
                return BookingResult(
                    success=False,
                    tickets_booked=0,
                    error_message="Form submission failed"
                )
                
        except Exception as e:
            return BookingResult(
                success=False,
                tickets_booked=0,
                error_message=f"Booking error: {str(e)}"
            )
    
    def _extract_form_fields(self) -> Dict[str, Any]:
        """Extract form fields from the current page"""
        try:
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            if not forms:
                return {}
                
            form = forms[0]  # Use first form
            fields = {}
            
            # Find input fields
            inputs = form.find_elements(By.TAG_NAME, "input")
            for input_elem in inputs:
                field_type = input_elem.get_attribute("type")
                field_name = input_elem.get_attribute("name") or input_elem.get_attribute("id")
                if field_name and field_type not in ["submit", "button", "hidden"]:
                    fields[field_name] = {
                        "type": field_type,
                        "element": input_elem,
                        "required": input_elem.get_attribute("required") is not None
                    }
            
            # Find select fields
            selects = form.find_elements(By.TAG_NAME, "select")
            for select_elem in selects:
                field_name = select_elem.get_attribute("name") or select_elem.get_attribute("id")
                if field_name:
                    fields[field_name] = {
                        "type": "select",
                        "element": select_elem,
                        "options": [opt.get_attribute("value") for opt in 
                                  select_elem.find_elements(By.TAG_NAME, "option")]
                    }
            
            return fields
            
        except Exception as e:
            self.logger.error(f"Form extraction failed: {e}")
            return {}
    
    def _fill_booking_form(self, form_data: Dict[str, Any], user_info: Dict[str, str], 
                          ticket_count: int) -> Dict[str, str]:
        """Fill booking form with provided data"""
        filled_data = {}
        
        try:
            # Use LLM to generate appropriate form data
            if self.llm_agent:
                field_names = list(form_data.keys())
                generated_data = self.llm_agent.generate_form_data(
                    field_names, user_info, ticket_count
                )
            else:
                generated_data = self._fallback_form_data(form_data, user_info, ticket_count)
            
            # Fill each field
            for field_name, field_info in form_data.items():
                try:
                    element = field_info["element"]
                    value = generated_data.get(field_name, "")
                    
                    if field_info["type"] == "select":
                        select = Select(element)
                        # Try to select by value or text
                        try:
                            select.select_by_value(value)
                        except:
                            select.select_by_visible_text(value)
                    else:
                        element.clear()
                        element.send_keys(value)
                        
                    filled_data[field_name] = value
                    
                except Exception as e:
                    self.logger.warning(f"Failed to fill field {field_name}: {e}")
                    
            return filled_data
            
        except Exception as e:
            self.logger.error(f"Form filling failed: {e}")
            return {}
    
    def _fallback_form_data(self, form_data: Dict[str, Any], user_info: Dict[str, str], 
                           ticket_count: int) -> Dict[str, str]:
        """Generate form data without LLM assistance"""
        data = {}
        
        for field_name in form_data.keys():
            field_lower = field_name.lower()
            
            if any(keyword in field_lower for keyword in ["name", "first", "last"]):
                data[field_name] = user_info.get("name", "John Doe")
            elif "email" in field_lower:
                data[field_name] = user_info.get("email", "user@example.com")
            elif "phone" in field_lower:
                data[field_name] = user_info.get("phone", "+1234567890")
            elif any(keyword in field_lower for keyword in ["quantity", "ticket", "count"]):
                data[field_name] = str(ticket_count)
            elif "address" in field_lower:
                data[field_name] = user_info.get("address", "123 Main St")
            else:
                data[field_name] = ""
                
        return data
    
    def _handle_captcha(self) -> bool:
        """Handle CAPTCHA if present"""
        try:
            # Look for CAPTCHA elements
            captcha_selectors = [
                "img[src*='captcha']", ".captcha", "#captcha",
                "canvas[width]", "[data-captcha]"
            ]
            
            captcha_element = None
            for selector in captcha_selectors:
                try:
                    captcha_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not captcha_element:
                return True  # No CAPTCHA present
                
            if not self.llm_agent:
                self.logger.warning("CAPTCHA found but no LLM agent available")
                return False
                
            # Save CAPTCHA image
            captcha_path = "/tmp/captcha.png"
            captcha_element.screenshot(captcha_path)
            
            # Solve CAPTCHA
            solution = self.llm_agent.solve_captcha(captcha_path)
            
            if solution:
                # Find CAPTCHA input field
                captcha_input = self.driver.find_element(By.CSS_SELECTOR, 
                    "input[name*='captcha'], input[id*='captcha']")
                captcha_input.clear()
                captcha_input.send_keys(solution)
                
                self.logger.info("CAPTCHA solved and entered")
                return True
            else:
                self.logger.warning("CAPTCHA solving failed")
                return False
                
        except Exception as e:
            self.logger.error(f"CAPTCHA handling failed: {e}")
            return False
    
    def _submit_booking_form(self) -> bool:
        """Submit the booking form"""
        try:
            # Find submit button
            submit_selectors = [
                "input[type='submit']", "button[type='submit']",
                ".submit", ".book-now", ".purchase", ".buy",
                "button[onclick*='submit']"
            ]
            
            for selector in submit_selectors:
                try:
                    submit_btn = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    self._safe_click(submit_btn)
                    
                    # Wait for submission to complete
                    time.sleep(3)
                    
                    # Check if submission was successful
                    return self._verify_submission_success()
                    
                except TimeoutException:
                    continue
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Form submission failed: {e}")
            return False
    
    def _verify_submission_success(self) -> bool:
        """Verify if form submission was successful"""
        success_indicators = [
            "confirmation", "success", "booked", "purchased",
            "thank you", "order number", "ticket number"
        ]
        
        page_text = self.driver.page_source.lower()
        return any(indicator in page_text for indicator in success_indicators)
    
    def _extract_confirmation_details(self) -> Dict[str, Any]:
        """Extract booking confirmation details from the page"""
        try:
            page_text = self.driver.page_source
            soup = BeautifulSoup(page_text, 'html.parser')
            
            details = {}
            
            # Look for confirmation number
            conf_patterns = [
                r"confirmation\s*(?:number|#)?\s*:?\s*([A-Z0-9]+)",
                r"order\s*(?:number|#)?\s*:?\s*([A-Z0-9]+)",
                r"booking\s*(?:reference|#)?\s*:?\s*([A-Z0-9]+)"
            ]
            
            import re
            for pattern in conf_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    details["number"] = match.group(1)
                    break
            
            # Look for total cost
            cost_patterns = [
                r"total\s*:?\s*\$?([0-9]+\.?[0-9]*)",
                r"amount\s*:?\s*\$?([0-9]+\.?[0-9]*)"
            ]
            
            for pattern in cost_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    details["total_cost"] = float(match.group(1))
                    break
            
            # Get full page content for email
            details["full_content"] = soup.get_text()
            
            return details
            
        except Exception as e:
            self.logger.error(f"Confirmation extraction failed: {e}")
            return {}
    
    def _safe_click(self, element) -> bool:
        """Safely click an element with retry logic"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)
                
                # Try regular click first
                element.click()
                return True
                
            except (ElementClickInterceptedException, ElementNotInteractableException):
                # Try JavaScript click
                try:
                    self.driver.execute_script("arguments[0].click();", element)
                    return True
                except Exception:
                    if attempt == max_attempts - 1:
                        return False
                    time.sleep(1)
                    
            except StaleElementReferenceException:
                # Element is stale, need to re-find it
                return False
                
        return False
    
    def _wait_for_page_load(self, timeout: int = None) -> None:
        """Wait for page to fully load"""
        timeout = timeout or self.timeout
        
        # Wait for document ready state
        WebDriverWait(self.driver, timeout).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        
        # Additional small delay for dynamic content
        time.sleep(2)
    
    def _random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
        """Add random delay to appear more human-like"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def get_booking_summary(self) -> Dict[str, Any]:
        """Get summary of all booking attempts"""
        return {
            "total_attempts": self.booking_attempts,
            "successful_bookings": self.successful_bookings,
            "success_rate": self.successful_bookings / max(1, self.booking_attempts),
            "timestamp": time.time()
        }