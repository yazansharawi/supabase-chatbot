from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any
import re

def sanitize_user_input(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""
    
    text = re.sub(r'[<>{}]', '', text)
    
    text = text[:500]
    
    dangerous_patterns = [
        r'--', r'/\*', r'\*/', r';.*--;', r'union\s+select',
        r'drop\s+table', r'delete\s+from', r'insert\s+into',
        r'update\s+.*\s+set', r'alter\s+table'
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()

class ChatRequest(BaseModel):
    message: str
    config: Dict[str, str]
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Message cannot be empty')
        if len(v) > 500:
            raise ValueError('Message too long (max 500 characters)')
        return sanitize_user_input(v)

class ChatResponse(BaseModel):
    response: str
    queryResult: Optional[Any] = None
    error: Optional[str] = None

class ConfigRequest(BaseModel):
    supabaseUrl: str
    supabaseKey: str
    openaiKey: str

class SessionRequest(BaseModel):
    name: str
    config: Dict[str, str] 