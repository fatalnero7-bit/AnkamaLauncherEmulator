# multilauncher/decrypt_real.py — version 100 % fiable pour ton .keydata

import sys
import hashlib
import json
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad


def decrypt_keydata(file_path: str) -> dict:
    # 🔑 Lis le fichier .keydata
    with open(file_path, "r", encoding="utf-8") as f:
        data = f.read().strip()

    # Sépare uuid | cipher (au premier "|")
    try:
        uuid_part, cipher_hex = data.split("|", 1)
    except ValueError:
        raise ValueError("Fichier .keydata mal formaté — pas de `|`")

    # Supprime le préfixe `.keydata` ou suffixe optionnel si présent
    uuid_clean = uuid_part.strip()
    
    if not cipher_hex or len(cipher_hex) < 32:  # IV=32 hex = 16 bytes
        raise ValueError("Ciphertext trop court")

    # Découpe iv + ciphertext (en hex)
    iv_hex, ciphertext_hex = cipher_hex[:32], cipher_hex[32:]
    
    if len(iv_hex) != 32:
        raise ValueError(f"IV invalide — longueur : {len(iv_hex)} (attendu: 32)")

    iv = bytes.fromhex(iv_hex)
    ciphertext = bytes.fromhex(ciphertext_hex)

    # 🔑 Clé = MD5(uuid)
    key = hashlib.md5(uuid_clean.encode("utf-8")).digest()

    # ✅ Déchiffre avec AES-CBC
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_padded = cipher.decrypt(ciphertext)
    
    try:
        decrypted = unpad(decrypted_padded, AES.block_size)
    except ValueError as e:
        raise ValueError(f"Déchiffrement échoué — clé UUID incorrecte ou données corrompues : {e}")

    # Parse JSON
    return json.loads(decrypted.decode("utf-8"))


if __name__ == "__main__":
    file_path = r"C:\Users\clemt\AppData\Roaming\zaap\keydata\.keydata16867972"
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]

    try:
        print(f"🔍 Tentative de déchiffrement : {file_path}")
        data = decrypt_keydata(file_path)
        
        print("=" * 60)
        print("✅ Déchiffrement réussi ! Voici les données décodées :")
        print("-" * 60)
        for k, v in sorted(data.items()):
            if isinstance(v, str) and len(v) > 50:
                print(f"{k} = {v[:48]}...")
            else:
                print(f"{k} = {v}")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Erreur : {e}", file=sys.stderr)
        sys.exit(1)
