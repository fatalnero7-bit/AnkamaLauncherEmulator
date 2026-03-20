# multilauncher/identity.py

import hashlib
import json
from pathlib import Path
from typing import Dict, Any


APP_DATA = Path.home() / "AppData" / "Roaming" / "zaap"
KEYDATA_DIR = APP_DATA / "keydata"


def get_stored_keydata():
    """Lit les fichiers .keydata dans le dossier zaap."""
    if not KEYDATA_DIR.exists():
        return []

    entries = []
    for f in sorted(KEYDATA_DIR.glob("*.keydata")):
        try:
            content = f.read_text().strip()
            parts = content.split("|", 1)
            if len(parts) == 2:
                uuid, cipher = parts
                entries.append({"uuid": uuid, "cipher": cipher})
        except Exception as e:
            print(f"[identity] Erreur lecture {f.name}: {e}")
    return entries


def generate_persistent_identity(cipher: str) -> Dict[str, Any]:
    """
    Crée une identité unique & persistante à partir du cipher (non déchiffré).
    L’identité est basée sur une empreinte SHA256 → donc stable d’un lancement à l’autre.
    """
    h = hashlib.sha256(cipher.encode()).digest()
    machine_id = ":".join(f"{b:02x}" for b in h[:16])  # 16 bytes = 32 chars hex

    return {
        "machine_id": machine_id,
        "platform": "win64",
        "arch": "x86_64",
        "cpu_count": 4,
        "cpu_model": "Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz",  # valeur neutre
    }


def save_identity(login: str, identity: dict) -> None:
    """Sauvegarde l’identité dans un fichier local (optionnel — peut être supprimé si tu veux purement dynamique)."""
    identity_dir = Path.home() / ".multilauncher" / "identities"
    identity_dir.mkdir(parents=True, exist_ok=True)
    
    login_hash = hashlib.sha256(login.encode()).hexdigest()[:12]
    path = identity_dir / f"{login_hash}.json"
    path.write_text(json.dumps(identity, indent=2))
