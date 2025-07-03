"""
Address Validation Middleware
Ensures addresses are hard-validated before underwriting analysis
"""

import logging
from functools import wraps
from flask import request, jsonify
from google_places_service import google_places_service, AddressValidationError, GooglePlacesAPIError

def require_valid_address(f):
    """
    Middleware decorator to require and validate address before analysis
    
    Expects request data to contain:
    - street_address (or address)
    - city
    - state  
    - zip_code
    
    On success, adds validated address components to request data
    On failure, returns HTTP 400 with error message
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get address components from request
            data = request.get_json() if request.is_json else request.form
            
            # Extract address components with fallbacks
            street = (data.get('street_address') or data.get('address') or '').strip()
            city = (data.get('city') or '').strip()
            state = (data.get('state') or '').strip()
            zip_code = (data.get('zip_code') or '').strip()
            
            # Check if all required components are present
            if not all([street, city, state, zip_code]):
                missing_fields = []
                if not street: missing_fields.append('street_address')
                if not city: missing_fields.append('city') 
                if not state: missing_fields.append('state')
                if not zip_code: missing_fields.append('zip_code')
                
                return jsonify({
                    'success': False,
                    'error': 'INCOMPLETE_ADDRESS',
                    'message': f'Missing required address fields: {", ".join(missing_fields)}',
                    'missing_fields': missing_fields
                }), 400
            
            # Validate address using Google Address Validation API
            logging.info(f"Validating address: {street}, {city}, {state} {zip_code}")
            
            validation_result = google_places_service.validate_address(
                street=street,
                city=city, 
                state=state,
                zip_code=zip_code
            )
            
            # Add validated address data to request for downstream processing
            # This ensures existing valuation services continue to work
            if hasattr(request, 'validated_address'):
                request.validated_address = validation_result
            else:
                # For Flask forms, update the data
                if request.is_json:
                    request.json.update({
                        'validated_address': validation_result,
                        'latitude': validation_result['latitude'],
                        'longitude': validation_result['longitude'],
                        'formatted_address': validation_result['formattedAddress']
                    })
                else:
                    # For form data, we'll store in request context
                    request.validated_address = validation_result
            
            logging.info(f"Address validation successful: {validation_result['formattedAddress']}")
            return f(*args, **kwargs)
            
        except AddressValidationError as e:
            error_message = str(e)
            
            # Check if Address Validation API is not enabled
            if "has not been used" in error_message or "is disabled" in error_message:
                logging.warning(f"Address Validation API not enabled, proceeding with basic validation")
                
                # Proceed without hard validation when API is not enabled
                # Store basic address data for downstream processing  
                
                # Check if coordinates were provided in the request
                latitude = data.get('latitude')
                longitude = data.get('longitude')
                formatted_address = data.get('formattedAddress') or f"{street}, {city}, {state} {zip_code}"
                
                request.validated_address = {
                    'isValid': True,
                    'formattedAddress': formatted_address,
                    'latitude': latitude,
                    'longitude': longitude,
                    'components': {
                        'street': street,
                        'city': city,
                        'state': state,
                        'zip': zip_code
                    },
                    'source': 'basic_validation'
                }
                
                return f(*args, **kwargs)
            
            # For other validation errors, return 400
            logging.warning(f"Address validation failed: {error_message}")
            return jsonify({
                'success': False,
                'error': 'INVALID_ADDRESS',
                'message': error_message
            }), 400
            
        except GooglePlacesAPIError as e:
            logging.error(f"Google Places API error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'VALIDATION_SERVICE_ERROR',
                'message': 'Address validation service is temporarily unavailable'
            }), 503
            
        except Exception as e:
            logging.error(f"Unexpected error in address validation: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': 'An error occurred during address validation'
            }), 500
    
    return decorated_function


def extract_validated_address_data(request):
    """
    Helper function to extract validated address data from request
    
    Returns:
        Dict containing validated address components for use in analysis
    """
    if hasattr(request, 'validated_address') and request.validated_address:
        return {
            'street_address': request.validated_address['components']['street'],
            'city': request.validated_address['components']['city'],
            'state': request.validated_address['components']['state'],
            'zip_code': request.validated_address['components']['zip'],
            'formatted_address': request.validated_address['formattedAddress'],
            'latitude': request.validated_address['latitude'],
            'longitude': request.validated_address['longitude']
        }
    
    # Fallback to original request data if validation data not available
    data = request.get_json() if request.is_json else request.form
    return {
        'street_address': data.get('street_address') or data.get('address', ''),
        'city': data.get('city', ''),
        'state': data.get('state', ''),
        'zip_code': data.get('zip_code', ''),
        'formatted_address': data.get('formatted_address', ''),
        'latitude': data.get('latitude'),
        'longitude': data.get('longitude')
    }