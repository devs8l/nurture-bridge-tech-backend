# InQuantic Microservice

Enterprise-grade FastAPI microservice built with InQuantic Foundry.

## Features

- ✅ FastAPI web framework
- 🔒 Zero-Trust security architecture
- 📊 Prometheus metrics & OpenTelemetry tracing
- 🏥 HIPAA, GDPR, SOC2 compliant
- 🔐 RBAC & multi-tenancy support
- 📧 Email service integration
- 🗄️ Database models & repositories
- 🧪 Comprehensive test coverage

## Development

### Local Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables in `.env`

3. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Testing

```bash
pytest
```

## Deployment

This application is configured for deployment on Vercel using serverless functions.

The application will be available at your Vercel deployment URL.

## Project Structure

- `app/` - Main application code
- `api/` - Serverless function handlers
- `db/` - Database models and migrations
- `config/` - Configuration management
- `security/` - RBAC and security utilities
- `tests/` - Test suite

## License

Proprietary - InQuantic.ai
