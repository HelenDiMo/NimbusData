import pytest
from unittest.mock import patch, MagicMock

# 1. CORRECTED IMPORT: Matching your actual folder, file, and class names
from src.ingestion.api_client import AemetClient

@pytest.fixture
def api_client():
    # 2. Instanciamos tu clase real en lugar de WeatherAPIClient
    # Asegúrate de pasar la base_url si tu __init__ la requiere
    return AemetClient() 

@patch("src.ingestion.api_client.requests.Session.get")
def test_fetch_data_exito(mock_get, api_client):
    """Prueba que el cliente devuelve el JSON cuando el código HTTP es 200."""
    
    # Preparamos el mock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"indicativo": "3195", "tmax": 22.5}]
    mock_get.return_value = mock_response

    # Asumiendo que tu método se llama fetch_data
    resultado = api_client.fetch_data("/endpoint_falso")

    assert mock_get.called
    assert resultado is not None
    assert resultado[0]["indicativo"] == "3195"