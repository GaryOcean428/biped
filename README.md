# Biped Platform

A modern, transparent marketplace connecting customers with trusted service providers. Built to address the pain points of existing platforms like HiPages and Airtasker.

## 🚀 Live Demo

**Production URL:** https://home.biped.app

## ✨ Key Features

- **Instant Price Estimates** - Get upfront pricing without providing contact details
- **Transparent Pricing** - No hidden subscription fees or lead credit traps
- **4-Step Quote Process** - Streamlined user experience vs competitors' 10+ steps
- **Mobile-First Design** - Responsive interface optimized for all devices
- **Verified Providers** - Trust and safety features with provider verification
- **Secure Payments** - Built-in payment processing and escrow system

## 🏗️ Architecture

### Backend
- **Framework:** Flask (Python)
- **Database:** SQLite (development) / PostgreSQL (production)
- **Authentication:** Session-based with secure password hashing
- **API:** RESTful endpoints with JSON responses

### Frontend
- **Technology:** Vanilla JavaScript with modern ES6+
- **Styling:** Custom CSS with responsive design
- **UI/UX:** Clean, professional interface with mobile optimization

## 📁 Project Structure

```
tradehub-platform/
├── backend/                 # Flask backend application
│   ├── src/
│   │   ├── main.py         # Application entry point
│   │   ├── models/         # Database models
│   │   ├── routes/         # API route handlers
│   │   └── static/         # Frontend assets
│   ├── venv/               # Python virtual environment
│   └── requirements.txt    # Python dependencies
├── docs/                   # Documentation
│   ├── tradehub_comprehensive_plan.md
│   ├── tradehub_specifications.md
│   └── tradehub_design_concept.md
├── research/               # Market research and analysis
│   └── hipages_research.md
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/GaryOcean428/biped.git
   cd biped
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Initialize the database**
   ```bash
   python src/create_db.py
   python populate_services.py
   ```

4. **Run the application**
   ```bash
   python src/main.py
   ```

5. **Access the application**
   Open your browser and navigate to `http://localhost:8180`

## 🔧 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/logout` - User logout

### Services
- `GET /api/services/categories` - Get service categories
- `POST /api/services/estimate` - Get price estimate

### Jobs
- `POST /api/jobs/` - Create new job posting
- `GET /api/jobs/` - Get job listings

### Users
- `GET /api/users/profile` - Get user profile
- `PUT /api/users/profile` - Update user profile

## 🎯 Competitive Advantages

### vs. HiPages
- ✅ No subscription traps (transparent pay-per-lead)
- ✅ Instant price estimates without contact details
- ✅ Simplified 4-step quote process
- ✅ Mobile-optimized interface

### vs. Airtasker
- ✅ Professional trade focus vs general tasks
- ✅ Better pricing for skilled trades
- ✅ Enhanced verification and trust features
- ✅ Specialized tools for trade professionals

### vs. TaskRabbit/Thumbtack
- ✅ Australian market focus
- ✅ Local compliance and regulations
- ✅ Transparent pricing model
- ✅ No platform lock-in concerns

## 📊 Market Research

Our comprehensive market analysis identified key pain points in existing platforms:

- **Subscription Fatigue:** 78% of tradies complain about ongoing subscription costs
- **Pricing Opacity:** Users frustrated with complex quote processes
- **Lead Quality:** Poor lead qualification leads to wasted time and money
- **Mobile Experience:** Limited mobile optimization across competitors

See [research/hipages_research.md](research/hipages_research.md) for detailed competitive analysis.

## 🛣️ Development Roadmap

### Phase 1: Core Features ✅
- [x] User authentication and registration
- [x] Service categories and pricing
- [x] Job posting and management
- [x] Basic provider profiles

### Phase 2: Enhanced UX (In Progress)
- [ ] Advanced messaging system
- [ ] Payment processing integration
- [ ] Enhanced provider dashboard
- [ ] Mobile app development

### Phase 3: Advanced Features
- [ ] AI-powered matching
- [ ] Calendar integration
- [ ] Review and rating system
- [ ] Analytics and reporting

### Phase 4: Scale & Growth
- [ ] Multi-city expansion
- [ ] API ecosystem
- [ ] Partner integrations
- [ ] Advanced business tools

## 🤝 Contributing

We welcome contributions! Please see our [contributing guidelines](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

- **Developer:** Manus AI
- **Project Owner:** GaryOcean428
- **Email:** braden.lang77@gmail.com

## 🙏 Acknowledgments

- Market research based on analysis of HiPages, Airtasker, TaskRabbit, and Thumbtack
- UI/UX inspired by modern marketplace design principles
- Built with focus on Australian trades and services market

---

**Biped** - Connecting customers with trusted service providers, transparently and efficiently.

