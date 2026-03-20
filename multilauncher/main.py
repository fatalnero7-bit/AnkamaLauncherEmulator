# multilauncher/main.py

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QListWidget,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from identity import get_stored_keydata, generate_persistent_identity, save_identity
from dofus_starter import launch_dofus
from auth import request_ticket_for_identity


class MultiLauncherGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MultiLauncher - Dofus")
        self.resize(700, 500)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Titre
        title = QPushButton("MultiLauncher — Dofus")
        title.setStyleSheet(
            "font-size: 20pt; font-weight: bold; color: #2979ff; background: transparent;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Description subtile
        desc = QPushButton("Lancez plusieurs comptes simultanément via fingerprint matériel unique")
        desc.setStyleSheet(
            "font-size: 10pt; color: #757575; background: transparent;"
        )
        desc.setFlat(True)
        layout.addWidget(desc)

        # Bouton principal
        self.launch_btn = QPushButton("▶ Lancer un compte")
        self.launch_btn.setStyleSheet("""
            QPushButton {
                font-size: 14pt;
                padding: 10px;
                background-color: #2979ff;
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #1e5cc9; }
        """)
        self.launch_btn.clicked.connect(self._launch_account)
        layout.addWidget(self.launch_btn)

        # Liste des comptes
        label_list = QPushButton("Comptes disponibles :")
        label_list.setFlat(True)
        layout.addWidget(label_list)

        self.account_list = QListWidget()
        self._refresh_accounts()
        layout.addWidget(self.account_list)

        # Info barre (statut)
        self.status_bar = QPushButton("")
        self.status_bar.setStyleSheet("color: #616161; background: transparent;")
        self.status_bar.setFlat(True)
        layout.addWidget(self.status_bar)

        self.setCentralWidget(central)
        self._refresh_status("En attente de lancement")

    def _refresh_accounts(self):
        self.accounts = get_stored_keydata()
        self.account_list.clear()
        for acc in self.accounts:
            uuid = acc["uuid"]
            # Essaye d’extraire le login (ex: "clemt") — ici on affiche un résumé
            login_display = f"{uuid[:8]}..."  # fallback
            item_text = f"👤 {login_display}"
            self.account_list.addItem(item_text)

    def _refresh_status(self, msg: str):
        self.status_bar.setText(msg)

    def _launch_account(self):
        if not self.accounts:
            QMessageBox.warning(self, "Erreur", "Aucun compte trouvé dans:\n`C:\\Users\\clemt\\AppData\\Roaming\\zaap\\keydata`")
            return

        selected = self.account_list.currentRow()
        if selected < 0:
            selected = 0
        account = self.accounts[selected]

        # Générer identité persistante (unique & stable)
        identity = generate_persistent_identity(account["cipher"])

        try:
            self._refresh_status(f"Demande de ticket pour {identity['machine_id'][:12]}...")
            ticket = request_ticket_for_identity(identity)

            if not ticket:
                raise RuntimeError("Échec de l'obtention du ticket. Vérifiez votre connexion.")

            pid = launch_dofus(ticket, identity)
            self._refresh_status(f"Dofus lancé (PID: {pid}) — Compte : {identity['machine_id'][:12]}")
            QMessageBox.information(self, "Lancement", f"Dofus est en cours d’exécution.\n\nMachine ID : {identity['machine_id']}")

        except Exception as e:
            self._refresh_status(f"Erreur : {e}")
            QMessageBox.critical(self, "Échec", f"Le lancement a échoué :\n{str(e)}")


def main():
    app = QApplication(sys.argv)
    window = MultiLauncherGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
