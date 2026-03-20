# multilauncher/auth.py

import requests
import hashlib
from typing import Dict, Any, Optional


ZAAP_PROXY_URL = "http://127.0.0.1:3000/api/v5"


def _get_proxy_auth_header(cipher: str) -> Dict[str, str]:
    """
    Construit l’en-tête X-Api-Key demandé par haapi.
    → Ici on utilise un dummy API key (le cipher brut) car le proxy zaap s’occupe du déchiffrement.
    Si besoin, on peut le décrypter avec la vraie clé — mais pas nécessaire ici.
    """
    return {
        "X-Api-Key": cipher,
        "User-Agent": "Ankama Launcher/2024.1 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/json",
    }


def request_ticket_for_identity(identity: Dict[str, Any]) -> Optional[str]:
    """
    Demande un ticket à haapi via le proxy zaap.
    
    On simule une nouvelle machine en changeant :
      - machine_id (unique)
      - platform / cpu_model
    
    Le proxy zaap se charge de l’authentification complète.
    """
    try:
        # Étape 1 : Créer un token via CreateToken
        url = f"{ZAAP_PROXY_URL}/Account/CreateToken"
        
        payload = {
            "certificate_id": identity["machine_id"],  # Utilise machine_id comme ID temporaire
            "hash": hashlib.sha256(identity["platform"].encode()).hexdigest()[:32],
            "apiKey": identity["machine_id"],  # Dummy API key — le proxy l’utilisera pour authentifier
            "machineId": identity["machine_id"],
            "platform": identity["platform"],
        }

        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            raise RuntimeError(f"haapi error: {resp.status_code} — {resp.text[:200]}")

        data = resp.json()
        
        # Extrait le token (structure standard de haapi /Account/CreateToken)
        return data.get("data", {}).get("token") or data.get("token")

    except Exception as e:
        print(f"[auth] Erreur: {e}")
        raise RuntimeError(
            "Impossible d'obtenir un ticket via zaap proxy.\n"
            f"Vérifiez que le proxy zaap tourne (port 3000) et est authentifié."
        ) from e
