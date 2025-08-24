"""
AI/LLM Integration Module for Ticket Booking Agent

This module provides LLM integration for handling dynamic website interactions,
CAPTCHA solving, form filling, and intelligent decision making.
"""

import os
import base64
import logging
from typing import Dict, List, Optional, Union, Any
from enum import Enum
import json
import time

# LLM API clients
try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from PIL import Image
import io


class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class LLMAgent:
    """AI-powered agent for handling complex web interactions"""
    
    def __init__(self, provider: str = "openai", api_key: str = None):
        self.provider = LLMProvider(provider.lower())
        self.api_key = api_key or self._get_api_key()
        self.client = self._initialize_client()
        self.logger = logging.getLogger(__name__)
        
    def _get_api_key(self) -> str:
        """Get API key based on provider"""
        key_map = {
            LLMProvider.OPENAI: "OPENAI_API_KEY",
            LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            LLMProvider.GEMINI: "GEMINI_API_KEY"
        }
        return os.getenv(key_map[self.provider])
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        if not self.api_key:
            raise ValueError(f"API key not found for {self.provider.value}")
            
        if self.provider == LLMProvider.OPENAI:
            if not openai:
                raise ImportError("OpenAI package not installed")
            return openai.OpenAI(api_key=self.api_key)
            
        elif self.provider == LLMProvider.ANTHROPIC:
            if not anthropic:
                raise ImportError("Anthropic package not installed")
            return anthropic.Anthropic(api_key=self.api_key)
            
        elif self.provider == LLMProvider.GEMINI:
            if not genai:
                raise ImportError("Google Generative AI package not installed")
            genai.configure(api_key=self.api_key)
            return genai.GenerativeModel('gemini-pro-vision')
            
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def analyze_webpage(self, html_content: str, url: str, task: str) -> Dict[str, Any]:
        """
        Analyze webpage content and provide instructions for ticket booking
        
        Args:
            html_content: Raw HTML content of the page
            url: URL of the page
            task: Specific task to accomplish (e.g., "find ticket booking form")
            
        Returns:
            Dictionary with analysis results and recommended actions
        """
        prompt = f"""
        Analyze this webpage for ticket booking. 
        URL: {url}
        Task: {task}
        
        HTML Content (truncated):
        {html_content[:5000]}...
        
        Please provide a JSON response with:
        1. "form_selectors": CSS selectors for booking form elements
        2. "ticket_elements": Selectors for ticket quantity/type elements
        3. "submit_button": Selector for the submit button
        4. "required_fields": List of required form fields
        5. "captcha_present": Boolean indicating if CAPTCHA is detected
        6. "next_steps": Array of actions to take
        7. "warnings": Any potential issues or obstacles
        
        Return ONLY valid JSON, no other text.
        """
        
        try:
            response = self._query_llm(prompt)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Webpage analysis failed: {e}")
            return self._fallback_analysis()
    
    def solve_captcha(self, captcha_image: Union[str, bytes, Image.Image]) -> str:
        """
        Attempt to solve CAPTCHA using vision-capable LLM
        
        Args:
            captcha_image: CAPTCHA image as file path, bytes, or PIL Image
            
        Returns:
            Predicted CAPTCHA solution
        """
        if self.provider != LLMProvider.GEMINI:
            self.logger.warning("CAPTCHA solving requires vision model (Gemini)")
            return ""
            
        try:
            # Convert image to PIL format if needed
            if isinstance(captcha_image, str):
                image = Image.open(captcha_image)
            elif isinstance(captcha_image, bytes):
                image = Image.open(io.BytesIO(captcha_image))
            else:
                image = captcha_image
                
            prompt = """
            Please solve this CAPTCHA image. Look carefully at the text or numbers 
            shown in the image and provide only the solution text, nothing else.
            If it's a mathematical expression, provide the calculated result.
            If it's distorted text, provide the clean text.
            """
            
            response = self.client.generate_content([prompt, image])
            solution = response.text.strip()
            
            self.logger.info(f"CAPTCHA solution generated: {solution}")
            return solution
            
        except Exception as e:
            self.logger.error(f"CAPTCHA solving failed: {e}")
            return ""
    
    def generate_form_data(self, form_fields: List[str], user_info: Dict[str, str], 
                          ticket_count: int) -> Dict[str, str]:
        """
        Generate appropriate form data for ticket booking
        
        Args:
            form_fields: List of form field names/IDs
            user_info: User information dictionary
            ticket_count: Number of tickets to book
            
        Returns:
            Dictionary mapping form fields to values
        """
        prompt = f"""
        Generate form data for ticket booking based on these fields:
        Form fields: {form_fields}
        
        User information:
        - Name: {user_info.get('name', '')}
        - Email: {user_info.get('email', '')}
        - Phone: {user_info.get('phone', '')}
        - Address: {user_info.get('address', '')}
        
        Ticket count: {ticket_count}
        
        Please provide a JSON mapping of form field names to appropriate values.
        Use common field naming patterns to match fields to user data.
        For unknown fields, provide reasonable default values.
        
        Return ONLY valid JSON, no other text.
        """
        
        try:
            response = self._query_llm(prompt)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Form data generation failed: {e}")
            return self._fallback_form_data(form_fields, user_info, ticket_count)
    
    def handle_dynamic_content(self, page_content: str, previous_action: str, 
                             error_message: str = None) -> Dict[str, Any]:
        """
        Handle dynamic page content changes and determine next actions
        
        Args:
            page_content: Current page HTML content
            previous_action: Description of the last action taken
            error_message: Any error message encountered
            
        Returns:
            Dictionary with recommended next actions
        """
        prompt = f"""
        The webpage has changed after performing this action: {previous_action}
        
        Current page content (truncated):
        {page_content[:3000]}...
        
        {f"Error encountered: {error_message}" if error_message else ""}
        
        Please analyze the current state and provide JSON response with:
        1. "status": "success", "error", or "waiting"
        2. "next_action": Specific action to take next
        3. "wait_time": Seconds to wait if status is "waiting"
        4. "selectors": Any new CSS selectors to use
        5. "form_data": Any form data to submit
        6. "error_resolution": Steps to resolve any errors
        
        Return ONLY valid JSON, no other text.
        """
        
        try:
            response = self._query_llm(prompt)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Dynamic content handling failed: {e}")
            return {"status": "error", "next_action": "retry", "wait_time": 5}
    
    def _query_llm(self, prompt: str, max_tokens: int = 1000) -> str:
        """Send query to the configured LLM provider"""
        try:
            if self.provider == LLMProvider.OPENAI:
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.1
                )
                return response.choices[0].message.content
                
            elif self.provider == LLMProvider.ANTHROPIC:
                response = self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=max_tokens,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
                
            elif self.provider == LLMProvider.GEMINI:
                response = self.client.generate_content(prompt)
                return response.text
                
        except Exception as e:
            self.logger.error(f"LLM query failed: {e}")
            raise
    
    def _fallback_analysis(self) -> Dict[str, Any]:
        """Fallback analysis when LLM fails"""
        return {
            "form_selectors": ["form", "input[type='submit']"],
            "ticket_elements": ["select[name*='quantity']", "input[name*='tickets']"],
            "submit_button": "input[type='submit'], button[type='submit']",
            "required_fields": ["name", "email", "phone"],
            "captcha_present": False,
            "next_steps": ["fill_form", "submit"],
            "warnings": ["LLM analysis failed - using fallback"]
        }
    
    def _fallback_form_data(self, form_fields: List[str], user_info: Dict[str, str], 
                           ticket_count: int) -> Dict[str, str]:
        """Fallback form data generation"""
        data = {}
        for field in form_fields:
            field_lower = field.lower()
            if 'name' in field_lower:
                data[field] = user_info.get('name', 'John Doe')
            elif 'email' in field_lower:
                data[field] = user_info.get('email', 'user@example.com')
            elif 'phone' in field_lower:
                data[field] = user_info.get('phone', '+1234567890')
            elif 'quantity' in field_lower or 'ticket' in field_lower:
                data[field] = str(ticket_count)
            else:
                data[field] = ""
        return data


class CaptchaSolver:
    """Specialized CAPTCHA solving utilities"""
    
    def __init__(self, llm_agent: LLMAgent):
        self.llm_agent = llm_agent
        self.logger = logging.getLogger(__name__)
    
    def solve_text_captcha(self, image_path: str) -> str:
        """Solve text-based CAPTCHA"""
        return self.llm_agent.solve_captcha(image_path)
    
    def solve_math_captcha(self, image_path: str) -> str:
        """Solve mathematical CAPTCHA"""
        solution = self.llm_agent.solve_captcha(image_path)
        # Additional processing for math problems
        try:
            # If it's a simple math expression, evaluate it
            if any(op in solution for op in ['+', '-', '*', '/', '=']):
                # Extract the math part and evaluate
                import re
                math_match = re.search(r'(\d+[\+\-\*/]\d+)', solution)
                if math_match:
                    expression = math_match.group(1)
                    result = eval(expression)  # Note: eval is dangerous in production
                    return str(result)
        except:
            pass
        return solution
    
    def detect_captcha_type(self, image_path: str) -> str:
        """Detect the type of CAPTCHA"""
        # This could be enhanced with image analysis
        return "text"  # Default to text type