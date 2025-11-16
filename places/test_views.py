"""
Sample tests for Kain Saan project.
Run with: pytest
"""

import pytest
from django.test import Client
from django.urls import reverse
from unittest.mock import Mock, patch


@pytest.mark.django_db
class TestIndexView:
    """Tests for the main index view."""
    
    def test_index_page_loads(self):
        """Test that the index page loads successfully."""
        client = Client()
        response = client.get(reverse('places:index'))
        
        assert response.status_code == 200
        assert b'Kain Saan' in response.content
        assert b'KAHIT SAAN!' in response.content
    
    def test_index_includes_maps_api_key(self):
        """Test that Google Maps API key is passed to template."""
        client = Client()
        response = client.get(reverse('places:index'))
        
        assert response.status_code == 200
        # Check that Maps API script tag is present
        assert b'maps.googleapis.com/maps/api/js' in response.content


@pytest.mark.django_db
class TestRandomPlaceAPI:
    """Tests for the random place API endpoint."""
    
    def test_missing_coordinates_returns_400(self):
        """Test that missing coordinates return 400 error."""
        client = Client()
        response = client.get(reverse('places:random_place'))
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
    
    def test_invalid_coordinates_returns_400(self):
        """Test that invalid coordinates return 400 error."""
        client = Client()
        
        # Test invalid latitude
        response = client.get(reverse('places:random_place'), {
            'lat': '999',
            'lng': '121.0'
        })
        assert response.status_code == 400
        
        # Test invalid longitude
        response = client.get(reverse('places:random_place'), {
            'lat': '14.6',
            'lng': '999'
        })
        assert response.status_code == 400
    
    def test_invalid_radius_returns_400(self):
        """Test that invalid radius returns 400 error."""
        client = Client()
        response = client.get(reverse('places:random_place'), {
            'lat': '14.6',
            'lng': '121.0',
            'radius': '-100'
        })
        
        assert response.status_code == 400
    
    @patch('places.views.GooglePlacesService')
    def test_no_restaurants_returns_404(self, mock_service):
        """Test that no restaurants found returns 404."""
        # Mock service to return None
        mock_instance = Mock()
        mock_instance.get_random_restaurant.return_value = None
        mock_service.return_value = mock_instance
        
        client = Client()
        response = client.get(reverse('places:random_place'), {
            'lat': '14.6',
            'lng': '121.0',
            'radius': '1000'
        })
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'No restaurants found' in data['error']
    
    @patch('places.views.GooglePlacesService')
    def test_successful_response(self, mock_service):
        """Test successful random restaurant response."""
        # Mock service to return a restaurant
        mock_restaurant = {
            'name': 'Test Restaurant',
            'photo_url': 'https://example.com/photo.jpg',
            'address': '123 Test St',
            'phone': '+63 2 1234567',
            'lat': 14.6,
            'lng': 121.0,
            'maps_url': 'https://maps.google.com/...',
            'place_id': 'ChIJ123'
        }
        mock_instance = Mock()
        mock_instance.get_random_restaurant.return_value = mock_restaurant
        mock_service.return_value = mock_instance
        
        client = Client()
        response = client.get(reverse('places:random_place'), {
            'lat': '14.6',
            'lng': '121.0',
            'radius': '1000'
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'Test Restaurant'
        assert data['address'] == '123 Test St'
        assert 'lat' in data
        assert 'lng' in data


@pytest.mark.django_db
class TestGooglePlacesService:
    """Tests for Google Places service (unit tests with mocked API calls)."""
    
    @patch('places.services.google_places.requests.get')
    def test_search_nearby_restaurants(self, mock_get):
        """Test nearby restaurant search."""
        from places.services.google_places import GooglePlacesService
        
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'status': 'OK',
            'results': [
                {'place_id': 'ChIJ123', 'name': 'Test Restaurant'}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        service = GooglePlacesService(api_key='test-key')
        results = service.search_nearby_restaurants(14.6, 121.0, 1000)
        
        assert len(results) == 1
        assert results[0]['name'] == 'Test Restaurant'
    
    @patch('places.services.google_places.requests.get')
    def test_zero_results(self, mock_get):
        """Test handling of zero results."""
        from places.services.google_places import GooglePlacesService
        
        # Mock API response with ZERO_RESULTS
        mock_response = Mock()
        mock_response.json.return_value = {
            'status': 'ZERO_RESULTS',
            'results': []
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        service = GooglePlacesService(api_key='test-key')
        results = service.search_nearby_restaurants(14.6, 121.0, 1000)
        
        assert results == []
    
    def test_get_photo_url(self):
        """Test photo URL generation."""
        from places.services.google_places import GooglePlacesService
        
        service = GooglePlacesService(api_key='test-key')
        url = service.get_photo_url('test-photo-ref', max_width=400)
        
        assert 'test-photo-ref' in url
        assert 'maxwidth=400' in url
        assert 'test-key' in url
    
    def test_get_maps_url(self):
        """Test Google Maps URL generation."""
        from places.services.google_places import GooglePlacesService
        
        service = GooglePlacesService(api_key='test-key')
        url = service.get_maps_url('ChIJ123', 14.6, 121.0)
        
        assert 'maps.google.com' in url
        assert '14.6' in url
        assert '121.0' in url
        assert 'ChIJ123' in url
