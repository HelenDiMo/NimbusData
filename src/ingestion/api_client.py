import os
import logging
import requests
from datetime import datetime, timezone  #For Organizing Timezones and date format
from dotenv import load_dotenv #Security Eniviroment
from requests.adapters import HTTPAdapter  #Retry Strategy and Backoff Exponential 
from urllib3.util.retry import Retry  #Retry Strategy and Backoff Exponential 

# Configuración del logger centralizado
logger = logging.getLogger("nimbus_logger")  

load_dotenv()  

class AemetClient:
    def __init__(self, base_url: str = "https://opendata.aemet.es/opendata/api"):
        """Inicializa el cliente de la API con una sesión persistente."""
        self.base_url = base_url
        self.api_key = os.getenv("WEATHER_API_KEY")
        
        # Validación de credenciales de seguridad
        if not self.api_key:
            logger.error("CRÍTICO: No se encontró WEATHER_API_KEY en el archivo .env")
            print("\n[!] ERROR: Falta la API Key de AEMET. Por favor, crea un archivo .env con WEATHER_API_KEY=tu_clave")
            
        self.session = requests.Session()
        
        # Cabecera requerida por el checklist: Respeto al Servidor
        self.session.headers.update({
            "User-Agent": "NimbusClimateApp/1.0",
            "Content-Type": "application/json"
        })
        
        # Retry Strategy and Backoff Exponential
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def fetch_data(self, endpoint: str, params: dict = None) -> list | dict | None:
        """
        Realiza la petición GET. Falla con gracia si hay errores HTTP sin detener el programa.
        """
        url = f"{self.base_url}{endpoint}"
        if params is None:
            params = {}
            
        if self.api_key:
            params['api_key'] = self.api_key

        try:
            logger.info(f"Solicitando datos a: {url}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status() 
            return response.json()
            
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"Error HTTP {response.status_code}: {http_err}")
            return None
        except ValueError: 
            logger.error("La API no devolvió un JSON válido. Posible respuesta vacía o error de API Key.")
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

    # Added Two Steps Architecture Model to get weather data and organize it in JSON 
    def get_today_weather(self, station_id: str) -> list | dict | None:
        """
        Obtiene los datos climatológicos del día actual para una estación.
        Maneja automáticamente el flujo de dos peticiones (Two-Step Hop) de AEMET.
        """
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00UTC")
        endpoint = f"/valores/climatologicos/diarios/datos/fechaini/{today_str}/fechafin/{today_str}/estacion/{station_id}"
        
        initial_response = self.fetch_data(endpoint)
        
        if not initial_response:
            return None
            
        if isinstance(initial_response, dict):
            if initial_response.get("estado") == 404:
                logger.warning(f"AEMET: No hay datos de hoy para la estación {station_id}.")
                return None
                
            datos_url = initial_response.get("datos")
            if datos_url:
                try:
                    logger.info("Descargando datos finales (Hoy) desde la URL temporal de AEMET.")
                    response = self.session.get(datos_url, timeout=10)
                    response.raise_for_status()
                    return response.json()
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error descargando los datos finales de AEMET: {e}")
                    return None
                    
        return initial_response

    def get_daily_weather(self, station_id: str, start_date: str, end_date: str) -> list | dict | None:
        """
        Obtiene datos históricos para un rango de fechas.
        Se asume que start_date y end_date ya vienen formateados como YYYY-MM-DDTHH:MM:SSUTC
        """
        endpoint = f"/valores/climatologicos/diarios/datos/fechaini/{start_date}/fechafin/{end_date}/estacion/{station_id}"
        
        initial_response = self.fetch_data(endpoint)
        
        if not initial_response:
            return None
            
        if isinstance(initial_response, dict):
            if initial_response.get("estado") == 404:
                logger.warning(f"AEMET: No hay datos para la estación {station_id} en esas fechas.")
                return None
                
            datos_url = initial_response.get("datos")
            if datos_url:
                try:
                    logger.info(f"Descargando histórico ({start_date} a {end_date}) desde la URL temporal.")
                    response = self.session.get(datos_url, timeout=10)
                    response.raise_for_status()
                    return response.json()
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error descargando el histórico de AEMET: {e}")
                    return None
                    
        return initial_response