"""
AI Listing Generator - GPT-4o powered property listing creation
Creates compelling investor-focused property listings with market data and analysis
"""

import os
import logging
from typing import Dict, Optional
from openai import OpenAI
from dispositions_module import dispositions_module

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
logger = logging.getLogger(__name__)

class AIListingGenerator:
    def __init__(self):
        """Initialize AI Listing Generator with OpenAI client"""
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    def generate_investor_listing(self, property_data: Dict, listing_type: str = 'off_market') -> Dict:
        """
        Generate complete investor listing using GPT-4o
        """
        if not self.client:
            return {
                'status': 'error',
                'error': 'OpenAI API key not configured',
                'listing': 'AI listing generation requires OpenAI API configuration'
            }
        
        try:
            # Get comprehensive listing data from dispositions module
            listing_data_result = dispositions_module.generate_investor_listing_data(property_data)
            
            if listing_data_result['status'] == 'error':
                return listing_data_result
            
            listing_data = listing_data_result['listing_data']
            
            # Create structured prompt for GPT-4o
            prompt = self._create_listing_prompt(listing_data, listing_type)
            
            # Generate listing with GPT-4o
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert real estate copywriter specializing in investor-focused property listings. Create compelling, accurate listings that sound professional but approachable. Focus on investment potential, financial metrics, and market opportunity."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1200
            )
            
            listing_content = response.choices[0].message.content
            
            return {
                'status': 'success',
                'listing': listing_content,
                'listing_type': listing_type,
                'property_data': listing_data,
                'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else 0
            }
            
        except Exception as e:
            logger.error(f"AI listing generation error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'listing': f'Unable to generate listing: {str(e)}'
            }
    
    def generate_mls_listing(self, property_data: Dict) -> Dict:
        """Generate MLS-optimized listing"""
        return self.generate_investor_listing(property_data, 'mls')
    
    def generate_off_market_listing(self, property_data: Dict) -> Dict:
        """Generate off-market investor listing"""
        return self.generate_investor_listing(property_data, 'off_market')
    
    def _create_listing_prompt(self, listing_data: Dict, listing_type: str) -> str:
        """Create structured prompt for GPT-4o listing generation"""
        
        prop_details = listing_data['property_details']
        financial = listing_data['financial_overview']
        comps = listing_data['comparable_sales']
        active_listings = listing_data['active_listings']
        location = listing_data['location_data']
        
        prompt = f"""
Create a compelling investor-focused property listing using the following data:

**PROPERTY DETAILS:**
Address: {prop_details['address']}
Bedrooms: {prop_details['bedrooms']}
Bathrooms: {prop_details['bathrooms']}
Square Feet: {prop_details['square_feet']:,}
Year Built: {prop_details['year_built']}
Property Type: {prop_details['property_type']}
Lot Size: {prop_details.get('lot_size', 'N/A')}

**FINANCIAL OVERVIEW:**
Buy Now Price: ${financial['buy_now_price']:,} (~70% of ARV)
Estimated Rehab: ${financial['estimated_rehab']:,}
ARV: ${financial['arv']:,}
Projected Net Profit: ${financial['projected_profit']:,}
Rent Estimate: ${financial['rent_estimate']:,}/month
Cap Rate: {financial['cap_rate']:.2%}

**LOCATION & NEIGHBORHOOD:**
City: {location['city']}, {location['state']}
Neighborhood: {location['neighborhood']}
Nearby Amenities:
{chr(10).join(f"- {amenity}" for amenity in location['nearby_amenities'])}

Growth Indicators:
{chr(10).join(f"- {indicator}" for indicator in location['growth_indicators'])}

**COMPARABLE SALES:**
{self._format_comps_for_prompt(comps)}

**ACTIVE LISTINGS:**
{self._format_active_listings_for_prompt(active_listings)}

**LISTING TYPE:** {listing_type.replace('_', ' ').title()}

**INSTRUCTIONS:**
Generate a professional, investor-focused listing following this structure:

1. **Opening Paragraph:** Create excitement around location, investment potential, and market opportunity. Mention specific financial metrics and growth potential.

2. **Property Highlights Section:**
   - Highlight key features and lot size
   - Mention neighborhood and location advantages
   - Include any unique selling points

3. **Schools & Amenities Section:**
   - Describe nearby schools, shopping, parks, commuter routes
   - Focus on rental appeal and tenant demand factors

4. **Financial Overview Section:**
   - Present buy price, rehab estimate, ARV clearly
   - Calculate and show projected profit
   - Include rent estimate and cap rate if applicable

5. **Property Specs & Condition Section:**
   - Square footage, year built, key systems
   - Current condition assessment
   - Renovation scope and potential

6. **Comparable Sales Section:**
   - Format the provided comps cleanly
   - Show recent sales with dates and prices
   - Highlight market validation

7. **Active Listings Section:**
   - Show current competition
   - Demonstrate market positioning

**TONE GUIDELINES:**
- Professional but approachable
- Focus on investment metrics and opportunity
- Use specific numbers and data points
- Avoid generic real estate fluff
- Write for experienced investors
- Include urgency and market positioning

Generate the complete listing now:
"""
        
        return prompt
    
    def _format_comps_for_prompt(self, comps: list) -> str:
        """Format comparable sales for prompt"""
        if not comps:
            return "No recent comparable sales data available"
        
        formatted = []
        for comp in comps:
            formatted.append(
                f"- {comp['address']}, {comp['beds_baths']}, "
                f"Sold for ${comp['sale_price']:,} on {comp['sale_date']}, "
                f"{comp['square_feet']:,} sqft (${comp['price_per_sqft']:.0f}/sqft)"
            )
        
        return "\n".join(formatted)
    
    def _format_active_listings_for_prompt(self, active_listings: list) -> str:
        """Format active listings for prompt"""
        if not active_listings:
            return "No current active listings in comparable range"
        
        formatted = []
        for listing in active_listings:
            formatted.append(
                f"- {listing['address']}, {listing['beds_baths']}, "
                f"Listed at ${listing['list_price']:,}, "
                f"on market {listing['days_on_market']} days"
            )
        
        return "\n".join(formatted)
    
    def generate_listing_variations(self, property_data: Dict) -> Dict:
        """Generate multiple listing variations for A/B testing"""
        try:
            variations = {}
            
            # Generate off-market version
            off_market = self.generate_off_market_listing(property_data)
            if off_market['status'] == 'success':
                variations['off_market'] = off_market['listing']
            
            # Generate MLS version
            mls = self.generate_mls_listing(property_data)
            if mls['status'] == 'success':
                variations['mls'] = mls['listing']
            
            return {
                'status': 'success',
                'variations': variations,
                'count': len(variations)
            }
            
        except Exception as e:
            logger.error(f"Listing variations error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'variations': {}
            }

# Create global instance
ai_listing_generator = AIListingGenerator()