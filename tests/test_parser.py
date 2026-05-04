import pytest
from src.processing.parser import DataParser 

@pytest.fixture
def parser_instance():
    # Load test station configuration (mocking the config.json data)
    estaciones = [{"id": "3195", "nombre": "Madrid-Retiro"}]
    # Corrected keyword argument to match the DataParser __init__ definition
    return DataParser(allowed_stations=estaciones)

def test_parser_datos_validos(parser_instance):
    """Prueba que el parser extrae correctamente los datos cuando el JSON es perfecto."""
    raw_data = [{
        "indicativo": "3195",
        "tmax": "22,5",  # Using tmax and comma decimals to verify parsing logic
        "hrMedia": "45", 
        "racha": "10,2", 
        "fecha": "2026-04-27T10:00:00"
    }]
    
    resultado = parser_instance.parse_and_clean(raw_data)
    
    assert len(resultado) == 1
    
    # Access attributes via object dot notation
    assert resultado[0].name == "Madrid-Retiro"
    
    # Verify strict typing enforcement (strings converted to floats)
    assert isinstance(resultado[0].temp_max, float)
    assert isinstance(resultado[0].humidity_avg, float)
    
    # Verify comma-to-dot decimal normalization
    assert resultado[0].temp_max == 22.5
    assert resultado[0].wind_gust == 10.2

def test_parser_datos_corruptos(parser_instance):
    """
    DEMO DE RESILIENCIA: Prueba qué ocurre cuando la API devuelve datos incompletos
    o tipos incorrectos (ej. una letra donde debería ir un número).
    """
    datos_corruptos = [
        {
            "indicativo": "3195", 
            "tmax": "ERROR",        # Invalid type: clean_float will return None, failing validation
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
    
    # The parser should ignore station 9999 and discard 3195 due to parsing failure
    resultado = parser_instance.parse_and_clean(datos_corruptos)
    
    # The final list must be empty because no records passed the normalization layer
    assert len(resultado) == 0