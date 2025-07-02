# Railway Environment Variables Template

## 🔑 Required Environment Variables for Biped Platform

### Core Application Settings
- `SECRET_KEY` = Generate a random 32+ character string
- `FLASK_ENV` = production
- `PYTHONPATH` = /app/backend
- `PORT` = 8080

### AI & Language Model APIs
- `OPENAI_API_KEY` = Your OpenAI API key
- `ANTHROPIC_API_KEY` = Your Anthropic API key
- `GROQ_API_KEY` = Your Groq API key
- `PERPLEXITY_API_KEY` = Your Perplexity API key
- `XAI_API_KEY` = Your xAI API key
- `GOOGLE_API_KEY` = Your Google API key
- `GEMINI_API_KEY` = Your Gemini API key

### Search & Data APIs
- `BING_SEARCH_API_KEY` = Your Bing Search API key
- `SERPER_API_KEY` = Your Serper API key
- `TAVILY_API_KEY` = Your Tavily API key
- `HUGGINGFACE_TOKEN` = Your Hugging Face token

### GitHub Integration
- `GITHUB_TOKEN` = Your GitHub personal access token
- `GITHUB_CLIENT_ID` = Your GitHub OAuth app client ID
- `GITHUB_USERNAME` = Your GitHub username
- `GITHUB_USEREMAIL` = Your GitHub email

### Google Services
- `GOOGLE_CLIENT_ID` = Your Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` = Your Google OAuth client secret

### Payment Processing (Stripe)
- `STRIPE_PUBLISHABLE_KEY` = Your Stripe publishable key
- `STRIPE_SECRET_KEY` = Your Stripe secret key
- `STRIPE_WEBHOOK_SECRET` = Your Stripe webhook secret

### Vector Database (Pinecone)
- `PINECONE_API_KEY` = Your Pinecone API key
- `PINECONE_ENVIRONMENT` = Your Pinecone environment

### Database Configuration
- `DATABASE_URL` = Auto-provided by Railway PostgreSQL service

### Security Settings
- `CORS_ORIGINS` = https://biped.up.railway.app
- `JWT_SECRET_KEY` = Generate a random secret key
- `SESSION_COOKIE_SECURE` = true
- `SESSION_COOKIE_HTTPONLY` = true

### Production Settings
- `FLASK_DEBUG` = false
- `LOG_LEVEL` = INFO

## 🔐 Security Notes

1. **Never commit API keys to version control**
2. **Use Railway's secure variable storage**
3. **Rotate keys regularly**
4. **Use test keys for development**
5. **Monitor API usage for anomalies**

## 📝 Instructions

1. Copy the variable names from this template
2. Add them to Railway with your actual secret values
3. Railway will securely store and inject them at runtime
4. Never share or expose these values publicly

