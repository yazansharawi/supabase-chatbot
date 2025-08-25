from prompts import (
    OPENAI_SQL_GENERATION_PROMPT,
    OPENAI_RESPONSE_GENERATION_PROMPT,
    HELP_RESPONSE,
    GREETING_RESPONSE
)

DEFAULT_QUERY_LIMIT = 10
MAX_QUERY_LIMIT = 100

KNOWN_TABLES = [
    'users', 'products', 'orders', 'customers', 'items', 'posts', 'comments',
    'configurations', 'chat_sessions', 'chat_messages', 'profiles', 'categories'
]

FILTER_OPERATORS = ['eq', 'gt', 'lt', 'gte', 'lte', 'like', 'ilike', 'in', 'neq']

SPECIAL_QUERY_KEYWORDS = {
    'help': ['help', 'what can you do', 'how do i', 'commands'],
    'tables': ['what tables', 'show tables', 'list tables', 'what data', 'database structure', 'what\'s in'],
    'database_info': ['database info', 'db info', 'database summary', 'overview'],
    'greeting': ['hello', 'hi', 'hey', 'greetings']
}

API_VERSION = "1.0.0"
API_TITLE = "Supabase Chatbot API"
API_DESCRIPTION = "API for natural language database interactions with Supabase"

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"

ERROR_MESSAGES = {
    'connection_failed': "I'm having trouble connecting to your database. Please check your Supabase configuration.",
    'no_permissions': "I couldn't retrieve information about your database structure. Please ensure your Supabase credentials have the necessary permissions.",
    'query_interpretation_failed': "I'm having trouble understanding your query. Could you try rephrasing it? For example, you could ask 'Show me all users' or 'What tables do I have?'",
    'query_execution_failed': "I encountered an error while executing your query. Please try rephrasing or check your query parameters.",
    'general_error': "I encountered an unexpected error while processing your query. Please try again or check your configuration."
}

STATUS_MESSAGES = {
    'connecting': "Connecting to database...",
    'analyzing_schema': "Analyzing database structure...",
    'interpreting_query': "Understanding your query...",
    'executing_query': "Executing database query...",
    'generating_response': "Generating response..."
}

REQUIRED_CONFIG_FIELDS = ['supabase_url', 'supabase_key', 'openai_key']

CONFIG_FILE_PATH = 'config.ini'
BACKUP_SUFFIX = '.backup' 