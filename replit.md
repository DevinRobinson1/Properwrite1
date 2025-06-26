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
- **Professional Underwriting System**: Implements strict real estate appraisal standards for comparable sales analysis
- **Financial Calculator**: Generates investment metrics with ARV calculated from adjusted comparable sales data
- **Comparable Sales Generator**: Follows professional underwriting rules including:
  - Time-based filtering (90-365 days, prioritizing recent sales)
  - Geographic boundaries (0.25-1 mile radius within same neighborhood)
  - Property matching (type, style, square footage within reasonable ranges)
  - Monetary adjustments for bedroom, bathroom, and size differences
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
- June 19, 2025. Enhanced comparable sales analysis with professional underwriting rules including time-based filtering, geographic boundaries, property matching, and monetary adjustments
- June 19, 2025. Fixed XSS vulnerability in notification system and identified RapidAPI subscription requirements for additional data sources
- June 19, 2025. Implemented data integrity policy - removed all synthetic/mock data generation, application now displays only authentic property data from Rentcast API
- June 19, 2025. Added comprehensive Offer Strategy Calculator module with MAO cash offers, seller financing, novation, and subject-to acquisition strategies with real-time recalculation capabilities
- June 19, 2025. Implemented tabbed interface for offer strategy calculator with four distinct calculator types: Wholesale (MAO with Ackerman Method), Installment (Novation with seller psychology), Subject-To (creative financing with exit strategies), and Seller Finance (owner financing terms)
- June 19, 2025. Completed UI restructuring with fixed property information section at top featuring editable fields (beds, baths, sqft, ARV, repairs, rent) and tabbed calculator system below. Added real-time recalculation functionality and fixed JavaScript console errors (updateWholesalePercentage, toggleAdvancedFees functions)
- June 19, 2025. Restructured tabbed interface to show only strategy-specific content per tab while maintaining shared property information at top. Removed duplicate content across tabs, implemented clean presentation_clean.html template with focused tab content (Wholesale shows only wholesale calculations, Installment shows only installment components, etc.). Added real-time API endpoint for cross-tab recalculation and optional Compare All Strategies dashboard
- June 19, 2025. Major upgrade: Implemented smart external data pulling from Zillow, Redfin, and Realtor.com with property_data_service.py. Created enhanced UI (index_upgraded.html) with cleaner tab navigation, auto-populated property data, editable fields, and comprehensive side-by-side strategy comparison dashboard. Added app_upgraded.py with improved API endpoints for property analysis and strategy calculations
- June 19, 2025. Enhanced each strategy tab with comprehensive analysis tools: Wholesale (MAO breakdown, Ackerman offers, strategy analysis), Installment (psychology framework, execution timeline, risk assessment), Subject-To (PITI analysis, exit strategies, legal considerations), Seller Finance (financing options, projections, advantages). Simplified Compare All tab to high-level summary only
- June 19, 2025. Implemented comprehensive address validation and normalization system with Google Places API integration (address_validation_service.py) and enhanced property service (enhanced_property_service.py) featuring confidence scoring, fuzzy matching, and precise property identification across multiple data sources. Added multi-platform estimate display with authentic Zillow, Redfin, and Realtor.com branding and colors
- June 19, 2025. Completed comprehensive data integrity sweep: standardized all calculator function signatures for consistent data flow, implemented property data caching system (property_cache_service.py) for 10x performance improvement, archived orphaned files (app.py, app_simple.py, unused templates), fixed BeautifulSoup errors in external_property_service.py, and created data_integrity_service.py for ongoing system monitoring
- June 25, 2025. Switched from rapid APIs to Rentcast API for authentic property data and comparables. Implemented rentcast_service.py and rentcast_property_service.py for property estimates, comparable sales, and rental data. Added AI-powered strategy assistant (ai_strategy_assistant.py) with OpenAI integration for deal analysis and seller psychology insights. Created new API endpoints: /ai_strategy_insight and /ai_deal_analysis for intelligent investment recommendations
- June 25, 2025. Major backend restructure: Split system into dedicated Acquisitions Module (acquisitions_module.py) handling all seller offer strategies and deal structuring, and Dispositions Module (dispositions_module.py) managing exit strategies and investor packaging. Implemented AI Listing Generator (ai_listing_generator.py) using GPT-4o to create professional investor listings with market data, comparable sales, and financial analysis. Added new API endpoints: /acquisitions_analysis, /optimal_acquisition_strategy, /generate_offer_package, /dispositions_analysis, /generate_investor_listing, and /generate_listing_variations. Updated UI with new Dispositions tab featuring exit strategy analysis, AI listing generator buttons, and Rentcast fallback display for property valuations when other sources fail
- June 25, 2025. Implemented Interactive Property Risk Heatmap with color-coded zones (property_risk_analyzer.py). Features comprehensive risk analysis across 6 categories: market conditions, neighborhood quality, property condition, financial metrics, investment potential, and external factors. Added visual heatmap with clickable risk zones, detailed factor breakdowns, recommendations, and mitigation strategies. New API endpoint: /analyze_property_risk. Risk zones color-coded from green (very low risk) to red (very high risk) with weighted scoring system
- June 25, 2025. Implemented visual and structural separation between Acquisitions and Dispositions sections. Added section toggle buttons (🏗 Acquisitions / 🏠 Dispositions), color-coded headers (blue for acquisitions, purple-green gradient for dispositions), visual divider with lock icons, and reference values display in Dispositions showing locked acquisition costs. Acquisitions focused on seller offers, Dispositions focused on investor exit strategies. Enhanced UX prevents confusion between deal phases
- June 25, 2025. Completed comprehensive calculator refinements and objection handling integration. Enhanced property info header with larger pill inputs and color-coded financial fields. Updated Wholesale to single Assignment Fee input, refined Installments with editable commission sliders and new MAO formula (ARV - Repairs - 10K - Total Fees - Our Fee), streamlined Subject-To with cash flow focus and buying guide, enhanced Seller Finance with balloon payments and custom monthly overrides. Added Subject-To and Seller Finance objection handling sections in Dispositions with scripts from attached documents. Implemented Seller Psychology Framework in Acquisitions header
- June 25, 2025. Implemented Advanced Dispositions Logic with smart selling console. Added global editable inputs (Acquisition Cost, Repairs, PITI, Rent), customizable deal variables panel with sliders for wholesale %, MLS discount %, title %, and cash flow thresholds. Created enhanced exit strategy cards with color-coded backgrounds, hover effects, and detailed profit/timeline information. Integrated AI assistants (Generate Listing Copy, Suggest Best Exit, Objection Handler) powered by GPT-4o. Added AI Exit Strategy Assistant (ai_exit_strategy_assistant.py) for intelligent exit strategy recommendations with comprehensive analysis including ROI calculations, risk assessment, and strategy rankings. All exit formulas tied to real-time calculations with instant updates
- June 25, 2025. Implemented streamlined One-Click Offer Deep Dive Modal system to eliminate feature conflicts. Consolidated all overlapping features into single comprehensive modal triggered by clicking any offer amount or "Deep Dive Analysis" button. Modal provides strategy-specific content including detailed financial breakdowns, seller presentation scripts, objection handling, risk analysis, market context, and implementation timelines. Features copy functionality for easy sharing and professional modal design. Removed competing features to create focused, non-confusing user experience while maintaining clean individual tab navigation
- June 26, 2025. Fixed JavaScript tab navigation errors and implemented comprehensive Dynamic Fee Section for Installment/Novation calculator. Added 16 editable fee inputs with real-time recalculation including listing commissions, title fees, staging costs, photography, and optional line items. Features advanced settings toggle, tooltips, orange-themed UI, automatic MAO recalculation based on fee changes, and integrated formula: InstallmentMAO = FinalSalesPrice - TotalInstallmentFees - MinAcceptableProfit. Moved objection handling sections from dispositions to appropriate acquisition tabs. Fixed updateComparisonResults function and resolved missing recalculateSellerFinance function
- June 26, 2025. Removed duplicate gray closing costs section from Installment tab and consolidated to single orange dynamic fee calculator. Fixed broken HTML structure and positioned fee section correctly. Changed "Buyer Over-Ask Bonus" to "Installment Equitable Deposit" for clearer terminology. Removed duplicate seller psychology framework from fee section since it already appears above. Fixed JavaScript error with updateComparisonFromTabs function reference
- June 26, 2025. Updated novation profit calculation formula to: ARV - Repairs - Discount to Sell Fast - Total Combined Fees - Our Minimum Profit = Maximum Allowable Offer. This provides clearer cost accounting and ensures accurate profit calculations for installment/novation deals. Both recalculateInstallment() and recalculateNovationMAO() functions now use this standardized formula with real-time fee integration from the dynamic fee calculator
- June 26, 2025. Added Purchase Price Variables section to acquisitions with global adjustment controls: Wholesale ARV % slider (60-80%), Assignment Fee input, Min Profit Target input, and Discount to Sell input. Fixed NoneType error in strategy calculations for missing rent data. Global variables sync with individual tab controls and update all strategy calculations in real-time. Green-themed UI with 4 editable inputs positioned above Seller Psychology Framework

## User Preferences

Preferred communication style: Simple, everyday language.