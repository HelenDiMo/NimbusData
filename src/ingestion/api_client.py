import os
import logging
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Assuming you import your configured logger
# from src.utils.logger import _logger 
logger = logging.getLogger("nimbus_logger")

load_dotenv()

class AemetClient:
    def __init__(self, base_url: str = "https://opendata.aemet.es/opendata/api"):
        """Inicializa el cliente de la API con una sesión persistente."""
        self.base_url = base_url
        self.api_key = os.getenv("WEATHER_API_KEY")
        self.session = requests.Session()
        
        # Cabecera requerida por el checklist: Respeto al Servidor
        self.session.headers.update({
            "User-Agent": "NimbusClimateApp/1.0",
            "Content-Type": "application/json"
        })
        
        # Opcional pero recomendado: Lógica de reintentos (Retries)
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def fetch_data(self, endpoint: str, params: dict = None) -> list | dict | None:
        """
        Realiza la petición GET. Falla con gracia si hay errores HTTP sin detener el programa.
        """
        url = f"{self.base_url}{endpoint}"
        
        if params is None:
            params = {}
            
        # AEMET suele requerir la API key en los parámetros
        if self.api_key:
            params['api_key'] = self.api_key

        try:
            logger.info(f"Solicitando datos a: {url}")
            response = self.session.get(url, params=params, timeout=10)
            
            # Verifica los códigos de estado (200, 401, 403, 404, 429)
            response.raise_for_status() 
            
            return response.json()
            
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"Error HTTP {response.status_code}: {http_err}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Error de conexión. Verifica la conectividad de red.")
            return None
        except requests.exceptions.Timeout:
            logger.error("Timeout: El servidor de la API tardó demasiado en responder.")
            return None
        except Exception as e:
            logger.error(f"Error inesperado durante la petición a la API: {e}")
            return None