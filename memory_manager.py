import json
import logging
import os
from typing import List, Dict

logger = logging.getLogger(__name__)

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "data", "user_memory.json")
MAX_HISTORY_MESSAGES = 14  # Keep last 14 messages (approx 7 rounds of dialogue)

# In-memory cache
_user_histories: Dict[int, List[Dict[str, str]]] = {}


def _load_memory():
    """Load conversations from disk if available."""
    global _user_histories
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                # Convert string keys back to int
                _user_histories = {int(k): v for k, v in raw_data.items()}
                logger.info(f"Loaded memory for {len(_user_histories)} users from file.")
    except Exception as e:
        logger.warning(f"Could not load user memory: {e}")
        _user_histories = {}


def _save_memory():
    """Save conversations to disk."""
    try:
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(_user_histories, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Could not save user memory: {e}")


# Initialize memory on import
_load_memory()


def get_user_history(user_id: int) -> List[Dict[str, str]]:
    """Return conversation history list for a user."""
    return _user_histories.get(user_id, [])


def add_message(user_id: int, role: str, content: str):
    """Add a message to user's conversation history and prune old turns."""
    if not content:
        return

    if user_id not in _user_histories:
        _user_histories[user_id] = []

    _user_histories[user_id].append({
        "role": role,
        "content": content.strip()
    })

    # Keep only the last MAX_HISTORY_MESSAGES
    if len(_user_histories[user_id]) > MAX_HISTORY_MESSAGES:
        _user_histories[user_id] = _user_histories[user_id][-MAX_HISTORY_MESSAGES:]

    _save_memory()


def clear_user_history(user_id: int):
    """Clear memory for a user."""
    if user_id in _user_histories:
        _user_histories[user_id] = []
        _save_memory()
