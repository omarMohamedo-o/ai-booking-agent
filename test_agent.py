#!/usr/bin/env python3
"""
Test Script for AI-Powered Ticket Booking Agent

This script helps you verify that all components are working correctly
before running the actual booking agent.
"""

import sys
import os
from pathlib import Path
import logging

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test if all required packages can be imported"""
    print("🔍 Testing imports...")
    
    required_packages = [
        ("selenium", "Selenium WebDriver"),
        ("requests", "HTTP Requests"),
        ("dotenv", "Environment Variables"),
        ("bs4", "Beautiful Soup"),
        ("PIL", "Pillow (Image Processing)"),
        ("fake_useragent", "Fake User Agent"),
    ]
    
    optional_packages = [
        ("openai", "OpenAI API Client"),
        ("anthropic", "Anthropic API Client"),
        ("google.generativeai", "Google Gemini API Client"),
        ("undetected_chromedriver", "Undetected Chrome Driver"),
    ]
    
    all_good = True
    
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {name}")
        except ImportError as e:
            print(f"  ❌ {name} - {e}")
            all_good = False
    
    print("\n📦 Optional packages:")
    for package, name in optional_packages:
        try:
            __import__(package)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ⚠️  {name} - Not installed (optional)")
    
    return all_good


def test_configuration():
    """Test configuration loading"""
    print("\n⚙️ Testing configuration...")
    
    if not os.path.exists(".env"):
        print("  ❌ .env file not found. Copy .env.template to .env and configure it.")
        return False
    
    try:
        from ticket_booking_agent import AgentConfig
        config = AgentConfig.from_env()
        
        # Check required fields
        required_fields = [
            ("target_website_url", "Target Website URL"),
            ("user_email", "User Email"),
            ("email_password", "Email Password"),
        ]
        
        all_good = True
        for field, name in required_fields:
            value = getattr(config, field)
            if value:
                print(f"  ✅ {name}: {value[:20]}..." if len(value) > 20 else f"  ✅ {name}: {value}")
            else:
                print(f"  ❌ {name}: Not configured")
                all_good = False
        
        # Check LLM API keys
        llm_keys = [
            ("openai_api_key", "OpenAI API Key"),
            ("anthropic_api_key", "Anthropic API Key"),
            ("gemini_api_key", "Gemini API Key"),
        ]
        
        has_llm_key = False
        for field, name in llm_keys:
            value = getattr(config, field)
            if value:
                print(f"  ✅ {name}: {'*' * 20}")
                has_llm_key = True
            else:
                print(f"  ⚠️  {name}: Not configured")
        
        if not has_llm_key:
            print("  ❌ At least one LLM API key is required")
            all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False


def test_email_configuration():
    """Test email configuration"""
    print("\n📧 Testing email configuration...")
    
    try:
        from ticket_booking_agent import TicketBookingAgent, AgentConfig
        
        config = AgentConfig.from_env()
        agent = TicketBookingAgent(config)
        
        if agent.test_email_configuration():
            print("  ✅ Email configuration test passed")
            print(f"  📬 Test email sent to {config.user_email}")
            return True
        else:
            print("  ❌ Email configuration test failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Email test error: {e}")
        return False


def test_browser_setup():
    """Test browser setup"""
    print("\n🌐 Testing browser setup...")
    
    try:
        from web_scraper import WebScraper
        
        config = {
            'headless_browser': True,
            'browser_timeout': 10,
            'max_attempts': 1,
            'retry_interval': 1,
        }
        
        with WebScraper(config) as scraper:
            # Try to load a simple webpage
            scraper.driver.get("https://httpbin.org/html")
            title = scraper.driver.title
            
            if title:
                print(f"  ✅ Browser test passed - Page title: {title}")
                return True
            else:
                print("  ❌ Browser test failed - No page title")
                return False
                
    except Exception as e:
        print(f"  ❌ Browser test error: {e}")
        print("  💡 Make sure Chrome/Chromium is installed")
        return False


def test_llm_integration():
    """Test LLM integration"""
    print("\n🤖 Testing LLM integration...")
    
    try:
        from llm_agent import LLMAgent
        from ticket_booking_agent import AgentConfig
        
        config = AgentConfig.from_env()
        
        # Try to create LLM agent
        if config.openai_api_key:
            provider = "openai"
            api_key = config.openai_api_key
        elif config.anthropic_api_key:
            provider = "anthropic"
            api_key = config.anthropic_api_key
        elif config.gemini_api_key:
            provider = "gemini"
            api_key = config.gemini_api_key
        else:
            print("  ❌ No LLM API key configured")
            return False
        
        llm = LLMAgent(provider=provider, api_key=api_key)
        
        # Test simple query
        response = llm._query_llm("Say 'Hello' if you can read this message.", max_tokens=10)
        
        if response and "hello" in response.lower():
            print(f"  ✅ LLM test passed - Provider: {provider}")
            print(f"  🤖 Response: {response}")
            return True
        else:
            print(f"  ⚠️  LLM responded but unexpected output: {response}")
            return False
            
    except Exception as e:
        print(f"  ❌ LLM test error: {e}")
        return False


def test_full_agent():
    """Test creating the full agent"""
    print("\n🎫 Testing full agent creation...")
    
    try:
        from ticket_booking_agent import TicketBookingAgent, AgentConfig
        
        config = AgentConfig.from_env()
        agent = TicketBookingAgent(config)
        
        # Validate configuration
        issues = agent.validate_configuration()
        
        if not issues:
            print("  ✅ Agent created successfully")
            print("  ✅ Configuration validation passed")
            return True
        else:
            print("  ❌ Configuration validation failed:")
            for issue in issues:
                print(f"    - {issue}")
            return False
            
    except Exception as e:
        print(f"  ❌ Agent creation error: {e}")
        return False


def run_comprehensive_test():
    """Run all tests"""
    print("🧪 AI-Powered Ticket Booking Agent - Comprehensive Test")
    print("=" * 60)
    
    tests = [
        ("Package Imports", test_imports),
        ("Configuration", test_configuration),
        ("Email Setup", test_email_configuration),
        ("Browser Setup", test_browser_setup),
        ("LLM Integration", test_llm_integration),
        ("Full Agent", test_full_agent),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"  💥 Test crashed: {e}")
            results[test_name] = False
        print()
    
    # Summary
    print("📊 Test Summary")
    print("-" * 30)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")
    
    print("-" * 30)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your agent is ready to use.")
        print("\n🚀 To run the agent:")
        print("   python run_agent.py")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix the issues before running the agent.")
        print("\n🔧 Common solutions:")
        print("   - Install missing packages: pip install -r requirements.txt")
        print("   - Configure .env file with your settings")
        print("   - Check API keys and email credentials")
        print("   - Install Chrome/Chromium browser")
    
    return passed == total


def quick_test():
    """Run a quick test for basic functionality"""
    print("⚡ Quick Test Mode")
    print("-" * 20)
    
    # Test only critical components
    tests = [
        test_imports,
        test_configuration,
    ]
    
    for test in tests:
        if not test():
            return False
        print()
    
    print("✅ Quick test passed! Run 'python test_agent.py --full' for comprehensive testing.")
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        run_comprehensive_test()
    else:
        quick_test()