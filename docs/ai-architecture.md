# Biped AI Architecture Documentation

## Overview

The Biped platform features an advanced multi-provider AI architecture designed for Railway deployment, providing intelligent job matching, demand prediction, and transparent algorithm explanations.

## Multi-Provider AI Architecture

### Supported Providers

According to `AGENT.md`, the following AI providers are approved:

#### Primary Providers
- **OpenAI**: GPT-4.1, gpt-4.1-mini, o1, GPT-4o
- **Anthropic**: Claude-4-Opus, Claude-4-Sonnet, Claude-Code, Claude 3.5 Sonnet  
- **Google**: Gemini-2.5-pro, Gemini-2.5-flash, Gemini multimodal
- **xAI**: Grok 3
- **DeepSeek**: R1
- **Groq**: Fast inference models
- **Perplexity**: Research and real-time tasks

#### Deprecated/Disallowed
- GPT-3.5, GPT-4 base variants
- Claude 2.x, Claude 3.x (except 3.5 Sonnet)
- Experimental/beta/legacy models

### AI Service Router

The `AIServiceRouter` class dynamically selects providers based on task type:

```python
# Task-to-Provider Routing
COMPLEX_ANALYSIS -> OpenAI (GPT-4.1)
CONTENT_MODERATION -> Anthropic (Claude-4-Sonnet)
REAL_TIME_CHAT -> Groq (Fast inference)
RESEARCH_TASKS -> Perplexity (Real-time research)
CREATIVE_TASKS -> xAI (Grok 3)
MULTIMODAL_TASKS -> Google (Gemini multimodal)
JOB_MATCHING -> OpenAI (GPT-4.1)
DEMAND_PREDICTION -> Google (Gemini-2.5-pro)
PRICING_OPTIMIZATION -> Anthropic (Claude-4-Sonnet)
```

## Core AI Features

### 1. Enhanced Job Analysis

**Endpoint**: `POST /api/ai/analyze-job`

Combines traditional NLP with AI provider analysis:
- Skill extraction and categorization
- Complexity assessment  
- Budget estimation with confidence intervals
- Urgency detection
- Transparency reporting

**Response Example**:
```json
{
  "analysis": {
    "budget_estimate": 640.0,
    "budget_range": [448.0, 832.0],
    "complexity": "medium", 
    "confidence": 0.85,
    "estimated_hours": 8,
    "skills": ["electrical"],
    "urgency": "asap",
    "ai_provider": "openai",
    "transparency": {
      "algorithm_used": "semantic_nlp_analysis",
      "confidence_score": 0.85,
      "factors_considered": [
        "job_description_complexity",
        "skill_requirements",
        "urgency_indicators", 
        "budget_estimation_markers"
      ]
    }
  }
}
```

### 2. Intelligent Job Matching

**Endpoint**: `POST /api/ai/find-matches`

Advanced semantic matching with transparency:
- Multi-factor scoring (skills, location, budget, availability, quality)
- Detailed explanations for each match
- Confidence breakdown per factor
- Provider-specific insights

**Scoring Algorithm**:
- **Skill Match (30%)**: Semantic analysis of required vs provider skills
- **Location Score (20%)**: Distance and travel time calculation
- **Budget Compatibility (20%)**: Rate alignment with project budget  
- **Availability Score (15%)**: Real-time availability matching
- **Quality Score (15%)**: Provider rating and experience

### 3. Demand Prediction

**Endpoint**: `POST /api/ai/predict-demand`

AI-enhanced forecasting:
- Historical pattern analysis
- Seasonal trend detection
- Market indicator integration
- Confidence intervals and accuracy metrics

### 4. Algorithm Transparency

**Endpoint**: `GET /api/ai/transparency`

Complete transparency reporting:
- Provider availability status
- Routing strategy explanation
- Algorithm weights and versions
- Ethical AI compliance status
- Performance metrics

## Railway Deployment Configuration

### Environment Variables

```bash
# AI Provider API Keys (optional - fallback to mock if not set)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key  
GOOGLE_API_KEY=your_google_key
XAI_API_KEY=your_xai_key
GROQ_API_KEY=your_groq_key
PERPLEXITY_API_KEY=your_perplexity_key
DEEPSEEK_API_KEY=your_deepseek_key

# Core Application
SECRET_KEY=your-secret-key-32-chars-minimum
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
ENVIRONMENT=production
```

### Dependencies

All AI dependencies are included in `requirements.txt`:
```
scikit-learn==1.7.0
geopy==2.4.1  
numpy==2.3.1
```

### Health Checks

Railway health monitoring includes AI status:
```json
{
  "status": "healthy",
  "ai_providers": {
    "openai": true,
    "anthropic": false, 
    "google": true
  },
  "enhanced_ai": true,
  "traditional_ai": true
}
```

## Security Features

### Input Validation
- Comprehensive sanitization using `InputValidator` class
- XSS prevention and SQL injection protection
- Rate limiting on AI endpoints
- Request size limits

### API Security  
- CORS configuration for Railway domains
- Security headers (CSP, HSTS, X-Frame-Options)
- JWT-based authentication ready
- Error handling without information leakage

### Ethical AI
- Bias mitigation active
- Fairness checks enabled
- Human oversight available
- Complete audit trail

## Performance Optimization

### Response Times
- Groq: < 0.1s (real-time tasks)
- OpenAI: ~0.5s (balanced analysis)
- Anthropic: ~0.8s (detailed analysis)
- Fallback: < 0.1s (mock responses)

### Caching Strategy
- Redis caching for frequently requested analyses
- Provider response caching with TTL
- Algorithm result memoization

### Scalability
- Stateless design for horizontal scaling
- Provider load balancing
- Graceful degradation when providers unavailable

## Integration Patterns

### Hybrid AI Approach
Combines traditional algorithms with AI providers:
1. Traditional analysis provides baseline
2. AI provider enhances with semantic understanding
3. Results merged with transparency tracking
4. Fallback to traditional if AI unavailable

### Error Handling
- Provider failures handled gracefully
- Automatic fallback to available providers
- Mock responses when no providers configured
- Detailed error logging for debugging

## Testing

### AI Test Server
Standalone server for AI feature validation:
```bash
cd backend/src
python ai_test_server.py
```

**Test Endpoints**:
- `GET /api/health` - System status
- `POST /api/ai/analyze-job` - Job analysis
- `POST /api/ai/find-matches` - Provider matching
- `GET /api/ai/transparency` - Algorithm transparency
- `POST /api/ai/predict-demand` - Demand forecasting

### Unit Tests
All AI components include comprehensive tests:
- Provider routing logic
- Fallback mechanisms  
- Transparency reporting
- Error handling

## Monitoring & Analytics

### Performance Metrics
- Response times per provider
- Accuracy rates for predictions
- User satisfaction scores
- Provider availability uptime

### Algorithm Transparency
- All scoring weights exposed
- Confidence levels provided
- Decision explanations available
- Audit trail maintained

## Future Enhancements

### Planned Features
- Computer vision integration for work verification
- Real-time provider recommendation updates  
- Advanced market trend analysis
- Multi-language support

### AI Model Updates
- Regular model evaluation and updates
- A/B testing for algorithm improvements
- Performance benchmarking
- User feedback integration