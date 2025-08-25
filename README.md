# Supabase Chatbot

An open-source chatbot application that allows users to interact with their Supabase database using natural language queries. Built with Next.js (frontend) and Python/FastAPI (backend).

## Features

- **Natural Language Interface**: Query your database using plain English
- **Supabase Integration**: Direct connection to your Supabase database
- **AI-Powered**: Uses OpenAI GPT models for query interpretation
- **Modern UI**: Clean, responsive interface built with Next.js and shadcn/ui
- **Easy Configuration**: Simple setup with API keys
- **Secure**: Credentials stored locally, no external data collection
- **Rich Responses**: Get both natural language explanations and raw data

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   Next.js       │    │   Python        │    │   Supabase      │
│   Frontend      │───▶│   FastAPI       │───▶│   Database      │
│                 │    │   Backend       │    │                 │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │                 │
                       │   OpenAI API    │
                       │                 │
                       └─────────────────┘
```

## Prerequisites

- Node.js 18+ and npm
- Python 3.13+ and uv package manager
- Supabase account and project
- OpenAI API key

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/supabase-chatbot.git
cd supabase-chatbot
```

### 2. Set Up the Backend

```bash
cd backend

uv sync

cp config.ini.example config.ini

uv run python main.py
```

The backend will start on `http://localhost:8000`

### 3. Set Up the Frontend

```bash
cd frontend

npm install

npm run dev
```

The frontend will start on `http://localhost:3000`

### 4. Configure Your Credentials

1. Open the application in your browser
2. Click on the Configuration tab
3. Enter your credentials:
   - **Supabase URL**: Your project URL (e.g., `https://your-project.supabase.co`)
   - **Supabase Anon Key**: Your anonymous public key
   - **OpenAI API Key**: Your OpenAI API key (starts with `sk-`)

### 5. Start Chatting!

Try some example queries:
- "What tables do I have?"
- "Show me all users"
- "Count products with price > 100"
- "Show user names and emails"

## Configuration

### Backend Configuration (config.ini)

Copy the example configuration file and fill in your actual API keys:

```bash
cd backend
cp config.ini.example config.ini
```

Edit `config.ini` with your credentials:

```ini
[DEFAULT]
supabase_url = https://your-project.supabase.co
supabase_key = your-supabase-anon-key-here

openai_key = sk-your-openai-api-key-here

api_host = 0.0.0.0
api_port = 8000
debug = false

log_level = INFO
```

> **⚠️ Security Note**: The `config.ini` file contains sensitive API keys and is ignored by git. Never commit this file to version control.

### Environment Variables (Frontend)

Create a `.env.local` file in the frontend directory:

```env
BACKEND_URL=http://localhost:8000
```

## API Endpoints

### Backend (FastAPI)

- `GET /` - Health check
- `GET /health` - Health status
- `POST /api/chat` - Process chat queries (non-streaming)
- `POST /api/chat/stream` - Process chat queries with streaming response
- `GET /api/config` - Get configuration status
- `POST /api/config` - Save configuration

### Frontend (Next.js)

- `POST /api/chat` - Proxy to backend chat endpoint
- `POST /api/chat/stream` - Proxy to backend streaming chat endpoint
- `GET /api/config` - Proxy to backend config endpoint

## Usage Examples

### Basic Queries

```
User: "What tables do I have?"
Bot: "Your database has 3 tables: users, products, orders. You can ask me questions about any of these tables..."

User: "Show me all users"
Bot: "I found 25 users in your database. Here are the first 10 results..."

User: "Count products with price > 100"
Bot: "There are 15 products with a price greater than 100."
```

### Advanced Queries

```
User: "Show users created in the last week"
Bot: "I found 8 users created in the last week..."

User: "What's the average order value?"
Bot: "The average order value is $127.50 based on 234 orders."
```

## Development

### Backend Development

```bash
cd backend

uv sync

uv run uvicorn main:app --reload --port 8000

uv run pytest
```

### Frontend Development

```bash
cd frontend

npm run dev

npm run build

npm start
```

## Security Considerations

- **Local Configuration**: API keys are stored in local `config.ini` files (ignored by git)
- **Browser Storage**: Frontend credentials are stored in browser session storage only
- **No External Data Collection**: No credentials are sent to external services except the configured APIs (Supabase & OpenAI)
- **Production Setup**: Use environment variables for production deployments
- **Rate Limiting**: Consider implementing rate limiting for production deployments
- **Database Security**: Ensure your Supabase RLS (Row Level Security) policies are properly configured
- **API Key Rotation**: Regularly rotate your API keys, especially if exposed
- **Repository Security**: The `config.ini` file is automatically ignored by git to prevent accidental commits

## Troubleshooting

### Common Issues

1. **"Connection failed"**
   - Check your Supabase URL and API key
   - Ensure your Supabase project is active
   - Verify network connectivity

2. **"Query interpretation failed"**
   - Check your OpenAI API key
   - Ensure you have sufficient OpenAI credits
   - Try rephrasing your query

3. **"Permission denied"**
   - Check your Supabase RLS policies
   - Ensure the anon key has necessary permissions
   - Consider using a service role key for development (not recommended for production)

4. **"Config file not found"**
   - Make sure you've copied `config.ini.example` to `config.ini`
   - Verify the file is in the `backend/` directory
   - Check file permissions

5. **"API keys exposed in git"**
   - The `config.ini` file should be ignored by git automatically
   - If accidentally committed, remove with: `git rm --cached backend/config.ini`
   - Rotate your API keys immediately if they were exposed

### Logs

- Backend logs are available in the console where you run the Python server
- Frontend logs are available in the browser console
- Adjust log levels in `config.ini`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Next.js](https://nextjs.org/) and [FastAPI](https://fastapi.tiangolo.com/)
- UI components from [shadcn/ui](https://ui.shadcn.com/)
- Database integration with [Supabase](https://supabase.com/)
- AI powered by [OpenAI](https://openai.com/)
- Package management with [uv](https://github.com/astral-sh/uv) 