# AI Learning Path Generator 🚀

A production-ready full-stack application that generates personalized learning paths powered by AI. Built with a modern hybrid architecture: React frontend on Vercel, and a Flask API with background workers on Render.

## 🏗️ Architecture (Hybrid Deployment)

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER FLOW                               │
└─────────────────────────────────────────────────────────────────┘

User Browser (React Frontend on Vercel)
        ↓
    POST /api/generate
        ↓
Backend API (Flask on Render) → Queue Task → Redis
        ↓                                      ↑
    Returns task_id                           │
        ↓                                      │
    Polls /api/status/{task_id}               │
        ↓                                      │
Background Worker (RQ on Render) ────────────┘
        │
        ├── OpenAI API (Path Generation)
        ├── Perplexity API (Job Market Data)
        └── Stores Result → PostgreSQL
                ↓
        GET /api/result/{task_id}
                ↓
        Display Learning Path on Frontend
```

### Components

- **Frontend**: React + Vite + TailwindCSS → Deployed on **Vercel**
- **Backend API**: Flask REST API → Deployed on **Render**
- **Worker**: RQ background worker → Deployed on **Render**
- **Queue/Cache**: Redis → Hosted on Redis Cloud
- **Database**: PostgreSQL → Hosted on Render
- **AI Services**: OpenAI GPT-4o-mini, Perplexity Sonar Pro

## Overview

This project uses advanced AI techniques and Retrieval-Augmented Generation (RAG) to create highly customized learning paths based on:
- **Topic selection and expertise level** - From beginner to expert
- **Individual learning style preferences** - Visual, auditory, reading/writing, or kinesthetic
- **Time availability and study preferences** - Minimal to intensive commitments
- **Specific learning goals and objectives** - Customized to your career aspirations
- **Real-time job market data** - Salary ranges, open positions, and trending employers

The system combines OpenAI's language models with vector database technology and a PostgreSQL backend to create detailed, personalized educational roadmaps with recommended resources, study schedules, progress tracking, and user authentication.

## Features

### Core Features
- 🤖 **AI-powered path generation** using LangChain and OpenAI GPT models
- 🎯 **Learning style adaptation** with support for visual, auditory, reading/writing, and kinesthetic learners
- 📊 **Difficulty assessment** of content using NLP analysis
- 📈 **Progress tracking** with milestone completion and status updates
- 📅 **Study scheduling** with customizable time commitments (minimal, moderate, substantial, intensive)
- 🔍 **Smart resource recommendations** tailored to learning style using OpenAI search API
- 💼 **Job market insights** with real-time salary data, open positions, and related roles
- 💾 **Vector database (RAG)** for efficient semantic search using ChromaDB
- 🌐 **Interactive web interface** with modern glassmorphic UI/UX
- 🎨 **Stunning visual design** with sci-fi themed glassmorphism, neon accents, and smooth animations

### User Features
- 👤 **User authentication** with email/password and Google OAuth integration
- 💾 **Save and manage learning paths** with persistent storage
- 📊 **Personal dashboard** to track all your learning paths and progress
- ✅ **Milestone tracking** with completion status and notes
- 🗄️ **Archive paths** to keep your dashboard organized
- 💬 **Popup AI chatbot widget** with three modes:
  - 💬 General Chat - Ask questions and get AI responses
  - 🎯 Path Creation - Generate learning paths conversationally
  - 🔍 Research - Explore skills, salaries, and career insights
- 📊 **Animated progress card** during path generation with 4 stages:
  - 🔍 Analyzing Requirements
  - 🤖 AI Processing
  - 📚 Curating Resources
  - ✨ Finalizing Path
- 🎨 **Collapsible skills database** with 2025 emerging AI roles
- ✅ **Resource checkboxes** to track completion (saves to database)
- 📱 **Responsive design** that works on desktop and mobile
- ✨ **Real-time username availability** checking with AJAX validation
- 🔐 **Password strength meter** with visual feedback
- 🎯 **Smart username suggestions** based on email
- 🌓 **Dark/Light theme toggle** with persistent preference

### Technical Features
- 🔄 **Multiple AI provider support** (OpenAI primary, DeepSeek legacy support)
- 🎨 **Pydantic schema validation** for reliable AI outputs
- 🔐 **Secure authentication** with Flask-Login and OAuth
- 🗃️ **PostgreSQL database** with SQLAlchemy ORM
- 🚀 **Production-ready** with Gunicorn and deployment guides
- 🧪 **Development mode** with API stubbing for UI development

### Observability
- 🕵️ **LLM Tracing with LangSmith**: End-to-end tracing of OpenAI and Perplexity API calls to debug prompts, view outputs, and monitor latency.
- 📊 **Metrics Monitoring with Weights & Biases (W&B)**: Logs key performance indicators, including:
  - **Cost Tracking**: `llm_cost_usd` and `perplexity_cost_usd` to monitor spending.
  - **Performance**: `llm_latency_ms` and `perplexity_latency_ms` to track response times.
  - **Token Usage**: `llm_tokens`, `perplexity_prompt_tokens`, and `perplexity_completion_tokens`.

## 🚀 Deployment Status

### Production Services (Render)
- ✅ **Backend API**: Deployed and running
- ✅ **Background Worker**: Deployed and running  
- ✅ **PostgreSQL Database**: Provisioned and connected
- ✅ **Redis**: Connected to Redis Cloud
- 🔄 **Frontend**: Ready to push to GitHub

### Recent Updates
- ✅ Popup AI chatbot widget integrated
- ✅ Animated progress card for path generation
- ✅ Collapsible skills database with emerging AI roles
- ✅ Resource completion tracking with checkboxes
- ✅ Dark/Light theme toggle
- ✅ Mobile responsive design improvements

## Tech Stack

### Backend
- **Framework**: Flask (Python web framework)
- **Web Server**: Gunicorn (production WSGI server)
- **Database**: PostgreSQL with Flask-SQLAlchemy ORM
- **Authentication**: Flask-Login, Flask-Dance (Google OAuth)
- **Migrations**: Flask-Migrate (Alembic)
- **Forms**: Flask-WTF with email validation

### AI/ML
- **LLM Framework**: LangChain with langchain-openai
- **AI Provider**: OpenAI (GPT-3.5-turbo, GPT-4)
- **Vector Database**: ChromaDB for semantic document storage
- **Embeddings**: SentenceTransformers for text vectorization
- **RAG**: FAISS-CPU for efficient similarity search
- **Schema Validation**: Pydantic for structured AI outputs
- **ML Libraries**: scikit-learn, numpy, pandas

### Frontend
- **Templates**: Jinja2 (Flask templating)
- **Styling**: Custom Glassmorphic CSS with Tailwind CSS utilities
- **Design System**: Eye-friendly purple-pink gradients with comfortable rgba colors
- **UI Components**: Glass cards, neon buttons, gradient text effects, collapsible chat
- **Animations**: Smooth transitions, fade-ins, pulse glows, floating elements
- **Scrollbars**: Custom styled with gradient glassmorphic design
- **JavaScript**: Vanilla JS for real-time validation, SSE streaming, chat interactions
- **Icons**: SVG icons with modern styling
- **Real-time Updates**: Server-Sent Events (SSE) for live progress tracking

### DevOps & Tools
- **Environment**: python-dotenv for configuration
- **Document Processing**: unstructured, pypandoc
- **Testing**: pytest
- **Deployment**: Render.com, Docker support

## Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/arun3676/ai-learning-path-generator.git
cd ai-learning-path-generator
```

2. **Create a virtual environment** (recommended)
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
# Copy the example file
cp .env.example .env

# Edit .env with your API keys and configuration
# Required: OPENAI_API_KEY
# Optional: SECRET_KEY, DATABASE_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
```

5. **Initialize the database**
```bash
# Set Flask app environment variable
$env:FLASK_APP = "web_app:create_app"  # Windows PowerShell
export FLASK_APP=web_app:create_app    # macOS/Linux

# Initialize migrations (first time only)
python -m flask db init

# Create migration for current models
python -m flask db migrate -m "Initial migration"

# Apply migrations to database
python -m flask db upgrade
```

6. **Run the application**
```bash
# Development mode
python run_flask.py

# Or using the main runner
python run.py
```

7. **Open your browser** and navigate to `http://localhost:5000`

## 🚀 Phase 2: Modern React Frontend

A production-ready React frontend with real-time progress tracking and beautiful glassmorphic UI.

### Quick Start (Frontend)

```powershell
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create .env file
Copy-Item .env.example .env

# Edit .env with your API URL:
# VITE_API_URL=http://localhost:5000  (for local development)
# VITE_API_URL=https://ai-learning-path-api.onrender.com  (for production)

# Start development server
npm run dev

# Open browser to http://localhost:3000
```

Or use the automated setup script:
```powershell
cd frontend
.\setup.ps1
```

### Frontend Features

- ✨ **Real-time Progress Tracking** - Watch your path being generated live
- 🎨 **Glassmorphic Design** - Modern UI with backdrop blur effects
- 📱 **Fully Responsive** - Works on desktop, tablet, and mobile
- 💼 **Job Market Insights** - Salary data, open positions, and careers
- 📥 **Export Functionality** - Download learning paths as JSON
- ⚡ **Lightning Fast** - Vite build tool for instant HMR

### Frontend Tech Stack

- React 18 + Vite 5
- TailwindCSS 3 + shadcn/ui
- Axios for API calls
- Lucide React for icons

### Deployment

**Deploy to Vercel:**
1. Push to GitHub
2. Import repo to Vercel
3. Set root directory to `frontend`
4. Add env var: `VITE_API_URL=https://ai-learning-path-api.onrender.com`
5. Deploy!

See `PHASE2_DEPLOYMENT_GUIDE.md` for complete instructions.

## Project Structure

```
ai-learning-path-generator/
│
├── src/                          # Core AI and business logic
│   ├── agent.py                  # AI agent with RAG capabilities
│   ├── learning_path.py          # Learning path generation logic
│   ├── direct_openai.py          # Direct OpenAI API integration
│   ├── ml/                       # Machine learning components
│   │   ├── model_orchestrator.py # AI model management and orchestration
│   │   ├── job_market.py         # Job market data fetching
│   │   └── resource_search.py    # Resource search using OpenAI
│   ├── data/                     # Data management and storage
│   │   ├── document_store.py     # Document storage and retrieval
│   │   ├── vector_store.py       # Vector database interface
│   │   └── resources.py          # Educational resource handling
│   ├── agents/                   # Specialized AI agents
│   └── utils/                    # Utility functions
│       ├── config.py             # Configuration management
│       └── helpers.py            # Helper functions
│
├── backend/                      # Phase 1: Backend API (Flask)
│   ├── app.py                    # Main Flask app
│   ├── routes.py                 # API endpoints (/generate, /status, /result)
│   ├── requirements.txt          # Minimal dependencies
│   ├── Procfile                  # Render deployment config
│   └── Dockerfile                # Docker configuration
│
├── worker/                       # Phase 1: Background Worker (RQ)
│   ├── celery_app.py             # RQ/Celery configuration
│   ├── tasks.py                  # Task definitions (generate_learning_path)
│   ├── requirements.txt          # All ML/AI dependencies
│   ├── Procfile                  # Render worker config
│   └── Dockerfile                # Docker configuration
│
├── frontend/                     # Phase 2: React Frontend (NEW!)
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/               # shadcn/ui components
│   │   │   ├── LearningPathForm.jsx    # Input form
│   │   │   ├── ProgressTracker.jsx     # Real-time progress
│   │   │   └── LearningPathResult.jsx  # Results display
│   │   ├── lib/
│   │   │   ├── api.js            # API client
│   │   │   └── utils.js          # Utilities
│   │   ├── App.jsx               # Main app
│   │   ├── main.jsx              # Entry point
│   │   └── index.css             # Global styles
│   ├── package.json              # Dependencies
│   ├── vite.config.js            # Vite config
│   ├── tailwind.config.js        # TailwindCSS config
│   ├── vercel.json               # Vercel deployment
│   ├── setup.ps1                 # Windows setup script
│   └── README.md                 # Frontend docs
│
├── web_app/                      # Legacy: Flask web application
│   ├── __init__.py               # App factory (create_app)
│   ├── app.py                    # Legacy entry point
│   ├── models.py                 # Database models
│   ├── main_routes.py            # Main routes
│   ├── auth_routes.py            # Authentication routes
│   ├── static/                   # Static assets
│   └── templates/                # HTML templates (Jinja2)
│
├── migrations/                   # Database migrations (Alembic)
├── vector_db/                    # Vector database storage (ChromaDB)
├── learning_paths/               # Saved learning paths (JSON files)
│
├── config.py                     # Application configuration
├── run.py                        # Main application runner
├── run_flask.py                  # Flask application runner (production)
├── initialize_db.py              # Database initialization script
├── Procfile                      # Deployment configuration (Render/Heroku)
├── requirements.txt              # Python dependencies
├── .env.example                  # Example environment variables
├── .gitignore                    # Git ignore rules
├── README.md                     # Project documentation
└── LICENSE                       # MIT License
```

## How It Works

### Application Flow

1. **User Input**: User fills out a form with their learning preferences (topic, expertise level, learning style, time commitment)
2. **AI Processing**: The `LearningPathGenerator` constructs a detailed prompt with Pydantic schema instructions
3. **LLM Generation**: `ModelOrchestrator` calls OpenAI API to generate a structured learning path
4. **Validation**: Response is validated against the `LearningPath` Pydantic model
5. **Enrichment**: System fetches job market data and searches for relevant resources for each milestone
6. **Storage**: Path is saved to PostgreSQL database (for logged-in users) or session (for guests)
7. **Display**: User sees their personalized learning path with milestones, resources, and career insights

### Key Components

- **`LearningPathGenerator`** (`src/learning_path.py`): Core class for generating learning paths
- **`ModelOrchestrator`** (`src/ml/model_orchestrator.py`): Manages AI model interactions and provider switching
- **`LearningAgent`** (`src/agent.py`): Advanced agent with RAG capabilities for complex interactions
- **Database Models** (`web_app/models.py`): User, UserLearningPath, LearningProgress
- **Routes** (`web_app/main_routes.py`, `web_app/auth_routes.py`): Flask endpoints for web interface

## API Usage

### Programmatic Access

```python
from src.learning_path import LearningPathGenerator

# Initialize generator
generator = LearningPathGenerator(api_key="your-openai-api-key")

# Generate learning path
learning_path = generator.generate_path(
    topic="Machine Learning",
    expertise_level="intermediate",
    learning_style="visual",
    time_commitment="moderate",
    goals=["Build ML models", "Deploy to production"]
)

# Save the path
file_path = generator.save_path(learning_path)
print(f"Learning path saved to: {file_path}")

# Access path data
print(f"Title: {learning_path.title}")
print(f"Duration: {learning_path.duration_weeks} weeks")
print(f"Total Hours: {learning_path.total_hours}")

for milestone in learning_path.milestones:
    print(f"\n{milestone.title}")
    print(f"  Hours: {milestone.estimated_hours}")
    print(f"  Skills: {', '.join(milestone.skills_gained)}")
```

## Interactive Chat System

### Two-Mode AI Assistant

The application features an **interactive AI chatbot** with two specialized modes:

#### 1. **Chat Mode** (General Conversation)
- Answer questions about learning and education
- Provide study tips and motivation
- Explain platform features
- General educational discussions

#### 2. **Interactive Path Mode** (Path Creation & Modification)
- **Create paths conversationally**: "Create a learning path for Python"
- **Get modification guidance**: Explains how to adjust pace, add resources, skip milestones
- **Smart topic extraction**: Understands natural language requests
- **Planning assistance**: Helps structure learning goals

### Chat Features
- **Eye-friendly design**: Soft purple-pink gradients, no harsh colors
- **Collapsible interface**: Click header to toggle on result pages
- **Message styling**: 
  - User messages: Purple-pink gradient background
  - AI messages: Dark slate with comfortable text color
- **Real-time responses**: Instant AI-powered replies
- **Consistent across pages**: Same experience on homepage and result pages

### SSE Progress Tracking

Real-time **Server-Sent Events (SSE)** provide live updates during path generation:

- **Animated progress modal** with percentage indicator
- **Status messages**: "Analyzing topic...", "Building curriculum...", etc.
- **Smooth animations**: Progress bar fills from 0% to 100%
- **Cancel option**: Stop generation at any time
- **Auto-redirect**: Seamlessly navigates to results when complete

## Design System

### Glassmorphic UI Theme

The application features a modern **glassmorphic design** with an eye-friendly aesthetic:

- **Color Palette** (Eye-Friendly):
  - Background: Deep navy gradients (`rgba(15, 23, 42)` to `rgba(30, 27, 75)`)
  - Purple Accent: `rgba(139, 92, 246)` (soft, comfortable)
  - Pink Accent: `rgba(236, 72, 153)` (warm, inviting)
  - Text: Light slate `rgba(226, 232, 240)` (high readability)
  - Glass effect: Semi-transparent with backdrop blur and soft borders
  - **No harsh whites or blacks**: All colors use rgba with comfortable opacity

- **UI Components**:
  - `.glass-card`: Translucent cards with blur effect
  - `.glass-input` / `.glass-select`: Form controls with glass styling
  - `.neon-btn`: Outlined buttons with glow effects
  - `.gradient-text`: Cyan-to-purple gradient text
  - Custom scrollbars with gradient styling

- **Animations**:
  - Smooth scroll behavior
  - Fade-in effects for page elements
  - Pulse glow for interactive elements
  - Hover transformations with scale and shadow

- **Typography**:
  - Font: Inter (Google Fonts)
  - Smooth antialiasing for crisp text rendering

### Accessibility Features
- High contrast neon colors on dark backgrounds
- Softer palette to reduce eye strain
- Smooth scrolling for better UX
- Responsive design for all screen sizes

## Deployment

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional - Flask Configuration
SECRET_KEY=your_secret_key_here
FLASK_ENV=development
DEBUG=True
FLASK_APP=web_app:create_app

# Optional - Database (defaults to SQLite)
DATABASE_URL=postgresql://user:password@localhost/dbname
# For local SQLite: sqlite:///app.db

# Optional - Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Optional - Development Mode (stubs API calls)
DEV_MODE=False
```

### Production Deployment (Render.com)

1. **Push to GitHub**: Ensure your code is in a GitHub repository

2. **Create Web Service** on Render:
   - Choose "New → Web Service"
   - Connect your GitHub repository
   - Render auto-detects the `Procfile`

3. **Configure Environment Variables**:
   - Go to Settings → Environment
   - Add: `OPENAI_API_KEY`, `SECRET_KEY`, `DATABASE_URL` (PostgreSQL)
   - Optionally add Google OAuth credentials

4. **Deploy**: Click "Create Web Service"
   - Render installs dependencies from `requirements.txt`
   - Starts Gunicorn on port 10000
   - Your app is live!

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p vector_db learning_paths

# Expose port
EXPOSE 5000

# Run with Gunicorn
CMD gunicorn run_flask:app -b 0.0.0.0:$PORT --workers 2 --timeout 120
```

**Build and run**:
```bash
docker build -t ai-learning-path-generator .
docker run -p 5000:5000 \
  -e PORT=5000 \
  -e OPENAI_API_KEY=your_key \
  -e SECRET_KEY=your_secret \
  ai-learning-path-generator
```

## Testing

Run the test suite:
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_learning_path.py

## Deployment

The application is production-ready and can be deployed to Render.com with Redis caching support.

###  Deploy to Render (Recommended)

**Quick Start**: Follow the comprehensive deployment guide in [`RENDER_DEPLOYMENT_GUIDE.md`](RENDER_DEPLOYMENT_GUIDE.md)

#### Prerequisites:
- GitHub repository (public or connected to Render)
- OpenAI API key
- Render account (free tier available)

#### Deployment Steps:

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Create Web Service on Render**
   - Connect your GitHub repository
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

3. **Add Environment Variables**
   - See [`RENDER_ENV_VARIABLES.md`](RENDER_ENV_VARIABLES.md) for complete list
   - Minimum required: `OPENAI_API_KEY`, `FLASK_SECRET_KEY`

4. **Add Redis Add-on**
   - Click "Add Redis" in Render dashboard
   - Free tier: 25MB (sufficient for most use cases)
   - Paid tier: $7/month for 256MB

5. **Deploy & Verify**
   - Render will automatically build and deploy
   - Visit your app URL: `https://your-app-name.onrender.com`

#### Cost Options:

| Plan | Web Service | Redis | Database | Total/Month |
|------|-------------|-------|----------|-------------|
| **Free Tier** | Free (spins down) | Free (25MB) | SQLite | $0 |
| **Budget** | $7 (Starter) | Free (25MB) | SQLite | $7 |
| **Recommended** | $7 (Starter) | $7 (256MB) | SQLite | $14 |
| **Full Production** | $7 (Starter) | $7 (256MB) | $7 (PostgreSQL) | $21 |

#### Deployment Documentation:

**Phase 1 (Backend + Worker):**
| File | Purpose |
|------|---------|
| `PHASE1_README.md` | Phase 1 implementation overview |
| `HYBRID_DEPLOYMENT_GUIDE.md` | Deploy backend API and worker to Render |
| `DEPLOYMENT_STATUS.md` | Current deployment status |
| `backend/Procfile` | Backend API configuration |
| `worker/Procfile` | Worker configuration |

**Phase 2 (Frontend):**
| File | Purpose |
|------|---------|
| `PHASE2_README.md` | Phase 2 implementation overview |
| `PHASE2_DEPLOYMENT_GUIDE.md` | Deploy React frontend to Vercel |
| `PHASE2_COMPLETE.md` | Phase 2 completion summary |
| `frontend/README.md` | Frontend-specific documentation |
| `frontend/vercel.json` | Vercel deployment config |
| `frontend/setup.ps1` | Automated Windows setup script |

**Legacy Files:**
| File | Purpose |
|------|---------|
| `Procfile` | Legacy monolithic deployment |
| `RENDER_DEPLOYMENT_GUIDE.md` | Legacy deployment instructions |
| `RENDER_ENV_VARIABLES.md` | Environment variables reference |
| `PRE_DEPLOYMENT_CHECKLIST.md` | Pre-deployment checklist |

#### Important Notes:
- ✅ Redis caching is fully configured and production-ready
- ✅ Automatic HTTPS with free SSL certificate
- ✅ Zero-downtime deployments (on paid plans)
- ✅ Automatic deploys on git push
- ⚠️ Never commit `.env` file to GitHub
- ⚠️ Generate a strong `FLASK_SECRET_KEY` for production

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Arun Kumar Chukkala**
- Email: arunkiran721@gmail.com
- GitHub: [@arun3676](https://github.com/arun3676)
- Project Link: [https://github.com/arun3676/ai-learning-path-generator](https://github.com/arun3676/ai-learning-path-generator)

## Recent Updates

### Latest Features (January 2025)
- 💬 **Popup AI Chatbot Widget** - Bottom-right floating chat with 3 modes:
  - General Chat for questions
  - Path Creation for learning paths
  - Research for skills and salaries
- 📊 **Animated Progress Card** - Real-time visual feedback during path generation:
  - 4-stage progress indicator
  - Shimmer effects on progress bar
  - Step-by-step status updates
- 🎨 **Collapsible Skills Database** - Accordion UI with 2025 emerging AI roles:
  - AI Ethics Specialist
  - Prompt Engineer
  - AI Safety Researcher
  - Multimodal AI Developer
  - And 20+ more roles
- ✅ **Resource Completion Tracking** - Checkboxes on each resource:
  - Saves to database for logged-in users
  - LocalStorage fallback for guests
  - Visual dimming when completed
- 🌓 **Dark/Light Theme Toggle** - Persistent theme preference
- 📱 **Mobile Responsive** - Optimized for all screen sizes

### UI/UX Enhancements
- ✨ Complete glassmorphic design system implementation
- 🎨 Pink/purple/cyan neon color scheme
- 📜 Custom gradient scrollbars with smooth scrolling
- 🔄 Real-time AJAX username availability checking
- 💪 Password strength meter with visual feedback
- 🎯 Smart username suggestions from email
- 🎭 Smooth animations and transitions throughout

### Database & Authentication
- 🗄️ PostgreSQL with SQLAlchemy ORM
- 🔐 Flask-Login authentication
- 🔄 Google OAuth integration
- 📝 Resource progress tracking table
- 💾 Learning path persistence

## Troubleshooting

### Common Issues

**SQLAlchemy OperationalError (no such column)**
- Run database migrations: `python -m flask db upgrade`
- If migrations are out of sync, regenerate: `python -m flask db migrate`

**Flask CLI not recognized on Windows**
- Use: `python -m flask` instead of `flask`
- Set environment variable: `$env:FLASK_APP = "web_app:create_app"`

**Username always shows as taken**
- Clear browser cache and hard refresh (Ctrl+Shift+R)
- Check that `/auth/check-username` endpoint returns `available: true/false`

## Documentation

Detailed documentation for recent features:

- **[INTERACTIVE_CHAT_GUIDE.md](INTERACTIVE_CHAT_GUIDE.md)** - Complete guide to the interactive chat system
- **[CHAT_AND_SSE_FIXES.md](CHAT_AND_SSE_FIXES.md)** - Technical details of chat UI and SSE implementation
- **[RESULT_PAGE_FIXES.md](RESULT_PAGE_FIXES.md)** - Career AI Assistant redesign and styling fixes
- **[LEARNING_PATH_MODIFICATION_GUIDE.md](LEARNING_PATH_MODIFICATION_GUIDE.md)** - How to modify learning paths
- **[RESOURCE_FIXES_APPLIED.md](RESOURCE_FIXES_APPLIED.md)** - Resource relevance improvements
- **[RENDER_DEPLOYMENT_GUIDE.md](RENDER_DEPLOYMENT_GUIDE.md)** - Complete Render deployment guide
- **[RENDER_ENV_VARIABLES.md](RENDER_ENV_VARIABLES.md)** - Environment variables quick reference
- **[PRE_DEPLOYMENT_CHECKLIST.md](PRE_DEPLOYMENT_CHECKLIST.md)** - Pre-deployment checklist

## Acknowledgments

- OpenAI for providing the GPT models
- LangChain for the LLM framework
- Flask community for the excellent web framework
- Glassmorphism design inspiration from modern UI trends
- All contributors and users of this project

---

**Built with ❤️ using Python, Flask, AI, and Eye-Friendly Glassmorphic Design**
