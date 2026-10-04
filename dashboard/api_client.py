import os
import requests
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")


class APIClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def _headers(self, token: Optional[str] = None) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def check_health(self) -> bool:
        try:
            res = requests.get(f"{self.base_url.rsplit('/api', 1)[0]}/", timeout=2)
            return res.status_code == 200
        except Exception:
            return False

    def login(self, email: str, password: str) -> Dict[str, Any]:
        url = f"{self.base_url}/auth/login"
        res = requests.post(url, json={"email": email, "password": password}, timeout=5)
        if res.status_code == 200:
            return {"success": True, "data": res.json()}
        error_detail = res.json().get("detail", "Login failed") if res.headers.get("content-type") == "application/json" else res.text
        return {"success": False, "error": error_detail}

    def register(self, data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/auth/register"
        res = requests.post(url, json=data, timeout=5)
        if res.status_code == 201:
            return {"success": True, "data": res.json()}
        error_detail = res.json().get("detail", "Registration failed") if res.headers.get("content-type") == "application/json" else res.text
        return {"success": False, "error": error_detail}

    def get_me(self, token: str) -> Dict[str, Any]:
        url = f"{self.base_url}/auth/me"
        res = requests.get(url, headers=self._headers(token), timeout=5)
        if res.status_code == 200:
            return {"success": True, "data": res.json()}
        return {"success": False, "error": "Session expired"}

    def get_doctors(self, specialty: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/doctors"
        params = {}
        if specialty and specialty != "All":
            params["specialty"] = specialty
        if search:
            params["search"] = search
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            return res.json()
        return []

    def get_departments(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/departments"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
        return []

    def book_appointment(self, token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/appointments"
        res = requests.post(url, json=payload, headers=self._headers(token), timeout=5)
        if res.status_code == 201:
            return {"success": True, "data": res.json()}
        error = res.json().get("detail", "Booking failed") if res.headers.get("content-type") == "application/json" else res.text
        return {"success": False, "error": error}

    def get_patient_appointments(self, token: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/patient/appointments"
        res = requests.get(url, headers=self._headers(token), timeout=5)
        if res.status_code == 200:
            return res.json()
        return []

    def get_physician_appointments(self, token: str, date_filter: Optional[str] = None, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/physician/appointments"
        params = {}
        if date_filter:
            params["appointment_date"] = date_filter
        if status_filter and status_filter != "All":
            params["status_filter"] = status_filter
        res = requests.get(url, params=params, headers=self._headers(token), timeout=5)
        if res.status_code == 200:
            return res.json()
        return []

    def update_appointment_status(self, token: str, appointment_id: str, new_status: str, notes: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/appointments/{appointment_id}/status"
        res = requests.patch(url, json={"status": new_status, "notes": notes}, headers=self._headers(token), timeout=5)
        if res.status_code == 200:
            return {"success": True, "data": res.json()}
        return {"success": False, "error": res.text}

    def cancel_appointment(self, token: str, appointment_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/appointments/{appointment_id}/cancel"
        res = requests.post(url, headers=self._headers(token), timeout=5)
        if res.status_code == 200:
            return {"success": True, "data": res.json()}
        return {"success": False, "error": res.text}

    def get_operations_overview(self, token: str) -> Dict[str, Any]:
        url = f"{self.base_url}/operations/overview"
        res = requests.get(url, headers=self._headers(token), timeout=5)
        if res.status_code == 200:
            return res.json()
        return {}

    def get_bed_occupancy(self, token: str) -> Dict[str, Any]:
        url = f"{self.base_url}/operations/bed-occupancy"
        res = requests.get(url, headers=self._headers(token), timeout=5)
        if res.status_code == 200:
            return res.json()
        return {}

    def get_staffing(self, token: str) -> Dict[str, Any]:
        url = f"{self.base_url}/operations/staffing"
        res = requests.get(url, headers=self._headers(token), timeout=5)
        if res.status_code == 200:
            return res.json()
        return {}

    def get_forecasts(self, token: str, horizon: int = 7) -> Dict[str, Any]:
        url = f"{self.base_url}/operations/forecasts?horizon={horizon}"
        res = requests.get(url, headers=self._headers(token), timeout=5)
        if res.status_code == 200:
            return res.json()
        return {}

    def run_simulation(self, token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/operations/simulate"
        res = requests.post(url, json=payload, headers=self._headers(token), timeout=5)
        if res.status_code == 200:
            return res.json()
        return {}


api_client = APIClient()
