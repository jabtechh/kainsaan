"""
Restaurant search service using OpenStreetMap Overpass API (FREE, no API key needed!)

Falls back to Google Places API if GOOGLE_PLACES_API_KEY is set.
"""

import random
import requests
from typing import Optional, Dict, List
from django.conf import settings


class GooglePlacesService:
    """Service for finding restaurants using OpenStreetMap or Google Places API."""
    
    # OpenStreetMap Overpass API (FREE!)
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    
    # Google Places API (requires billing)
    BASE_URL = "https://maps.googleapis.com/maps/api"
    NEARBY_SEARCH_ENDPOINT = f"{BASE_URL}/place/nearbysearch/json"
    PLACE_DETAILS_ENDPOINT = f"{BASE_URL}/place/details/json"
    PLACE_PHOTO_ENDPOINT = f"{BASE_URL}/place/photo"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the service with an API key (optional for OpenStreetMap).
        
        Args:
            api_key: Google Places API key. If not provided, uses OpenStreetMap.
        """
        self.api_key = api_key or settings.GOOGLE_PLACES_API_KEY
        self.use_google = bool(self.api_key and self.api_key not in ['dev', 'test', 'test-key', ''])
    
    def search_nearby_restaurants_osm(
        self, 
        latitude: float, 
        longitude: float, 
        radius: int = 1000
    ) -> List[Dict]:
        """
        Search for nearby restaurants using OpenStreetMap Overpass API (FREE!).
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius: Search radius in meters
            
        Returns:
            List of restaurant objects
        """
        # Overpass QL query to find restaurants
        query = f"""
        [out:json];
        (
          node["amenity"="restaurant"](around:{radius},{latitude},{longitude});
          way["amenity"="restaurant"](around:{radius},{latitude},{longitude});
          relation["amenity"="restaurant"](around:{radius},{latitude},{longitude});
        );
        out body;
        >;
        out skel qt;
        """
        
        try:
            response = requests.post(
                self.OVERPASS_URL,
                data={'data': query},
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            
            restaurants = []
            for element in data.get('elements', []):
                if element.get('type') == 'node' and element.get('tags', {}).get('amenity') == 'restaurant':
                    tags = element.get('tags', {})
                    restaurants.append({
                        'id': element.get('id'),
                        'name': tags.get('name', 'Unknown Restaurant'),
                        'lat': element.get('lat'),
                        'lng': element.get('lon'),
                        'address': self._format_osm_address(tags),
                        'phone': tags.get('phone', tags.get('contact:phone', 'N/A')),
                        'cuisine': tags.get('cuisine', 'Restaurant'),
                    })
            
            return restaurants
        except Exception as e:
            print(f"OSM API error: {e}")
            return []
    
    def _format_osm_address(self, tags: Dict) -> str:
        """Format address from OSM tags."""
        parts = []
        if tags.get('addr:housenumber'):
            parts.append(tags['addr:housenumber'])
        if tags.get('addr:street'):
            parts.append(tags['addr:street'])
        if tags.get('addr:city'):
            parts.append(tags['addr:city'])
        if tags.get('addr:province'):
            parts.append(tags['addr:province'])
        
        return ', '.join(parts) if parts else 'Address not available'
    
    def search_nearby_restaurants(
        self, 
        latitude: float, 
        longitude: float, 
        radius: int = 1000
    ) -> List[Dict]:
        """
        Search for nearby restaurants using Google Places Nearby Search API.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius: Search radius in meters (default 1000m = 1km)
            
        Returns:
            List of restaurant place objects from Google Places API
            
        Raises:
            requests.RequestException: If API call fails
        """
        params = {
            'location': f"{latitude},{longitude}",
            'radius': radius,
            'type': 'restaurant',
            'key': self.api_key
        }
        
        response = requests.get(self.NEARBY_SEARCH_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') != 'OK':
            # Return empty list for ZERO_RESULTS or other non-error statuses
            if data.get('status') == 'ZERO_RESULTS':
                return []
            # Raise exception for actual errors
            raise Exception(f"Google Places API error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
        
        return data.get('results', [])
    
    def get_place_details(self, place_id: str) -> Dict:
        """
        Get detailed information about a specific place.
        
        Args:
            place_id: Google Place ID
            
        Returns:
            Place details dictionary
            
        Raises:
            requests.RequestException: If API call fails
        """
        params = {
            'place_id': place_id,
            'fields': 'name,formatted_address,formatted_phone_number,international_phone_number,geometry,photos',
            'key': self.api_key
        }
        
        response = requests.get(self.PLACE_DETAILS_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') != 'OK':
            raise Exception(f"Google Places API error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
        
        return data.get('result', {})
    
    def get_photo_url(
        self, 
        photo_reference: str, 
        max_width: int = 400
    ) -> str:
        """
        Generate a photo URL from a photo reference.
        
        Args:
            photo_reference: Photo reference from Places API
            max_width: Maximum width of the photo in pixels
            
        Returns:
            URL to the photo
        """
        return f"{self.PLACE_PHOTO_ENDPOINT}?maxwidth={max_width}&photo_reference={photo_reference}&key={self.api_key}"
    
    def get_maps_url(self, place_id: str, lat: float, lng: float) -> str:
        """
        Generate a Google Maps URL for a place.
        
        Args:
            place_id: Google Place ID
            lat: Latitude
            lng: Longitude
            
        Returns:
            Google Maps search URL
        """
        return f"https://www.google.com/maps/search/?api=1&query={lat},{lng}&query_place_id={place_id}"
    
    def get_random_restaurant(
        self, 
        latitude: float, 
        longitude: float, 
        radius: int = 1000,
        fallback_photo_url: str = "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400"
    ) -> Optional[Dict]:
        """
        Get a random restaurant from nearby results.
        Uses OpenStreetMap (free) by default, falls back to Google Places if API key is set.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius: Search radius in meters
            fallback_photo_url: URL to use for photo
            
        Returns:
            Dictionary with restaurant info or None if no restaurants found
        """
        # Use OpenStreetMap (FREE!)
        if not self.use_google:
            return self._get_random_restaurant_osm(latitude, longitude, radius, fallback_photo_url)
        
        # Use Google Places API (requires billing)
        return self._get_random_restaurant_google(latitude, longitude, radius, fallback_photo_url)
    
    def _get_random_restaurant_osm(
        self,
        latitude: float,
        longitude: float,
        radius: int,
        fallback_photo_url: str
    ) -> Optional[Dict]:
        """Get random restaurant using OpenStreetMap."""
        restaurants = self.search_nearby_restaurants_osm(latitude, longitude, radius)
        
        if not restaurants:
            return None
        
        chosen = random.choice(restaurants)
        
        # Generate Google Maps URL with restaurant name for better pin display
        restaurant_name = chosen['name'].replace(' ', '+')
        maps_url = f"https://www.google.com/maps/search/?api=1&query={restaurant_name}+near+{chosen['lat']},{chosen['lng']}"
        
        # Use food-related Unsplash photos as fallback
        food_photos = [
            "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400",
            "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=400",
            "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400",
            "https://images.unsplash.com/photo-1476224203421-9ac39bcb3327?w=400",
        ]
        
        return {
            'name': chosen['name'],
            'photo_url': random.choice(food_photos),
            'address': chosen['address'],
            'phone': chosen['phone'],
            'lat': chosen['lat'],
            'lng': chosen['lng'],
            'maps_url': maps_url,
            'place_id': str(chosen['id'])
        }
    
    def _get_random_restaurant_google(
        self,
        latitude: float,
        longitude: float,
        radius: int,
        fallback_photo_url: str
    ) -> Optional[Dict]:
        """Get random restaurant using Google Places API."""
        restaurants = self.search_nearby_restaurants(latitude, longitude, radius)
        
        if not restaurants:
            return None
        
        chosen = random.choice(restaurants)
        place_id = chosen.get('place_id')
        
        details = self.get_place_details(place_id)
        
        name = details.get('name', 'Unknown Restaurant')
        address = details.get('formatted_address', 'Address not available')
        phone = details.get('international_phone_number') or details.get('formatted_phone_number') or 'N/A'
        
        geometry = details.get('geometry', {})
        location = geometry.get('location', {})
        lat = location.get('lat', latitude)
        lng = location.get('lng', longitude)
        
        photos = details.get('photos', [])
        if photos:
            photo_reference = photos[0].get('photo_reference')
            photo_url = self.get_photo_url(photo_reference)
        else:
            photo_url = fallback_photo_url
        
        maps_url = self.get_maps_url(place_id, lat, lng)
        
        return {
            'name': name,
            'photo_url': photo_url,
            'address': address,
            'phone': phone,
            'lat': lat,
            'lng': lng,
            'maps_url': maps_url,
            'place_id': place_id
        }
