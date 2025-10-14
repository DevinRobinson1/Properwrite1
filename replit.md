# properwrite.com

## Overview

properwrite.com is a Flask-based web application designed to generate professional property presentations for real estate investors. It enables users to input property details and receive comprehensive investment analysis reports, including financial projections, neighborhood insights, and presentation-ready formatting. Key capabilities include a renovation estimator for Fix & Flip projects, based on industry templates with detailed cost calculations, and an upgraded JV Deals Admin Panel offering enhanced team collaboration, user portfolio management, and real-time Zapier webhook notifications for deal status updates. The platform aims to streamline property investment analysis and presentation creation for real estate professionals.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions
- **Frontend Framework**: HTML templates with Jinja2.
- **Styling**: Tailwind CSS for responsive design.
- **Interactivity**: Vanilla JS for form validation, live editing, print/PDF, and share link generation.
- **Design Principles**: Modern, professional aesthetic with gradient backgrounds, clean cards, professional typography, color-coded sections (e.g., green for wholesale, blue for novation), and mobile-first responsiveness.
- **Navigation**: Sticky headers, mobile bottom navigation, horizontally scrollable tabs, and unified dashboard for user management.

### Technical Implementations
- **Backend Framework**: Flask (Python 3.11) with Gunicorn for production.
- **Session Management**: Flask's built-in sessions with a configurable secret key.
- **Property Analysis Engine**: Professional underwriting system for comparable sales, financial calculations (ARV, investment metrics), and mock data generation for neighborhood, school, and amenity insights.
- **Presentation Generator**: Creates professional layouts with financial overviews, property specifications, and local data, optimized for print/PDF.
- **Interactive Features**: Live editing of presentations, shareable links, and print/PDF export functionality.
- **AI Integration**: GPT-4o powered AI Control Center for objection handling, deal analysis, and listing generation, consolidated into a tabbed interface.
- **Billing System**: Comprehensive in-app subscription management, credit tracking, team management, and payment processing via Stripe and Coinbase Commerce (Bitcoin).
- **Security**: Global CSRF protection, rate limiting on sensitive endpoints, secure session management, and environment variable-based API key handling.
- **Caching**: Global property data cache using Redis and PostgreSQL fallback for performance and API cost reduction.
- **Admin System**: Dedicated JV-only admin panel and a unified main admin dashboard with live data, user management, affiliate tracking, and usage analytics.
- **Email Service**: Comprehensive email service infrastructure with SMTP, SendGrid, and Google Workspace integration for welcome emails, team invites, and notifications.

### Feature Specifications
- **Property Input**: Multi-field form with client and server-side validation.
- **Comparable Sales**: Smart Comps 2.0 with rule-adaptive search, progressive rule relaxation, and a 5-rule scoring system.
- **Renovation Estimator**: Professional-grade estimator based on industry templates for Fix & Flip and New Construction projects with detailed cost calculations and CSV export.
- **Offer Strategy Calculators**: Tabbed interface for Wholesale (MAO, Ackerman Method), Installment (Novation, equitable deposit), Subject-To (PITI analysis, cash flow), and Seller Finance (custom payment, balloon exit strategy).
- **JV Deals System**: Submission form with partner info, auto-underwriting, Zapier webhooks, and an enhanced admin panel.
- **User Dashboard**: Account overview, credit management, team management, settings, API integrations, and resources.

## External Dependencies

- **Python Packages**:
    - Flask
    - Flask-SQLAlchemy (for future database integration)
    - Gunicorn
    - psycopg2-binary (for future database integration)
    - email-validator
    - werkzeug (for password hashing)
    - OpenAI (for GPT-4o integration)
    - Redis (for caching)

- **Frontend Dependencies**:
    - Tailwind CSS (via CDN)
    - Font Awesome 6.0.0 (via CDN)
    - jQuery DataTables (for admin panel)
    - Chart.js (for admin dashboard visualizations)

- **APIs and Services**:
    - **Google Maps Platform**: Places Autocomplete API, Place Details API, Address Validation API.
    - **RapidAPI**:
        - Zillow API (via zillow-com1.p.rapidapi.com) for property data and estimates.
        - Realtor.com API (via realtor-search.p.rapidapi.com) for property data.
        - Redfin API (via redfin-com-data.p.rapidapi.com) for property data.
    - **RentCast API**: For alternative property valuations and rent data.
    - **Rentometer API**: For accurate rent data.
    - **Stripe**: For subscription management and credit card payments.
    - **Coinbase Commerce**: For Bitcoin payments.
    - **Zapier**: For webhook notifications and workflow automation.
    - **SendGrid/Gmail SMTP**: For email delivery.

- **Databases**:
    - PostgreSQL
    - Redis (for caching)