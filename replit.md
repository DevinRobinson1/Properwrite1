# Real Estate Investment Analyzer

## Overview

This is a Flask-based web application that generates professional property presentations for real estate investors. The application allows users to input property details and generates comprehensive investment analysis reports with financial projections, neighborhood insights, and presentation-ready formatting.

## System Architecture

### Frontend Architecture
- **Framework**: HTML templates with Jinja2 templating
- **Styling**: Tailwind CSS for responsive design and styling
- **JavaScript**: Vanilla JS for interactive features including:
  - Form validation
  - Live editing of generated presentations
  - Print/PDF functionality
  - Share link generation

### Backend Architecture
- **Framework**: Flask (Python 3.11)
- **Server**: Gunicorn for production deployment
- **Session Management**: Flask built-in sessions with configurable secret key
- **Data Processing**: Mock data generators for property analysis and financial calculations

### Template Structure
- `templates/index.html`: Main property input form
- `templates/presentation.html`: Generated property presentation page
- Static assets organized in `static/` directory

## Key Components

### Property Input System
- Multi-field form for property details (address, city, beds, baths, square footage, buy price)
- Form validation on both client and server side
- Error handling and user feedback

### Property Analysis Engine
- **Financial Calculator**: Generates investment metrics including buy price, rehab estimates, ARV (After Repair Value), and net profit projections
- **Title Generator**: Creates engaging property titles with emojis and descriptive language
- **Mock Data Systems**: 
  - Neighborhood data for major cities (Charlotte, Raleigh, Atlanta, Nashville)
  - School information with ratings and distances
  - Local amenities and points of interest

### Presentation Generator
- Professional property presentation layouts
- Financial overview sections
- Property specifications and highlights
- Nearby amenities and school data
- Print-optimized styling for PDF generation

### Interactive Features
- **Live Editing**: Users can edit generated content directly in the presentation
- **Share Functionality**: Generate shareable links for presentations
- **Print/PDF Export**: Optimized printing with proper page breaks

## Data Flow

1. **Input Collection**: User submits property details through the main form
2. **Data Processing**: Flask backend processes input and generates mock analysis data
3. **Financial Calculations**: Calculate investment metrics based on property characteristics
4. **Presentation Generation**: Render presentation template with calculated data
5. **User Interaction**: Allow live editing and sharing of generated presentations

## External Dependencies

### Python Packages
- **Flask 3.1.1**: Web framework
- **Flask-SQLAlchemy 3.1.1**: Database ORM (prepared for future database integration)
- **Gunicorn 23.0.0**: WSGI HTTP Server for production
- **psycopg2-binary 2.9.10**: PostgreSQL adapter (prepared for future database integration)
- **email-validator 2.2.0**: Email validation utilities

### Frontend Dependencies
- **Tailwind CSS**: Utility-first CSS framework (loaded via CDN)
- **Font Awesome 6.0.0**: Icon library (loaded via CDN)

### Mock Data Sources
- Neighborhood data for major southeastern US cities
- School ratings and distance calculations
- Local amenity databases
- Property comparable sales data

## Deployment Strategy

### Replit Configuration
- **Environment**: Python 3.11 with Nix package manager
- **Packages**: OpenSSL and PostgreSQL prepared for future database integration
- **Deployment Target**: Autoscale deployment
- **Production Server**: Gunicorn bound to 0.0.0.0:5000

### Development Workflow
- **Development**: Flask development server with debug mode
- **Production**: Gunicorn with reload capability for seamless updates
- **Port Configuration**: Application runs on port 5000 with automatic port detection

### Environment Variables
- `SESSION_SECRET`: Configurable session secret key (defaults to development key)

## Changelog

- June 19, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.