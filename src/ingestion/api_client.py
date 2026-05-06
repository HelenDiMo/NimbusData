import os
import logging
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
        code = response.status_code
        if code == 200:
            return True

        messages = {
            401: "No autorizado: API Key inválida.",
            403: "Prohibido: Acceso denegado al recurso.",
            404: "No encontrado: El endpoint o los datos no existen.",
            429: "Rate Limit: Demasiadas peticiones.",
            503: "Servicio no disponible: AEMET está en mantenimiento."
        }
        
        msg = messages.get(code, f"Error inesperado ({code})")
        log_error.error(f"[{context}] {msg}")
        return False
    
    def _execute_request(self, endpoint):
        """
        Gestiona el flujo completo de AEMET: 
        Petición de URL -> Validación de estados -> Descarga de JSON final.
        """
        url = f"{self.base_url}/{endpoint}"
        
        try:
            # PASO 1: Obtener el enlace temporal de datos
            start_t = time.time()
            response = self.session.get(url, timeout=10)
            latency = time.time() - start_t

            log_info.info(f"STEP1 {url} - {response.status_code} - {latency:.2f}s")

            if not self._check_status(response, f"STEP1: {endpoint}"):
                return None

            res_json = response.json()
            
            # Validación del estado interno de AEMET
            if res_json.get("estado") != 200:
                log_warning.warning(f"AEMET (Interno {res_json.get('estado')}): "
                                f"{res_json.get('descripcion')}")
                return None

            data_url = res_json.get("datos")
            if not data_url:
                log_error.error(f"No se encontró 'datos_url' en la respuesta de {endpoint}")
                return None

            # PASO 2: Descargar el contenido real
            response_data = self.session.get(data_url, timeout=15)
            
            if self._check_status(response_data, "STEP2: Descarga Final"):
                return response_data.json()
            
            return None

        except requests.exceptions.RequestException as e:
            log_error.error(f"Error de red: {e}")
            return None


    def get_today_weather(self, station_id):
        endpoint = f"observacion/convencional/datos/estacion/{station_id}"
        return self._execute_request(endpoint)

    def get_daily_weather(self, station_id, start_date, end_date):
        endpoint = f"valores/climatologicos/diarios/datos/fechaini/{start_date}/fechafin/{end_date}/estacion/{station_id}"
        return self._execute_request(endpoint)
        
    def get_stations(self): 
        endpoint = "valores/climatologicos/inventarioestaciones/todasestaciones"
        return self._execute_request(endpoint)
