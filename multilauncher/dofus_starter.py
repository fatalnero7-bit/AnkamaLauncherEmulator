# multilauncher/dofus_starter.py

import subprocess
from pathlib import Path
from typing import Dict, Any


def get_dofus_exe_path() -> Path:
    """Trouve Dofus.exe dans les emplacements standards."""
    candidates = [
        Path(r"C:\Program Files (x86)\Ankama\Dofus 2\dofus.exe"),
        Path(r"C:\Program Files\Ankama\Dofus 2\dofus.exe"),
        Path.home() / "AppData" / "Roaming" / "zaap" / "resources" / "app" / "Dofus.exe",
    ]

    for path in candidates:
        if path.exists():
            return path

    raise FileNotFoundError(
        "Impossible de trouver `Dofus.exe`.\n"
        f"Tenté dans : {[str(p) for p in candidates]}"
    )


def launch_dofus(ticket: str, identity: Dict[str, Any]) -> int:
    """
    Lance Dofus avec le ticket et les paramètres matériels personnalisés.
    
    → Le fingerprint est injecté via **variables d’environnement** (méthode la plus discrète).
    Dofus les lit automatiquement au démarrage.
    """
    exe = get_dofus_exe_path()

    env = {
        "DOFUS_MACHINE_ID": identity["machine_id"],
        "DOFUS_PLATFORM": identity["platform"],
    }

    proc = subprocess.Popen(
        [str(exe)],
        env={**subprocess.os.environ, **env},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return proc.pid
