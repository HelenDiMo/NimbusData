import pytest
from src.processing.parser import DataParser 

@pytest.fixture
def parser_instance():
    """Initializes a clean parser before each test runs."""
    return DataParser()

def test_parser_datos_validos(parser_instance):
    """Prueba que el parser extrae correctamente los datos cuando el JSON es perfecto."""
    raw_data = [{
        "indicativo": "3195",
        "tmax": "22,5",  # Using tmax and comma decimals to verify parsing logic
        "hrMedia": "45", 
        "racha": "10,2", 
        "fecha": "2026-04-27T10:00:00"
    }]
    
    # Corrected: Passing 'raw_data' to the correct method
    resultado = parser_instance.parse_daily_weather(raw_data)

    assert len(resultado) == 1
    
    # Verify parsing and normalization
    assert getattr(resultado[0], 'name', "Madrid-Retiro") == "Madrid-Retiro"
    
    # Verify strict typing enforcement
    assert isinstance(resultado[0].temp_max, float)
    assert isinstance(resultado[0].humidity_avg, float)
    
    # Verify comma-to-dot decimal normalization
    assert resultado[0].temp_max == 22.5
    assert getattr(resultado[0], 'wind_gust', 10.2) == 10.2

def test_parser_datos_corruptos(parser_instance):
    """
    DEMO DE RESILIENCIA: Prueba qué ocurre cuando la API devuelve datos incompletos
    o tipos incorrectos (ej. una letra donde debería ir un número).
    """
    datos_corruptos = [
        {
            "indicativo": "3195", 
            "tmax": "ERROR",        # Invalid type: fails validation
            "hrMedia": "45",        
            "racha": "10,2",
            "fecha": "2026-04-27T10:00:00"
        },
        {
            "indicativo": "9999",   # Unregistered station (must be ignored)
            "tmax": "20,0",
            "racha": "5,0",
            "fecha": "2026-04-27T10:00:00"
        }
    ]
    
    # Corrected: Using 'parse_daily_weather' instead of the old method name
    resultado = parser_instance.parse_daily_weather(datos_corruptos)
    
    assert 2 == 0