# Karat - AI-Powered Financial Assistant

## Project Overview

Karat is an intelligent financial assistant that syncs with users' banking platforms to optimize saving ratios, maximize savings potential, and present banking data in an organized, actionable format. The application provides intelligent financial planning assistance that adapts to each user's unique financial situation and goals.

## The Problem

Financial insecurity affects 60% of Americans who cannot cover a $1,000 emergency expense. The core issue isn't lack of desire to save, it's the overwhelming complexity of financial planning. People struggle to:
- Manually track expenses across multiple accounts
- Predict future spending patterns and seasonal variations
- Balance competing financial priorities (bills, savings, discretionary spending)
- Optimize their savings rate without detailed financial expertise
- Understand where their money actually goes each month

## Our Solution

Karat combines:
1. **Banking Platform Integration** - Secure sync via Plaid API
2. **AI-Powered Savings Optimization** - ML-driven analysis and recommendations
3. **Organized Data Presentation** - Interactive dashboards and visualizations
4. **Intelligent Financial Planning** - Personalized, goal-oriented savings plans

## Project Structure

```
Karat/
├── backend/              # Python backend (Data Engineering & ML)
│   ├── api/             # REST API endpoints
│   ├── banking/         # Plaid integration
│   ├── ml/              # Machine learning models
│   ├── optimization/    # Savings optimization algorithms
│   ├── database/        # Database models and migrations
│   └── utils/           # Shared utilities
├── frontend/            # React/TypeScript frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── services/    # API services
│   │   └── utils/       # Frontend utilities
│   └── public/
├── database/            # Database schemas and migrations
├── docs/                # Documentation
├── scripts/             # Utility scripts
└── tests/               # Test files
```

## Development Phases

### Phase 1: Foundation & Banking Integration (Weeks 1-4)
- Banking platform sync via Plaid API
- Organized data presentation dashboard
- Transaction categorization

### Phase 2: AI-Powered Optimization & Intelligence (Weeks 5-10)
- Savings ratio optimization engine
- ML models for spending prediction
- AI-powered financial planning

### Phase 3: User Interface & Full Integration (Weeks 11-14)
- Complete end-to-end application
- AI assistant interface
- Full system integration

### Phase 4: Testing, Refinement & Presentation (Weeks 15-16)
- Beta testing and refinement
- Final presentation and demo

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- Plaid API account (Sandbox for development)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `backend/.env.example` to `backend/.env` and set:
- `DATABASE_URL` – PostgreSQL connection string (e.g. `postgresql://user:password@localhost:5432/karat_db`)
- `PLAID_CLIENT_ID` and `PLAID_SECRET` – from [Plaid Dashboard](https://dashboard.plaid.com) (use Sandbox for dev)
- `PLAID_ENVIRONMENT` – `sandbox` | `development` | `production`

Run the API:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:3000` and proxies `/api` to the backend.

### Plaid Connect Flow
1. Frontend calls `GET /api/banking/link_token?user_id=1` to get a `link_token`.
2. Initialize [Plaid Link](https://plaid.com/docs/link/) with that token; user connects their bank.
3. On success, frontend receives a `public_token`; call `POST /api/banking/connect` with `{"public_token": "...", "user_id": 1}`.
4. Backend exchanges the token, stores the item and accounts, and returns account list.
5. To sync transactions: `POST /api/banking/sync?account_id=<id>`.

## Team Structure

- **Data Engineering Team (2-3)**: Banking integration, database, data pipeline
- **ML Team (3-4)**: Forecasting models, optimization algorithms, RL system
- **Frontend/UX Team (2-3)**: Dashboards, UI components, user experience
- **Research Team (1-2)**: Economic data, benchmarks, documentation

## Data Sources

- **Primary**: Plaid API for banking data
- **Secondary**: Synthetic data for training, economic indicators (BLS, FRED), benchmark spending data

## License

[Add license information]

## Contributing

[Add contribution guidelines]
