import random
import string
from datetime import datetime

def generate_ticket_id() -> str:
    """Generate a random 8-character ticket ID."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=8))

def format_timestamp(dt: datetime) -> str:
    """Format datetime to Discord <t:...> format."""
    timestamp = int(dt.timestamp())
    return f"<t:{timestamp}:F>"
