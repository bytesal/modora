import time
from collections import defaultdict
from typing import Dict, Tuple

class RateLimiter:
    """Simple in-memory rate limiter for DM replies."""
    
    def __init__(self, max_messages: int = 5, per_seconds: int = 60):
        self.max_messages = max_messages
        self.per_seconds = per_seconds
        self.user_messages: Dict[int, list] = defaultdict(list)
    
    def check_and_update(self, user_id: int) -> Tuple[bool, int]:
        """
        Check if user is rate limited.
        Returns (is_limited, seconds_to_wait)
        """
        now = time.time()
        cutoff = now - self.per_seconds
        
        # Clean old messages
        self.user_messages[user_id] = [ts for ts in self.user_messages[user_id] if ts > cutoff]
        
        if len(self.user_messages[user_id]) >= self.max_messages:
            # Rate limited - calculate wait time
            oldest = min(self.user_messages[user_id])
            wait_time = int(self.per_seconds - (now - oldest))
            return True, max(1, wait_time)
        
        # Not limited - add timestamp
        self.user_messages[user_id].append(now)
        return False, 0
    
    def reset(self, user_id: int):
        """Reset rate limit for a user."""
        if user_id in self.user_messages:
            del self.user_messages[user_id]
