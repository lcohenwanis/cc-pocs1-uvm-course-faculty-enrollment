"""
Configuration settings for the UVM course enrollment scraper and analyzer.
"""

# Data source
BASE_URL = "https://serval.uvm.edu/~rgweb/batch/enrollment/enrollment_tab.html"
DATA_DIR = "data"
DATABASE_PATH = "data/uvm_courses.db"

# Scraping settings
START_YEAR = 1995
END_YEAR = 2025
REQUEST_TIMEOUT = 30
DELAY_BETWEEN_REQUESTS = 1  # seconds

# Network analysis settings
NETWORK_OUTPUT_DIR = "data/networks"
VISUALIZATION_OUTPUT_DIR = "data/visualizations"

# Database settings
DB_ECHO = False  # Set to True for SQL debugging
