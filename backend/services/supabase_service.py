import logging
from typing import Dict, List, Any, Optional
from supabase import create_client, Client
import json
from constants import KNOWN_TABLES, DEFAULT_QUERY_LIMIT

logger = logging.getLogger(__name__)

class SupabaseService:
    
    def __init__(self, url: str, key: str):
        self.url = url
        self.key = key
        self.client: Client = create_client(url, key)
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        try:
            result = self.client.table(table_name).select("*").limit(0).execute()
            
            return {
                "table_name": table_name,
                "exists": True,
                "message": f"Table '{table_name}' is accessible"
            }
                
        except Exception as e:
            logger.error(f"Error getting table schema for {table_name}: {str(e)}")
            return {
                "table_name": table_name,
                "exists": False,
                "error": str(e)
            }
    
    async def list_tables(self) -> List[Dict[str, Any]]:
        try:
            known_tables = KNOWN_TABLES
            found_tables = []
            
            for table_name in known_tables:
                try:
                    test_result = self.client.table(table_name).select("*").limit(0).execute()
                    found_tables.append({
                        "table_name": table_name,
                        "table_schema": "public",
                        "accessible": True
                    })
                except Exception as e:
                    logger.debug(f"Table {table_name} not accessible: {str(e)}")
                    continue
            
            if not found_tables:
                found_tables = [{"table_name": "users", "table_schema": "public", "accessible": False}]
            
            return found_tables
                
        except Exception as e:
            logger.error(f"Error listing tables: {str(e)}")
            return [{"table_name": "users", "table_schema": "public", "accessible": False}]
    
    async def execute_query(self, table_name: str, operation: str, filters: Optional[Dict] = None, 
                          select_columns: Optional[List[str]] = None, limit: Optional[int] = DEFAULT_QUERY_LIMIT) -> Dict[str, Any]:
        try:
            if operation.lower() == "select":
                query = self.client.table(table_name)
                
                if select_columns:
                    query = query.select(", ".join(select_columns))
                else:
                    query = query.select("*")
                
                if filters:
                    for key, value in filters.items():
                        if isinstance(value, dict):
                            for op, val in value.items():
                                if op == "eq":
                                    query = query.eq(key, val)
                                elif op == "gt":
                                    query = query.gt(key, val)
                                elif op == "lt":
                                    query = query.lt(key, val)
                                elif op == "gte":
                                    query = query.gte(key, val)
                                elif op == "lte":
                                    query = query.lte(key, val)
                                elif op == "like":
                                    query = query.like(key, val)
                                elif op == "ilike":
                                    query = query.ilike(key, val)
                        else:
                            query = query.eq(key, value)
                
                if limit:
                    query = query.limit(limit)
                
                result = query.execute()
                
                return {
                    "success": True,
                    "data": result.data,
                    "count": len(result.data) if result.data else 0,
                    "operation": operation
                }
                
            elif operation.lower() == "count":
                query = self.client.table(table_name).select("*", count="exact")
                
                if filters:
                    for key, value in filters.items():
                        if isinstance(value, dict):
                            for op, val in value.items():
                                if op == "eq":
                                    query = query.eq(key, val)
                        else:
                            query = query.eq(key, value)
                
                result = query.execute()
                
                return {
                    "success": True,
                    "count": result.count,
                    "operation": operation
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported operation: {operation}"
                }
                
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "operation": operation
            }
    
    async def get_database_info(self) -> Dict[str, Any]:
        try:
            tables = await self.list_tables()
            
            database_info = {
                "tables": [],
                "total_tables": len([t for t in tables if t.get("accessible", False)]),
                "schema_summary": []
            }
            
            accessible_tables = [t for t in tables if t.get("accessible", False)]
            
            for table in accessible_tables[:10]:  # Limit to first 10 tables for performance
                table_name = table.get("table_name", "")
                if table_name and not table_name.startswith("_"):  # Skip system tables
                    try:
                        sample_result = self.client.table(table_name).select("*").limit(1).execute()
                        
                        columns = []
                        if sample_result.data and len(sample_result.data) > 0:
                            columns = list(sample_result.data[0].keys())
                        
                        table_info = {
                            "name": table_name,
                            "columns": columns,
                            "estimated_rows": "unknown",
                            "accessible": True
                        }
                        
                        try:
                            count_result = self.client.table(table_name).select("*", count="exact").limit(0).execute()
                            if hasattr(count_result, 'count') and count_result.count is not None:
                                table_info["estimated_rows"] = count_result.count
                        except:
                            pass
                        
                        database_info["tables"].append(table_info)
                        database_info["schema_summary"].append(f"{table_name}: {', '.join(columns[:5])}")
                        
                    except Exception as e:
                        logger.warning(f"Could not get detailed info for table {table_name}: {str(e)}")
                        database_info["tables"].append({
                            "name": table_name,
                            "columns": [],
                            "accessible": False,
                            "error": str(e)
                        })
            
            return database_info
            
        except Exception as e:
            logger.error(f"Error getting database info: {str(e)}")
            return {
                "error": str(e),
                "tables": [],
                "total_tables": 0,
                "schema_summary": []
            }
    
    def test_connection(self) -> Dict[str, Any]:
        try:
            test_result = self.client.table("users").select("*").limit(0).execute()
            return {
                "success": True,
                "message": "Connection successful"
            }
        except Exception as e:
            if "relation" in str(e).lower() and "does not exist" in str(e).lower():
                return {
                    "success": True,
                    "message": "Connection successful (table verification)"
                }
            logger.error(f"Connection test failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _validate_sql_safety(self, sql_query: str) -> Dict[str, Any]:
        try:
            sql_lower = sql_query.lower().strip()
            
            forbidden_keywords = [
                'insert', 'update', 'delete', 'drop', 'alter', 'create', 
                'truncate', 'replace', 'merge', 'grant', 'revoke', 
                'exec', 'execute', 'sp_', 'xp_', '--', '/*', '*/',
                'union', 'into', 'information_schema', 'pg_', 'sys',
                'schema', 'database', 'table', 'column', 'index'
            ]
            
            for keyword in forbidden_keywords:
                if keyword in sql_lower:
                    return {
                        "success": False,
                        "error": f"Unsafe SQL detected: '{keyword}' operations are not allowed. Only SELECT and COUNT queries are permitted.",
                        "sql": sql_query
                    }
            
            if not (sql_lower.startswith('select')):
                return {
                    "success": False,
                    "error": "Only SELECT queries are allowed. I can help you view, count, or filter your data.",
                    "sql": sql_query
                }
            
            if ';' in sql_query and sql_query.count(';') > 1:
                return {
                    "success": False,
                    "error": "Multiple SQL statements are not allowed.",
                    "sql": sql_query
                }
            
            return {
                "success": True,
                "message": "SQL query is safe"
            }
            
        except Exception as e:
            logger.error(f"Error validating SQL safety: {str(e)}")
            return {
                "success": False,
                "error": "Unable to validate SQL safety",
                "sql": sql_query
            }

    async def execute_raw_sql(self, sql_query: str) -> Dict[str, Any]:
        try:
            safety_check = self._validate_sql_safety(sql_query)
            if not safety_check.get("success", False):
                return safety_check
            
            sql_lower = sql_query.lower().strip()
            
            if 'count' in sql_lower and 'from' in sql_lower:
                from_match = sql_lower.split(' from ')[1].split(' ')[0].strip()
                table_name = from_match.replace(';', '')
                
                query = self.client.table(table_name).select("*", count="exact").limit(0)
                result = query.execute()
                
                return {
                    "success": True,
                    "data": [{"count": result.count}],
                    "count": 1,
                    "sql": sql_query,
                    "method": "supabase_count"
                }
            
            return await self._fallback_sql_execution(sql_query)
                
        except Exception as e:
            logger.error(f"Error executing raw SQL: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "sql": sql_query
            }
    
    async def _fallback_sql_execution(self, sql_query: str) -> Dict[str, Any]:
        try:
            sql_lower = sql_query.lower().strip()
            
            if sql_lower.startswith('select'):
                if ' from ' in sql_lower:
                    from_part = sql_lower.split(' from ')[1].split(' ')[0].strip()
                    table_name = from_part.replace(';', '')
                    
                    query = self.client.table(table_name)
                    
                    select_part = sql_lower.split(' from ')[0].replace('select', '').strip()
                    if select_part == '*':
                        query = query.select("*")
                    else:
                        columns = select_part.replace(' ', '')
                        query = query.select(columns)
                    
                    if ' where ' in sql_lower:
                        where_part = sql_lower.split(' where ')[1]
                        if ' limit ' in where_part:
                            where_part = where_part.split(' limit ')[0]
                        
                        if ' = ' in where_part:
                            parts = where_part.split(' = ')
                            if len(parts) == 2:
                                column = parts[0].strip()
                                value = parts[1].strip().replace("'", "").replace('"', '')
                                try:
                                    value = int(value)
                                except:
                                    try:
                                        value = float(value)
                                    except:
                                        pass
                                query = query.eq(column, value)
                    
                    if ' limit ' in sql_lower:
                        limit_part = sql_lower.split(' limit ')[1].split(' ')[0]
                        try:
                            limit_val = int(limit_part.replace(';', ''))
                            query = query.limit(limit_val)
                        except:
                            query = query.limit(DEFAULT_QUERY_LIMIT)
                    else:
                        query = query.limit(DEFAULT_QUERY_LIMIT)
                    
                    result = query.execute()
                    
                    return {
                        "success": True,
                        "data": result.data,
                        "count": len(result.data) if result.data else 0,
                        "sql": sql_query,
                        "method": "fallback_parsing"
                    }
            
            elif sql_lower.startswith('select count'):
                if ' from ' in sql_lower:
                    from_part = sql_lower.split(' from ')[1].split(' ')[0].strip()
                    table_name = from_part.replace(';', '')
                    
                    query = self.client.table(table_name).select("*", count="exact").limit(0)
                    
                    if ' where ' in sql_lower:
                        where_part = sql_lower.split(' where ')[1].replace(';', '')
                        if ' = ' in where_part:
                            parts = where_part.split(' = ')
                            if len(parts) == 2:
                                column = parts[0].strip()
                                value = parts[1].strip().replace("'", "").replace('"', '')
                                try:
                                    value = int(value)
                                except:
                                    try:
                                        value = float(value)
                                    except:
                                        pass
                                query = query.eq(column, value)
                    
                    result = query.execute()
                    
                    return {
                        "success": True,
                        "data": [{"total": result.count}],
                        "count": 1,
                        "sql": sql_query,
                        "method": "supabase_count"
                    }
            
            raise Exception("SQL query type not supported by fallback parser")
            
        except Exception as e:
            raise Exception(f"Fallback SQL parsing failed: {str(e)}") 