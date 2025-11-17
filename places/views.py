from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .services.google_places import GooglePlacesService
import logging

logger = logging.getLogger(__name__)


def index(request):
    """
    Main page view - renders the roulette interface.
    
    Passes Google Maps API key to the template for map initialization.
    """
    context = {
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    }
    return render(request, 'places/index.html', context)


@require_http_methods(["GET"])
def random_place(request):
    """
    API endpoint to get a random restaurant.
    
    Query params:
        lat (float): Latitude coordinate
        lng (float): Longitude coordinate
        radius (int): Search radius in meters (default: 1000)
    
    Returns:
        JSON response with restaurant details or error message
        
    Example success response:
        {
            "name": "Random Resto",
            "photo_url": "https://...",
            "address": "123 Some St, Quezon City",
            "phone": "+63 2 123 4567",
            "lat": 14.6123,
            "lng": 121.0312,
            "maps_url": "https://www.google.com/maps/...",
            "place_id": "ChIJ..."
        }
    
    Example error response:
        {"error": "No restaurants found in this area."}
    """
    # Validate required parameters
    try:
        lat = float(request.GET.get('lat'))
        lng = float(request.GET.get('lng'))
    except (TypeError, ValueError):
        return JsonResponse(
            {'error': 'Invalid or missing coordinates. Please provide lat and lng.'}, 
            status=400
        )
    
    # Validate coordinate ranges
    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        return JsonResponse(
            {'error': 'Coordinates out of range. Lat must be -90 to 90, lng must be -180 to 180.'}, 
            status=400
        )
    
    # Parse radius (default 1000m = 1km)
    try:
        radius = int(request.GET.get('radius', 1000))
        if radius <= 0 or radius > 50000:  # Max 50km
            raise ValueError()
    except (TypeError, ValueError):
        return JsonResponse(
            {'error': 'Invalid radius. Must be between 1 and 50000 meters.'}, 
            status=400
        )
    
    # Call Google Places service
    try:
        service = GooglePlacesService()
        restaurant = service.get_random_restaurant(lat, lng, radius)
        
        if not restaurant:
            return JsonResponse(
                {'error': 'No restaurants found in this area. Try increasing the radius or changing your location.'}, 
                status=404
            )
        
        return JsonResponse(restaurant)
    
    except Exception as e:
        logger.error(f"Error fetching random restaurant: {str(e)}", exc_info=True)
        return JsonResponse(
            {'error': f'An error occurred while searching for restaurants: {str(e)}'}, 
            status=500
        )
