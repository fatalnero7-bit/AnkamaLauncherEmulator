# multilauncher/decrypt_with_device.py — DÉCHIFFREMENT AVEC DEVICE.PY

import hashlib
import json
import os
from pathlib import Path
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad


class Device:
    """Copie conforme de ton device.py — pour être autonome"""
    
    __uuid: str | None = None

    @staticmethod
    def getUUID():
        if Device.__uuid:
            return Device.__uuid

        plt = Device.getPlatform()
        arch = Device.getArch()
        machine_id = Device.getMachineId(plt, arch)
        cpu_count = Device.getCpuLength()
        cpu_model = Device.getCpuModel()

        Device.__uuid = ",".join([plt, arch, machine_id, str(cpu_count), cpu_model])
        return Device.__uuid

    @staticmethod
    def getMachineId(plt: str, arch: str) -> str:
        try:
            cmd = Device.getGUIDCmdPerPlatform(plt, arch)
            output = subprocess.check_output(cmd, shell=True, text=True)
            machine_uuid = Device.parseMachineGuuid(plt, output)

            sha256_hash_machine_uuid = hashlib.sha256()
            sha256_hash_machine_uuid.update(machine_uuid.encode("utf-8"))
            return sha256_hash_machine_uuid.hexdigest()
        except Exception as e:
            raise Exception(f"Error while obtaining machine id: {e}")

    @staticmethod
    def getGUIDCmdPerPlatform(plt: str, arch: str):
        import subprocess
        cmd_per_platform = {
            "darwin": "ioreg -rd1 -c IOPlatformExpertDevice",
            "win32": (
                os.path.join(
                    "%windir%",
                    "sysnative"
                    if arch == "32bit" and "PROCESSOR_ARCHITEW6432" in os.environ
                    else "System32",
                )
                + "\\REG.exe QUERY HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography /v MachineGuid"
            ),
            "linux": "( cat /var/lib/dbus/machine-id /etc/machine-id 2> /dev/null || hostname ) | head -n 1 || :",
        }
        return cmd_per_platform.get(plt)

    @staticmethod
    def parseMachineGuuid(plt: str, std_out: str) -> str:
        import re
        match plt:
            case "darwin":
                return re.sub(
                    r'=|\s+|"', "", std_out.split("IOPlatformUUID")[1].split("\n")[0]
                ).lower()
            case "win32":
                return re.sub(r"\r+|\n+|\s+", "", std_out.split("REG_SZ")[1]).lower()
            case "linux" | _:
                return re.sub(r"\r+|\n+|\s+", "", std_out).lower()

    @staticmethod
    def getArch():
        arch_map = {"AMD64": "x64", "x86_64": "x64", "i386": "x86", "i686": "x86"}
        return arch_map[platform.machine()]

    @staticmethod
    def getPlatform():
        system_map = {"Windows": "win32", "Darwin": "darwin", "Linux": "linux"}
        plt = system_map[platform.system()]
        return plt

    @staticmethod
    def getCpuLength() -> int:
        import psutil
        return psutil.cpu_count(logical=True) or 0

    @staticmethod
    def getCpuModel() -> str:
        if psutil.WINDOWS:
            import wmi, pythoncom
            pythoncom.CoInitialize()
            _wmi = wmi.WMI()
            cpu_info = _wmi.Win32_Processor()[0]
            return cpu_info.Name
        else:
            with open("/proc/cpuinfo", "r") as file:
                for line in file:
                    if "model name" in line:
                        return line.split(":")[1].strip()
                raise ValueError("CPU model not found")

    @staticmethod
    def getOsVersion():
        import platform
        version_splitted = platform.version().split(".")
        major_version = version_splitted[0]
        medium_version = version_splitted[1]
        return float(f"{major_version}.{medium_version}")


def decrypt_keydata_with_device(file_path: str) -> dict:
    """
    Déchiffre un .keydata avec la logique exacte de CryptoHelper + Device.getUUID()
    """
    # Lire le fichier
    with open(file_path, "r", encoding="utf-8") as f:
        data = f.read().strip()

    uuid = Device.getUUID()  # ← C'EST LE UUID VRAI UTILISÉ PAR ANKAMA

    # Découpe iv | ciphertext (en hex)
    try:
        parts = data.split("|", 1)
        if len(parts) != 2:
            raise ValueError("Format invalide")

        iv_hex, ciphertext_hex = parts
        iv = bytes.fromhex(iv_hex)
        ciphertext = bytes.fromhex(ciphertext_hex)

        # Clé : MD5(UUID)
        key = hashlib.md5(uuid.encode("utf-8")).digest()

        # AES-CBC decryption
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_padded = cipher.decrypt(ciphertext)
        
        try:
            decrypted = unpad(decrypted_padded, AES.block_size)
        except Exception as e:
            raise RuntimeError(
                f"Déchiffrement échoué (UUID={uuid[:8]}...). "
                "La clé est probablement incorrecte — le .keydata a pu être généré sur une autre machine."
            ) from e

        return json.loads(decrypted.decode("utf-8"))

    except Exception as e:
        raise RuntimeError(f"Erreur critique : {e}") from e


if __name__ == "__main__":
    import platform
    import subprocess

    # Chemin par défaut (Windows)
    file_path = Path.home() / "AppData" / "Roaming" / "zaap" / "keydata" / ".keydata16867972"
    
    print("🔍 Détails du système :")
    print(f"   UUID calculé : {Device.getUUID()[:30]}...")
    print(f"   Fichier cible : {file_path}")
    
    try:
        data = decrypt_keydata_with_device(str(file_path))
        
        print("\n✅ Déchiffrement réussi ! Données extraites :")
        print("-" * 60)
        for k, v in sorted(data.items()):
            if isinstance(v, str) and len(v) > 50:
                print(f"{k} = {v[:48]}...")
            else:
                print(f"{k} = {v}")
        
    except FileNotFoundError:
        print("❌ Fichier non trouvé.")
        print("   Vérifie que le chemin est bon, ou passe-le en argument :")
        print(f"   python {__file__} \"C:\\path\\to\\.keydata\"")
    except Exception as e:
        print(f"❌ Erreur : {e}")
