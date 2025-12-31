"""
GoTo Call Automation System - Backend Package

A production-ready system for automated call recording transcription,
AI-powered analysis, and intelligent notifications.
"""

__version__ = "1.0.0"
__author__ = "GoTo Automation Team"

from config import get_settings, configure_logging
from database import db_manager, get_db

__all__ = [
    "get_settings",
    "configure_logging",
    "db_manager",
    "get_db",
]
