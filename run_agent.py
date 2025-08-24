#!/usr/bin/env python3
"""
Quick start script for the AI-Powered Ticket Booking Agent

This script provides an easy way to run the agent with minimal setup.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ticket_booking_agent import main

if __name__ == "__main__":
    main()