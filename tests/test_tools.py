"""
Unit tests for tool functions
"""

import pytest
from unittest.mock import patch, Mock
from app.tools.weather import WeatherTools
from app.tools.fx import FxTools
from app.tools.search import SearchTools
from app.tools.card import CardTools


class TestWeatherTool:
    """Test cases for weather tool"""
    
    @patch('app.tools.weather.requests.get')
    def test_get_weather_success(self, mock_get):
        """Test successful weather data retrieval"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'latitude': 48.8566,
            'longitude': 2.3522,
            'timezone': 'GMT',
            'daily': {
                'time': ['2025-09-03', '2025-09-04'],
                'temperature_2m_max': [25.0, 26.0],
                'temperature_2m_min': [15.0, 16.0],
                'weathercode': [1, 2]
            }
        }
        mock_get.return_value = mock_response
        
        weather_tool = WeatherTools()
        result = weather_tool.get_weather(48.8566, 2.3522)
        
        assert result['latitude'] == 48.8566
        assert result['longitude'] == 2.3522
        assert result['timezone'] == 'GMT'
        assert 'daily' in result
        mock_get.assert_called_once()
    
    @patch('app.tools.weather.requests.get')
    def test_get_weather_api_error(self, mock_get):
        """Test weather tool handles API errors"""
        mock_get.side_effect = Exception("API Error")
        
        weather_tool = WeatherTools()
        with pytest.raises(Exception):
            weather_tool.get_weather(48.8566, 2.3522)


class TestFxTool:
    """Test cases for FX tool"""
    
    @patch('app.tools.fx.requests.get')
    def test_convert_fx_success(self, mock_get):
        """Test successful currency conversion"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'amount': 100.0,
            'base': 'USD',
            'date': '2025-09-03',
            'rates': {'EUR': 85.81}
        }
        mock_get.return_value = mock_response
        
        fx_tool = FxTools()
        result = fx_tool.convert_fx(100, "USD", "EUR")
        
        assert result['amount'] == 100.0
        assert result['base'] == 'USD'
        assert result['rates']['EUR'] == 85.81
        mock_get.assert_called_once()
    
    @patch('app.tools.fx.requests.get')
    def test_convert_fx_api_error(self, mock_get):
        """Test FX tool handles API errors"""
        mock_get.side_effect = Exception("API Error")
        
        fx_tool = FxTools()
        with pytest.raises(Exception):
            fx_tool.convert_fx(100, "USD", "EUR")


class TestSearchTool:
    """Test cases for search tool"""
    
    def test_web_search_success_mock_results(self):
        """Test web search falls back to mock results when no API available"""
        # Without any environment variables, it should fall back to mock results
        search_tool = SearchTools()
        result = search_tool._mock_search_results("best restaurants Paris", 5)
        
        # Mock results should return restaurant data for restaurant queries
        assert len(result) >= 1
        assert 'title' in result[0]
        assert 'url' in result[0]
        assert 'snippet' in result[0]
    
    @patch.dict('os.environ', {}, clear=True)
    def test_web_search_missing_config(self):
        """Test web search with missing configuration falls back to mock results"""
        search_tool = SearchTools()
        result = search_tool.web_search("test query", 5)
        
        # Without config, should fall back to mock results
        assert len(result) >= 1
        assert 'title' in result[0]
        assert 'snippet' in result[0]
    
    @patch.dict('os.environ', {
        'PROJECT_ENDPOINT': 'https://test.endpoint.com',
        'AGENT_ID': 'test-agent-id',
        'BING_CONNECTION_ID': 'test-connection-id'
    })
    def test_web_search_api_error(self):
        """Test search tool handles API errors gracefully - falls back to mock results"""
        search_tool = SearchTools()
        result = search_tool.web_search("test query", 5)
        
        # Without BING_KEY, it should fall back to mock results or return error
        assert len(result) >= 1


class TestCardTool:
    """Test cases for card tool"""
    
    def test_recommend_card_success(self):
        """Test successful card recommendation"""
        card_tool = CardTools()
        result = card_tool.recommend_card("5812", 100, "France")
        
        assert 'best' in result
        assert 'explanation' in result
        assert 'card' in result['best']
        assert 'benefit' in result['best']
        assert 'fx_fee' in result['best']
    
    def test_recommend_card_different_countries(self):
        """Test card recommendation for different countries"""
        card_tool = CardTools()
        result_france = card_tool.recommend_card("5812", 100, "France")
        result_japan = card_tool.recommend_card("5812", 100, "Japan")
        
        # Both should return valid results
        assert 'best' in result_france
        assert 'best' in result_japan
        assert 'card' in result_france['best']
        assert 'card' in result_japan['best']
    
    def test_recommend_card_different_mccs(self):
        """Test card recommendation for different merchant categories"""
        card_tool = CardTools()
        result_dining = card_tool.recommend_card("5812", 100, "France")  # Dining
        result_gas = card_tool.recommend_card("5541", 100, "France")      # Gas
        
        # Both should return valid results
        assert 'best' in result_dining
        assert 'best' in result_gas
        assert 'card' in result_dining['best']
        assert 'card' in result_gas['best']
