import logging
import logging.handlers
import sys
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)  # Create logs directory if it doesn't exist
LOG_FILE = LOG_DIR / "app.log"

# Basic configuration
LOG_LEVEL = logging.INFO  # Set the desired log level (e.g., INFO, DEBUG)
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Create formatter
formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

# --- Handlers ---

# Console Handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(LOG_LEVEL)  # Console handler can have its own level

# Rotating File Handler
# Rotates logs when they reach 10MB, keeps 5 backup logs
file_handler = logging.handlers.RotatingFileHandler(
    LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
file_handler.setFormatter(formatter)
file_handler.setLevel(LOG_LEVEL)  # File handler can also have its own level

# --- Configure Root Logger ---
# Get the root logger
root_logger = logging.getLogger()
root_logger.setLevel(LOG_LEVEL)  # Set the minimum level for the root logger

# Remove default handlers if any exist
if root_logger.hasHandlers():
    root_logger.handlers.clear()

# Add our handlers
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

# --- Specific Logger Example (optional, good practice) ---
# You can also configure specific loggers if needed
# specific_logger = logging.getLogger("my_module")
# specific_logger.setLevel(logging.DEBUG) # Override level for this specific logger
# specific_logger.addHandler(some_other_handler)
# specific_logger.propagate = False # Prevent messages from going to root logger handlers


def get_logger(name: str) -> logging.Logger:
    """Gets a logger instance configured according to the project settings."""
    return logging.getLogger(name)


# Optional: Log that configuration is done (useful for debugging setup)
# logging.info("Logging configured successfully.") # Use get_logger(__name__).info(...) instead if using specific loggers primarily
