from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, validator
import configparser
import os
import json
import re
from typing import Optional, Dict, Any, AsyncGenerator
from constants import (
    API_TITLE,
    API_DESCRIPTION, 
    API_VERSION,
    CONFIG_FILE_PATH,
    REQUIRED_CONFIG_FIELDS
)

from services.supabase_service import SupabaseService
from services.openai_service import OpenAIService
from services.query_processor import QueryProcessor

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    return response

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
    
    @validator('message')
    def validate_message(cls, v):
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

config = configparser.ConfigParser()

def load_config():
    if os.path.exists(CONFIG_FILE_PATH):
        config.read(CONFIG_FILE_PATH)

def save_config(new_config: ConfigRequest):
    config['DEFAULT'] = {
        'supabase_url': new_config.supabaseUrl,
        'supabase_key': new_config.supabaseKey,
        'openai_key': new_config.openaiKey
    }
    
    with open(CONFIG_FILE_PATH, 'w') as configfile:
        config.write(configfile)

@app.on_event("startup")
async def startup_event():
    load_config()

@app.get("/")
async def root():
    return {"message": "Supabase Chatbot API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "supabase-chatbot-api"}

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    try:
        load_config()
        
        supabase_url = request.config.get("supabaseUrl")
        supabase_key = request.config.get("supabaseKey") 
        openai_key = request.config.get("openaiKey")
        
        if not supabase_url and 'DEFAULT' in config:
            supabase_url = config['DEFAULT'].get('supabase_url', '')
        if not supabase_key and 'DEFAULT' in config:
            supabase_key = config['DEFAULT'].get('supabase_key', '')
        if not openai_key and 'DEFAULT' in config:
            openai_key = config['DEFAULT'].get('openai_key', '')
        
        if not supabase_url:
            raise Exception("supabase_url is required")
        if not supabase_key:
            raise Exception("supabase_key is required")
        if not openai_key:
            raise Exception("openai_key is required")
        
        supabase_service = SupabaseService(url=supabase_url, key=supabase_key)
        openai_service = OpenAIService(api_key=openai_key)
        
    except Exception as e:
        async def error_response() -> AsyncGenerator[str, None]:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        
        return StreamingResponse(
            error_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }
        )

    async def generate_response() -> AsyncGenerator[str, None]:
        try:
            query_processor = QueryProcessor(supabase_service, openai_service)
            
            session_id = request.config.get("sessionId")
            
            yield f"data: {json.dumps({'type': 'status', 'message': 'Processing your query...'})}\n\n"
            
            async for chunk in query_processor.process_query_stream(request.message, session_id):
                yield f"data: {json.dumps(chunk)}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            error_data = {
                'type': 'error',
                'error': str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        supabase_url = request.config.get("supabaseUrl") or config['DEFAULT'].get('supabase_url', '')
        supabase_key = request.config.get("supabaseKey") or config['DEFAULT'].get('supabase_key', '')
        openai_key = request.config.get("openaiKey") or config['DEFAULT'].get('openai_key', '')
        
        if not supabase_url:
            raise HTTPException(status_code=400, detail="supabase_url is required")
        if not supabase_key:
            raise HTTPException(status_code=400, detail="supabase_key is required")
        if not openai_key:
            raise HTTPException(status_code=400, detail="openai_key is required")
        
        supabase_service = SupabaseService(url=supabase_url, key=supabase_key)
        openai_service = OpenAIService(api_key=openai_key)
        
        query_processor = QueryProcessor(supabase_service, openai_service)
        
        session_id = request.config.get("sessionId")
        
        result = await query_processor.process_query(request.message, session_id)
        
        return ChatResponse(
            response=result["response"],
            queryResult=result.get("queryResult"),
            error=result.get("error")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )

@app.post("/api/config")
async def save_configuration(request: ConfigRequest):
    try:
        save_config(request)
        
        supabase_service = SupabaseService(
            url=request.supabaseUrl,
            key=request.supabaseKey
        )
        
        supabase_key_hint = f"{request.supabaseKey[:8]}...{request.supabaseKey[-4:]}"
        openai_key_hint = f"{request.openaiKey[:12]}...{request.openaiKey[-4:]}"
        
        existing_config = await supabase_service.execute_query(
            table_name="configurations",
            operation="select",
            filters={"supabase_url": request.supabaseUrl},
            limit=1
        )
        
        if existing_config.get("success") and existing_config.get("data"):
            config_id = existing_config["data"][0]["id"]
            update_result = supabase_service.client.table("configurations").update({
                "supabase_key_hint": supabase_key_hint,
                "openai_key_hint": openai_key_hint,
                "updated_at": "NOW()",
                "is_active": True
            }).eq("id", config_id).execute()
        else:
            insert_result = supabase_service.client.table("configurations").insert({
                "name": "Frontend Config",
                "supabase_url": request.supabaseUrl,
                "supabase_key_hint": supabase_key_hint,
                "openai_key_hint": openai_key_hint
            }).execute()
        
        return {"message": "Configuration saved successfully to file and database"}
    except Exception as e:
        try:
            save_config(request)
            return {"message": f"Configuration saved to file, but database save failed: {str(e)}"}
        except Exception as file_error:
            raise HTTPException(
                status_code=500,
                detail=f"Error saving configuration: {str(file_error)}"
            )

@app.get("/api/config")
async def get_configuration():
    """
    Get current configuration (without sensitive keys)
    """
    try:
        if 'DEFAULT' in config:
            supabase_url = config['DEFAULT'].get('supabase_url', '')
            supabase_key = config['DEFAULT'].get('supabase_key', '')
            openai_key = config['DEFAULT'].get('openai_key', '')
            
            is_configured = bool(supabase_url and supabase_key and openai_key)
            
            return {
                "supabaseUrl": supabase_url,
                "hasSupabaseKey": bool(supabase_key),
                "hasOpenaiKey": bool(openai_key),
                "isConfigured": is_configured,
                "canSkipConfig": is_configured
            }
        return {
            "supabaseUrl": "",
            "hasSupabaseKey": False,
            "hasOpenaiKey": False,
            "isConfigured": False,
            "canSkipConfig": False
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving configuration: {str(e)}"
        )

@app.post("/api/sessions")
async def create_session(request: SessionRequest):
    try:
        supabase_service = SupabaseService(
            url=request.config.get("supabaseUrl"),
            key=request.config.get("supabaseKey")
        )
        
        config_result = await supabase_service.execute_query(
            table_name="configurations",
            operation="select", 
            filters={"supabase_url": request.config.get("supabaseUrl")},
            limit=1
        )
        
        config_id = None
        if config_result.get("success") and config_result.get("data"):
            config_id = config_result["data"][0]["id"]
        
        session_result = supabase_service.client.table("chat_sessions").insert({
            "session_name": request.name,
            "configuration_id": config_id
        }).execute()
        
        return {
            "message": "Session created successfully",
            "session": session_result.data[0] if session_result.data else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating session: {str(e)}"
        )

@app.get("/api/sessions")
async def get_sessions(supabase_url: str, supabase_key: str):
    try:
        supabase_service = SupabaseService(url=supabase_url, key=supabase_key)
        
        sessions_result = supabase_service.client.table("chat_sessions").select(
            "*, configurations(name, supabase_url)"
        ).order("created_at", desc=True).execute()
        
        return {
            "sessions": sessions_result.data if sessions_result.data else []
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving sessions: {str(e)}"
        )

@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: int, supabase_url: str, supabase_key: str):
    try:
        supabase_service = SupabaseService(url=supabase_url, key=supabase_key)
        
        messages_result = await supabase_service.execute_query(
            table_name="chat_messages",
            operation="select",
            filters={"session_id": session_id}
        )
        
        return {
            "messages": messages_result.get("data", []) if messages_result.get("success") else []
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving messages: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
