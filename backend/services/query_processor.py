import logging
from typing import Dict, Any, Optional, AsyncGenerator
from .supabase_service import SupabaseService
from .openai_service import OpenAIService
from constants import (
    HELP_RESPONSE,
    GREETING_RESPONSE,
    STATUS_MESSAGES,
    ERROR_MESSAGES,
    SPECIAL_QUERY_KEYWORDS
)

logger = logging.getLogger(__name__)

class QueryProcessor:
    
    def __init__(self, supabase_service: SupabaseService, openai_service: OpenAIService):
        self.supabase = supabase_service
        self.openai = openai_service
    
    async def process_query(self, user_query: str, session_id: Optional[int] = None) -> Dict[str, Any]:
        try:
            connection_test = self.supabase.test_connection()
            if not connection_test.get("success", False):
                return {
                    "response": ERROR_MESSAGES['connection_failed'],
                    "error": connection_test.get("error", "Connection failed")
                }
            
            logger.info("Getting database schema...")
            database_info = await self.supabase.get_database_info()
            
            if "error" in database_info:
                return {
                    "response": ERROR_MESSAGES['no_permissions'],
                    "error": database_info["error"]
                }
            
            logger.info("Generating SQL with OpenAI...")
            sql_generation = await self.openai.generate_sql_query(user_query, database_info)
            
            if not sql_generation.get("success", False):
                return {
                    "response": ERROR_MESSAGES['query_interpretation_failed'],
                    "error": sql_generation.get("error", "SQL generation failed")
                }
            
            sql_response = sql_generation["sql_response"]
            
            if sql_response.get("type") == "help":
                return {
                    "response": GREETING_RESPONSE,
                    "queryResult": None
                }
            elif sql_response.get("type") == "tables":
                tables = database_info.get("tables", [])
                table_names = [table.get("name", "") for table in tables if table.get("name")]
                return {
                    "response": f"Your database has {len(table_names)} tables: {', '.join(table_names)}. You can ask me to count records, view data, or filter information from any of these tables.",
                    "queryResult": {
                        "tables": table_names,
                        "total_tables": len(table_names)
                    }
                }
            elif sql_response.get("type") == "error":
                return {
                    "response": sql_response.get("message", "An error occurred"),
                    "error": "Table not found"
                }
            
            logger.info(f"Executing SQL: {sql_response.get('sql')}")
            sql_query = sql_response.get("sql")
            if not sql_query:
                return {
                    "response": "I couldn't generate a SQL query for your request. Could you try rephrasing it?",
                    "error": "Empty SQL query"
                }
            
            query_result = await self.supabase.execute_raw_sql(sql_query)
            
            logger.info("Generating natural language response...")
            response_text = await self.openai.generate_response(
                user_query, 
                query_result, 
                database_info
            )
            
            if session_id:
                try:
                    self.supabase.client.table("chat_messages").insert({
                        "session_id": session_id,
                        "message_type": "user",
                        "content": user_query
                    }).execute()
                    
                    self.supabase.client.table("chat_messages").insert({
                        "session_id": session_id,
                        "message_type": "bot",
                        "content": response_text,
                        "query_result": query_result if query_result.get("success") else None,
                        "query_params": {"sql": sql_query, "explanation": sql_response.get("explanation")}
                    }).execute()
                except Exception as save_error:
                    logger.warning(f"Failed to save messages to database: {str(save_error)}")
            
            return {
                "response": response_text,
                "queryResult": query_result if query_result.get("success") else None,
                "sqlQuery": sql_query,
                "explanation": sql_response.get("explanation"),
                "error": query_result.get("error") if not query_result.get("success") else None
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "response": ERROR_MESSAGES['general_error'],
                "error": str(e)
            }

    async def process_query_stream(self, user_query: str, session_id: Optional[int] = None) -> AsyncGenerator[Dict[str, Any], None]:
        try:
            yield {"type": "status", "message": STATUS_MESSAGES['connecting']}
            
            connection_test = self.supabase.test_connection()
            if not connection_test.get("success", False):
                yield {
                    "type": "error",
                    "message": ERROR_MESSAGES['connection_failed'],
                    "error": connection_test.get("error", "Connection failed")
                }
                return
            
            yield {"type": "status", "message": STATUS_MESSAGES['analyzing_schema']}
            
            database_info = await self.supabase.get_database_info()
            
            if "error" in database_info:
                yield {
                    "type": "error",
                    "message": ERROR_MESSAGES['no_permissions'],
                    "error": database_info["error"]
                }
                return
            
            yield {"type": "status", "message": STATUS_MESSAGES['interpreting_query']}
            
            sql_generation = await self.openai.generate_sql_query(user_query, database_info)
            
            if not sql_generation.get("success", False):
                yield {
                    "type": "error",
                    "message": ERROR_MESSAGES['query_interpretation_failed'],
                    "error": sql_generation.get("error", "SQL generation failed")
                }
                return
            
            sql_response = sql_generation["sql_response"]
            
            if sql_response.get("type") == "help":
                yield {
                    "type": "response",
                    "message": GREETING_RESPONSE,
                    "queryResult": None
                }
                return
            elif sql_response.get("type") == "tables":
                tables = database_info.get("tables", [])
                table_names = [table.get("name", "") for table in tables if table.get("name")]
                yield {
                    "type": "response",
                    "message": f"Your database has {len(table_names)} tables: {', '.join(table_names)}. You can ask me to count records, view data, or filter information from any of these tables.",
                    "queryResult": {
                        "tables": table_names,
                        "total_tables": len(table_names)
                    }
                }
                return
            elif sql_response.get("type") == "error":
                yield {
                    "type": "response",
                    "message": sql_response.get("message", "An error occurred"),
                    "error": "Table not found"
                }
                return
            
            yield {"type": "status", "message": STATUS_MESSAGES['executing_query']}
            
            sql_query = sql_response.get("sql")
            if not sql_query:
                yield {
                    "type": "error",
                    "message": "I couldn't generate a SQL query for your request. Could you try rephrasing it?",
                    "error": "Empty SQL query"
                }
                return
            
            query_result = await self.supabase.execute_raw_sql(sql_query)
            
            yield {"type": "status", "message": STATUS_MESSAGES['generating_response']}
            
            try:
                async for response_chunk in self.openai.generate_response_stream(
                    user_query, 
                    query_result, 
                    database_info
                ):
                    yield {
                        "type": "response_chunk",
                        "content": response_chunk
                    }
            except Exception as stream_error:
                logger.error(f"Error in response streaming: {str(stream_error)}")
                fallback_response = await self.openai.generate_response(user_query, query_result, database_info)
                yield {
                    "type": "response",
                    "message": fallback_response,
                    "queryResult": query_result if query_result.get("success") else None
                }
            
            yield {
                "type": "final",
                "queryResult": query_result if query_result.get("success") else None,
                "sqlQuery": sql_query,
                "explanation": sql_response.get("explanation"),
                "error": query_result.get("error") if not query_result.get("success") else None
            }
            
            if session_id:
                try:
                    full_response = await self.openai.generate_response(user_query, query_result, database_info)
                    
                    self.supabase.client.table("chat_messages").insert({
                        "session_id": session_id,
                        "message_type": "user",
                        "content": user_query
                    }).execute()
                    
    
                    self.supabase.client.table("chat_messages").insert({
                        "session_id": session_id,
                        "message_type": "bot",
                        "content": full_response,
                        "query_result": query_result if query_result.get("success") else None,
                        "query_params": {"sql": sql_query, "explanation": sql_response.get("explanation")}
                    }).execute()
                except Exception as save_error:
                    logger.warning(f"Failed to save messages to database: {str(save_error)}")
            
        except Exception as e:
            logger.error(f"Error processing query stream: {str(e)}")
            yield {
                "type": "error",
                "message": ERROR_MESSAGES['general_error'],
                "error": str(e)
            } 