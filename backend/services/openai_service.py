import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
from openai import AsyncOpenAI
import json
from constants import (
    OPENAI_SQL_GENERATION_PROMPT, 
    OPENAI_RESPONSE_GENERATION_PROMPT,
    KNOWN_TABLES,
    DEFAULT_QUERY_LIMIT
)

logger = logging.getLogger(__name__)

class OpenAIService:
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def generate_sql_query(self, user_query: str, database_schema: Dict[str, Any]) -> Dict[str, Any]:
        try:
            schema_info = self._format_schema_for_prompt(database_schema)
            logger.info(f"Schema info for AI: {schema_info}")
            
            system_prompt = OPENAI_SQL_GENERATION_PROMPT.format(schema_info=schema_info)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ]
            
            logger.info(f"Sending query to OpenAI: {user_query}")
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.1,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content
            logger.info(f"OpenAI raw response: {response_text}")
            
            try:
                sql_response = json.loads(response_text)
                logger.info(f"Successfully parsed SQL response: {sql_response}")
                return {
                    "success": True,
                    "sql_response": sql_response
                }
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse OpenAI response as JSON: {response_text}")
                extracted = self._extract_json_from_response(response_text)
                if not extracted.get("success"):
                    logger.warning("JSON extraction failed, creating fallback response")
                    return self._create_fallback_sql_response(user_query, response_text)
                logger.info(f"Successfully extracted JSON: {extracted}")
                return extracted
                
        except Exception as e:
            logger.error(f"Error interpreting query: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_response(self, user_query: str, query_result: Dict[str, Any], 
                              database_context: Optional[Dict[str, Any]] = None) -> str:
        try:
            context = {
                "user_query": user_query,
                "query_result": query_result,
                "database_context": database_context
            }
            
            system_prompt = OPENAI_RESPONSE_GENERATION_PROMPT
            
            user_prompt = f"""
User asked: "{user_query}"

Query result: {json.dumps(query_result, indent=2)}

Please provide a natural language response to the user.
"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return f"I found some results for your query, but I'm having trouble explaining them right now. Here's the raw data: {str(query_result)}"
    
    async def generate_response_stream(self, user_query: str, query_result: Dict[str, Any], 
                                     database_context: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:

        try:
            context = {
                "user_query": user_query,
                "query_result": query_result,
                "database_context": database_context
            }
            
            system_prompt = OPENAI_RESPONSE_GENERATION_PROMPT
            
            user_prompt = f"""
User asked: "{user_query}"

Query result: {json.dumps(query_result, indent=2)}

Please provide a natural language response to the user.
"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            stream = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=300,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
            
        except Exception as e:
            logger.error(f"Error generating streaming response: {str(e)}")
            yield f"I found some results for your query, but I'm having trouble explaining them right now."
    
    def _format_schema_for_prompt(self, database_schema: Dict[str, Any]) -> str:
        try:
            if not database_schema or "tables" not in database_schema:
                return "No table information available"
            
            schema_text = f"Database has {database_schema.get('total_tables', 0)} accessible tables:\n\n"
            
            for table in database_schema.get("tables", []):
                table_name = table.get("name", "unknown")
                columns = table.get("columns", [])
                estimated_rows = table.get("estimated_rows", "unknown")
                accessible = table.get("accessible", False)
                
                if not accessible:
                    continue
                    
                schema_text += f"Table: {table_name}\n"
                
                if columns:
                    schema_text += f"Available columns: {', '.join(columns)}\n"
                    schema_text += f"IMPORTANT: This table ONLY has these {len(columns)} columns. Do NOT assume any other columns exist!\n"
                else:
                    schema_text += "Columns: (structure unknown - try querying to discover)\n"
                
                if estimated_rows != "unknown":
                    schema_text += f"Estimated rows: {estimated_rows}\n"
                
                schema_text += "\n"
            
            schema_text += "CRITICAL RULES:\n"
            schema_text += "- ONLY use columns that are explicitly listed above\n"
            schema_text += "- If user asks about non-existent columns (like location, city, country), explain that column doesn't exist\n"
            schema_text += "- Never assume or invent data that isn't in the actual schema\n"
            schema_text += "- Always check the column list before generating queries\n\n"
            
            if "schema_summary" in database_schema:
                summary = database_schema["schema_summary"]
                if summary:
                    schema_text += "Quick reference:\n"
                    for item in summary:
                        schema_text += f"- {item}\n"
            
            return schema_text
            
        except Exception as e:
            logger.error(f"Error formatting schema: {str(e)}")
            return f"Error formatting schema information: {str(e)}"
    
    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        try:
            cleaned_text = response_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith('```'):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
            
            cleaned_text = cleaned_text.strip()
            
            start = cleaned_text.find('{')
            end = cleaned_text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = cleaned_text[start:end]
                sql_response = json.loads(json_str)
                return {
                    "success": True,
                    "sql_response": sql_response
                }
            
            return {
                "success": False,
                "error": "Could not parse AI response as valid JSON",
                "raw_response": response_text
            }
            
        except Exception as e:
            logger.error(f"Error extracting JSON: {str(e)}")
            return {
                "success": False,
                "error": f"JSON extraction failed: {str(e)}",
                "raw_response": response_text
            }
    
    def _create_fallback_sql_response(self, user_query: str, ai_response: str) -> Dict[str, Any]:
        query_lower = user_query.lower().strip()
        
        if any(word in query_lower for word in ['users', 'user']):
            if any(word in query_lower for word in ['count', 'how many']):
                sql = "SELECT COUNT(*) as total FROM users;"
                explanation = "Count all users in the users table"
            else:
                sql = f"SELECT * FROM users LIMIT {DEFAULT_QUERY_LIMIT};"
                explanation = f"Retrieve first {DEFAULT_QUERY_LIMIT} users from the users table"
            
            return {
                "success": True,
                "sql_response": {
                    "type": "sql",
                    "sql": sql,
                    "explanation": explanation
                }
            }
        elif any(word in query_lower for word in ['products', 'product']):
            if any(word in query_lower for word in ['count', 'how many']):
                sql = "SELECT COUNT(*) as total FROM products;"
                explanation = "Count all products in the products table"
            else:
                sql = f"SELECT * FROM products LIMIT {DEFAULT_QUERY_LIMIT};"
                explanation = f"Retrieve first {DEFAULT_QUERY_LIMIT} products from the products table"
            
            return {
                "success": True,
                "sql_response": {
                    "type": "sql",
                    "sql": sql,
                    "explanation": explanation
                }
            }
        else:
            return {
                "success": False,
                "error": f"Could not parse SQL generation. AI said: {ai_response}",
                "fallback_response": ai_response
            } 