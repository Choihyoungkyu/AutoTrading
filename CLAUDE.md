# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AutoTrading is an automated trading system. This is an early-stage project currently in setup phase.

## 언어 규칙

- **코드**: 영어로 작성 (변수명, 함수명, 클래스명 등)
- **나머지**: 한국어로 표현 (문서, 커밋 메시지, 이슈 설명, 주석 등)
- **커밋메시지**: 커밋 메시지는 한국어로, 한 줄 요약 + 변경 이유

## Project Structure

The codebase is organized as follows (evolving):
- `src/` - Main application code
- `tests/` - Test suite
- `config/` - Configuration files (API keys, trading parameters, etc.)
- `docs/` - Project documentation
- `scripts/` - Utility scripts for setup, migration, etc.

## Development Commands

These commands will be available as the project develops:

```bash
# Setup
npm install          # Install dependencies (if Node.js based)
python -m venv venv  # Create virtual environment (if Python based)
source venv/bin/activate

# Development
npm run dev          # Start development server
npm run lint         # Run linter
npm run test         # Run test suite
npm run test -- path/to/test.spec.js  # Run single test

# Production
npm run build        # Build for production
npm start            # Start application
```

(Commands will be updated as the tech stack is finalized.)

## Key Architecture Patterns

As this project develops, follow these patterns:

1. **Configuration Management**: Keep sensitive data (API keys, credentials) in environment variables or `.env` files (never committed). Use configuration modules to centralize settings.

2. **API Integration**: Separate API clients and trading logic. Create dedicated modules for exchange APIs and internal service communication.

3. **Data Handling**: Trading data is time-sensitive. Use appropriate data structures and consider caching strategies where applicable.

4. **Error Handling**: Trading systems require robust error handling. Log failures comprehensively for debugging and auditing.

5. **Testing Strategy**: 
   - Unit tests for trading logic and calculations
   - Integration tests for API interactions (use mocks for external services in CI)
   - End-to-end tests for critical trading flows

6. **Documentation**: Each module should have a brief comment explaining its responsibility. Document any non-obvious trading logic or calculations.

## Tech Stack Considerations

- **Backend**: Node.js (Express/Fastify) or Python (FastAPI/Django) - choose based on team expertise
- **Database**: Consider PostgreSQL for transaction safety in financial systems
- **Message Queue**: Redis or similar for async tasks and event processing
- **Monitoring**: Structured logging and metrics collection for trading operations

## Important Guidelines

- **Never hardcode secrets**: Use environment variables for all credentials
- **Validate all inputs**: Especially important for trading parameters and market data
- **Version your APIs**: Maintain backwards compatibility when possible
- **Keep trading logic isolated**: Separate business logic from infrastructure concerns
- **Audit trail**: Log all significant actions for compliance and debugging

## Git Workflow

- Use descriptive commit messages
- Reference issues/tickets in commit messages when applicable
- Protect main branch with required reviews before merge

## Future Improvements

- Add CI/CD pipeline for automated testing and deployment
- Implement proper logging and monitoring infrastructure
- Set up documentation site (e.g., with MkDocs or Docusaurus)
- Create development guidelines document as conventions solidify
