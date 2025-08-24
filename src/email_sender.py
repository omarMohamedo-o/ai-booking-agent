"""
Email Module for Ticket Booking Agent

This module handles sending booking confirmation emails with ticket details,
receipts, and other important information to users.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import tempfile


class EmailSender:
    """Email sender for ticket booking confirmations and notifications"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # SMTP configuration
        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.sender_email = config.get('user_email')
        self.sender_password = config.get('email_password')
        
        # Email settings
        self.use_tls = config.get('use_tls', True)
        self.use_ssl = config.get('use_ssl', False)
        
        if not self.sender_email or not self.sender_password:
            raise ValueError("Email credentials not configured")
    
    def send_booking_confirmation(self, booking_results: List[Dict[str, Any]], 
                                 recipient_email: str = None) -> bool:
        """
        Send booking confirmation email with ticket details
        
        Args:
            booking_results: List of booking results from web scraper
            recipient_email: Recipient email (defaults to sender email)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            recipient_email = recipient_email or self.sender_email
            
            # Generate email content
            subject = self._generate_subject(booking_results)
            html_content = self._generate_html_content(booking_results)
            text_content = self._generate_text_content(booking_results)
            
            # Create message
            message = MIMEMultipart('alternative')
            message['From'] = self.sender_email
            message['To'] = recipient_email
            message['Subject'] = subject
            message['Date'] = formatdate(localtime=True)
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Add ticket summary attachment
            self._attach_ticket_summary(message, booking_results)
            
            # Send email
            return self._send_email(message, recipient_email)
            
        except Exception as e:
            self.logger.error(f"Failed to send booking confirmation: {e}")
            return False
    
    def send_booking_failure_notification(self, error_details: Dict[str, Any], 
                                        recipient_email: str = None) -> bool:
        """
        Send notification about booking failure
        
        Args:
            error_details: Details about the booking failure
            recipient_email: Recipient email (defaults to sender email)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            recipient_email = recipient_email or self.sender_email
            
            subject = "❌ Ticket Booking Failed - Action Required"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 20px; border-radius: 5px;">
                    <h2 style="color: #721c24; margin-top: 0;">🚫 Ticket Booking Failed</h2>
                    
                    <p>Unfortunately, the automated ticket booking attempt was unsuccessful.</p>
                    
                    <h3>Failure Details:</h3>
                    <ul>
                        <li><strong>Target Website:</strong> {error_details.get('website_url', 'N/A')}</li>
                        <li><strong>Requested Tickets:</strong> {error_details.get('ticket_count', 'N/A')}</li>
                        <li><strong>Total Attempts:</strong> {error_details.get('total_attempts', 'N/A')}</li>
                        <li><strong>Error Message:</strong> {error_details.get('error_message', 'Unknown error')}</li>
                        <li><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                    </ul>
                    
                    <h3>Recommended Actions:</h3>
                    <ol>
                        <li>Check if the website is accessible and tickets are available</li>
                        <li>Verify your user information and payment details</li>
                        <li>Try booking manually or run the agent again later</li>
                        <li>Check the agent logs for more detailed error information</li>
                    </ol>
                    
                    <p style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; color: #666;">
                        This is an automated message from your AI Ticket Booking Agent.
                    </p>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            TICKET BOOKING FAILED
            
            Unfortunately, the automated ticket booking attempt was unsuccessful.
            
            Failure Details:
            - Target Website: {error_details.get('website_url', 'N/A')}
            - Requested Tickets: {error_details.get('ticket_count', 'N/A')}
            - Total Attempts: {error_details.get('total_attempts', 'N/A')}
            - Error Message: {error_details.get('error_message', 'Unknown error')}
            - Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Recommended Actions:
            1. Check if the website is accessible and tickets are available
            2. Verify your user information and payment details
            3. Try booking manually or run the agent again later
            4. Check the agent logs for more detailed error information
            
            This is an automated message from your AI Ticket Booking Agent.
            """
            
            message = MIMEMultipart('alternative')
            message['From'] = self.sender_email
            message['To'] = recipient_email
            message['Subject'] = subject
            message['Date'] = formatdate(localtime=True)
            
            message.attach(MIMEText(text_content, 'plain'))
            message.attach(MIMEText(html_content, 'html'))
            
            return self._send_email(message, recipient_email)
            
        except Exception as e:
            self.logger.error(f"Failed to send failure notification: {e}")
            return False
    
    def send_booking_status_update(self, status: str, details: Dict[str, Any], 
                                  recipient_email: str = None) -> bool:
        """
        Send booking status update (e.g., "In Progress", "Waiting for Release")
        
        Args:
            status: Current status of booking process
            details: Additional details about the status
            recipient_email: Recipient email (defaults to sender email)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            recipient_email = recipient_email or self.sender_email
            
            subject = f"🔄 Ticket Booking Status: {status}"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; padding: 20px; border-radius: 5px;">
                    <h2 style="color: #0c5460; margin-top: 0;">📊 Booking Status Update</h2>
                    
                    <p><strong>Current Status:</strong> {status}</p>
                    
                    <h3>Details:</h3>
                    <ul>
                        {self._format_details_html(details)}
                    </ul>
                    
                    <p style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; color: #666;">
                        This is an automated status update from your AI Ticket Booking Agent.
                    </p>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            TICKET BOOKING STATUS UPDATE
            
            Current Status: {status}
            
            Details:
            {self._format_details_text(details)}
            
            This is an automated status update from your AI Ticket Booking Agent.
            """
            
            message = MIMEMultipart('alternative')
            message['From'] = self.sender_email
            message['To'] = recipient_email
            message['Subject'] = subject
            message['Date'] = formatdate(localtime=True)
            
            message.attach(MIMEText(text_content, 'plain'))
            message.attach(MIMEText(html_content, 'html'))
            
            return self._send_email(message, recipient_email)
            
        except Exception as e:
            self.logger.error(f"Failed to send status update: {e}")
            return False
    
    def _generate_subject(self, booking_results: List[Dict[str, Any]]) -> str:
        """Generate email subject based on booking results"""
        successful_bookings = sum(1 for result in booking_results if result.get('success', False))
        total_tickets = sum(result.get('tickets_booked', 0) for result in booking_results)
        
        if successful_bookings > 0:
            return f"✅ Ticket Booking Confirmation - {total_tickets} Tickets Booked!"
        else:
            return "❌ Ticket Booking Failed - Please Review"
    
    def _generate_html_content(self, booking_results: List[Dict[str, Any]]) -> str:
        """Generate HTML email content"""
        successful_bookings = [r for r in booking_results if r.get('success', False)]
        failed_bookings = [r for r in booking_results if not r.get('success', False)]
        total_tickets = sum(result.get('tickets_booked', 0) for result in booking_results)
        total_cost = sum(result.get('total_cost', 0) for result in booking_results)
        
        # Success section
        success_html = ""
        if successful_bookings:
            success_html = f"""
            <div style="background-color: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="color: #155724; margin-top: 0;">✅ Successful Bookings</h3>
                <p><strong>Total Tickets Booked:</strong> {total_tickets}</p>
                {f'<p><strong>Total Cost:</strong> ${total_cost:.2f}</p>' if total_cost > 0 else ''}
                
                {self._generate_booking_details_html(successful_bookings)}
            </div>
            """
        
        # Failure section
        failure_html = ""
        if failed_bookings:
            failure_html = f"""
            <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="color: #721c24; margin-top: 0;">❌ Failed Attempts</h3>
                <p>{len(failed_bookings)} booking attempt(s) failed.</p>
                
                <ul>
                {self._generate_failure_details_html(failed_bookings)}
                </ul>
            </div>
            """
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #333; text-align: center;">🎫 Ticket Booking Report</h1>
            
            <p>Here's a summary of your automated ticket booking session:</p>
            
            {success_html}
            {failure_html}
            
            <div style="background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 15px; border-radius: 5px;">
                <h3 style="margin-top: 0;">📋 Session Summary</h3>
                <ul>
                    <li><strong>Total Booking Attempts:</strong> {len(booking_results)}</li>
                    <li><strong>Successful Bookings:</strong> {len(successful_bookings)}</li>
                    <li><strong>Failed Attempts:</strong> {len(failed_bookings)}</li>
                    <li><strong>Session Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                </ul>
            </div>
            
            <p style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; color: #666;">
                This email was automatically generated by your AI Ticket Booking Agent. 
                Please save this email for your records.
            </p>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_text_content(self, booking_results: List[Dict[str, Any]]) -> str:
        """Generate plain text email content"""
        successful_bookings = [r for r in booking_results if r.get('success', False)]
        failed_bookings = [r for r in booking_results if not r.get('success', False)]
        total_tickets = sum(result.get('tickets_booked', 0) for result in booking_results)
        total_cost = sum(result.get('total_cost', 0) for result in booking_results)
        
        content = "TICKET BOOKING REPORT\n"
        content += "=" * 50 + "\n\n"
        
        if successful_bookings:
            content += "✅ SUCCESSFUL BOOKINGS\n"
            content += f"Total Tickets Booked: {total_tickets}\n"
            if total_cost > 0:
                content += f"Total Cost: ${total_cost:.2f}\n"
            content += "\nBooking Details:\n"
            
            for i, booking in enumerate(successful_bookings, 1):
                content += f"\n{i}. Booking #{booking.get('confirmation_number', 'N/A')}\n"
                content += f"   Tickets: {booking.get('tickets_booked', 0)}\n"
                if booking.get('total_cost', 0) > 0:
                    content += f"   Cost: ${booking.get('total_cost', 0):.2f}\n"
            
        if failed_bookings:
            content += "\n\n❌ FAILED ATTEMPTS\n"
            content += f"{len(failed_bookings)} booking attempt(s) failed.\n\n"
            
            for i, booking in enumerate(failed_bookings, 1):
                content += f"{i}. Error: {booking.get('error_message', 'Unknown error')}\n"
        
        content += "\n\n📋 SESSION SUMMARY\n"
        content += f"Total Booking Attempts: {len(booking_results)}\n"
        content += f"Successful Bookings: {len(successful_bookings)}\n"
        content += f"Failed Attempts: {len(failed_bookings)}\n"
        content += f"Session Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        content += "\n" + "=" * 50 + "\n"
        content += "This email was automatically generated by your AI Ticket Booking Agent.\n"
        content += "Please save this email for your records."
        
        return content
    
    def _generate_booking_details_html(self, successful_bookings: List[Dict[str, Any]]) -> str:
        """Generate HTML for successful booking details"""
        if not successful_bookings:
            return ""
            
        html = "<div><h4>Booking Details:</h4><ul>"
        
        for booking in successful_bookings:
            html += f"""
            <li>
                <strong>Confirmation #{booking.get('confirmation_number', 'N/A')}</strong><br>
                Tickets: {booking.get('tickets_booked', 0)}<br>
                {f"Cost: ${booking.get('total_cost', 0):.2f}<br>" if booking.get('total_cost', 0) > 0 else ""}
                {f"Details: {booking.get('booking_details', {}).get('full_content', '')[:200]}..." if booking.get('booking_details') else ""}
            </li>
            """
        
        html += "</ul></div>"
        return html
    
    def _generate_failure_details_html(self, failed_bookings: List[Dict[str, Any]]) -> str:
        """Generate HTML for failed booking details"""
        html = ""
        for booking in failed_bookings:
            html += f"<li>{booking.get('error_message', 'Unknown error')}</li>"
        return html
    
    def _format_details_html(self, details: Dict[str, Any]) -> str:
        """Format details dictionary as HTML list items"""
        html = ""
        for key, value in details.items():
            html += f"<li><strong>{key.replace('_', ' ').title()}:</strong> {value}</li>"
        return html
    
    def _format_details_text(self, details: Dict[str, Any]) -> str:
        """Format details dictionary as text"""
        text = ""
        for key, value in details.items():
            text += f"- {key.replace('_', ' ').title()}: {value}\n"
        return text
    
    def _attach_ticket_summary(self, message: MIMEMultipart, 
                              booking_results: List[Dict[str, Any]]) -> None:
        """Attach ticket summary as JSON file"""
        try:
            # Create summary data
            summary = {
                "booking_session": {
                    "timestamp": datetime.now().isoformat(),
                    "total_attempts": len(booking_results),
                    "successful_bookings": len([r for r in booking_results if r.get('success', False)]),
                    "total_tickets": sum(r.get('tickets_booked', 0) for r in booking_results),
                    "total_cost": sum(r.get('total_cost', 0) for r in booking_results)
                },
                "booking_results": booking_results
            }
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(summary, f, indent=2, default=str)
                temp_file = f.name
            
            # Attach file
            with open(temp_file, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="ticket_booking_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
            )
            
            message.attach(part)
            
            # Clean up temp file
            os.unlink(temp_file)
            
        except Exception as e:
            self.logger.warning(f"Failed to attach summary file: {e}")
    
    def _send_email(self, message: MIMEMultipart, recipient_email: str) -> bool:
        """Send email using SMTP"""
        try:
            # Create SMTP connection
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                if self.use_tls:
                    server.starttls()
            
            # Login and send
            server.login(self.sender_email, self.sender_password)
            server.send_message(message)
            server.quit()
            
            self.logger.info(f"Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return False
    
    def test_email_config(self) -> bool:
        """Test email configuration by sending a test email"""
        try:
            subject = "🧪 Test Email - AI Ticket Booking Agent"
            
            html_content = """
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>✅ Email Configuration Test</h2>
                <p>This is a test email to verify your email configuration is working correctly.</p>
                <p>If you receive this email, your AI Ticket Booking Agent is ready to send notifications!</p>
                <p style="color: #666; margin-top: 20px;">
                    Sent at: {timestamp}
                </p>
            </body>
            </html>
            """.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            text_content = f"""
            EMAIL CONFIGURATION TEST
            
            This is a test email to verify your email configuration is working correctly.
            
            If you receive this email, your AI Ticket Booking Agent is ready to send notifications!
            
            Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            message = MIMEMultipart('alternative')
            message['From'] = self.sender_email
            message['To'] = self.sender_email
            message['Subject'] = subject
            message['Date'] = formatdate(localtime=True)
            
            message.attach(MIMEText(text_content, 'plain'))
            message.attach(MIMEText(html_content, 'html'))
            
            return self._send_email(message, self.sender_email)
            
        except Exception as e:
            self.logger.error(f"Email configuration test failed: {e}")
            return False