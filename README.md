# 🔐 Dezentrale Sicherheit und mathematische Fundamente: Blockchain als Infrastruktur für datenbasierte Lernsysteme


**THN | Fakultät für Angewandte Mathematik und Physik**

---

## 🌟 Überblick

Dieses Projekt implementiert einen Mockup welcher die Vorstufe eines Marktplatzes sein soll welcher eine sichere, dezentralisierte Plattform, auf der KI-Forscher, Datenwissenschaftler und Organisationen Datensätze und Machine-Learning-Modelle teilen, entdecken, kaufen und monetarisieren können. Durch den Einsatz der Blockchain-Technologie werden alle Transaktionen transparent und unveränderlich gespeichert, während gleichzeitig die Privatsphäre durch Ende-zu-Ende-Verschlüsselung gewahrt bleibt.

## ✨ Hauptfunktionen

- **🔗 Blockchain-Integration**: Alle Transaktionen werden auf einer unveränderlichen Blockchain protokolliert
- **🔒 Ende-zu-Ende-Verschlüsselung**: Sämtliche Daten werden verschlüsselt, wobei nur autorisierte Nutzer Zugriff haben
- **🏪 Dezentraler Marktplatz**: Upload, Verkauf, Kauf und Verwaltung von Datensätzen und Modellen
- **👤 Benutzerauthentifizierung**: Sichere blockchain-basierte Benutzeridentifikation
- **🔍 Datentransparenz**: Einsicht und Verifizierung aller Blockchain-Transaktionen
- **🛡️ Datenhoheit**: Klare Herkunfts- und Eigentumsnachweise
- **⚙️ Administrationsoberfläche**: Umfassende Verwaltungsschnittstelle mit Analysefunktionen
- **📊 Datenbankmanagement**: Synchronisierte relationale Datenbank mit Blockchain-Daten
- **📦 IPFS-Integration**: Dezentralisierte Speicherung von Datensätzen und Modellen
- **🤖 Modelltraining-Funktionalität**: Direkte Erstellung von Machine-Learning-Modellen

## 🧮 Mathematische Grundlagen

Die Implementierung basiert auf folgenden kryptographischen und mathematischen Prinzipien:

- **SHA-256 Hashing**: Sicherstellung der Blockchain-Integrität
- **Proof-of-Work**: Konsensalgorithmus mit anpassbarer Schwierigkeit
- **Kryptographische Signaturen**: Verifizierung und Authentifizierung von Transaktionen
- **Symmetrische Verschlüsselung**: Fernet-basierte Verschlüsselung für sicheren Datenaustausch

## 🛠️ Technologie-Stack

- **Backend**: Python, Flask
- **Datenbank**: SQLite via SQLAlchemy ORM
- **Verschlüsselung**: Cryptography-Bibliothek mit Fernet
- **Frontend**: HTML, CSS, Bootstrap 5, JavaScript
- **Blockchain**: Maßgeschneiderte Python-Blockchain-Implementierung
- **Speicherung**: Simulierte IPFS-Integration
- **Machine Learning**: Sklearn-basierte Modelltraining-Funktionalität

## 🏗️ Architektur

```
┌─────────────────────┐     ┌─────────────────────┐
│   Flask Web App     │     │  Blockchain Node    │
│                     │     │                     │
│  ┌───────────────┐  │     │  ┌───────────────┐  │
│  │ User Interface│◄─┼─────┼─►│Block Validation│  │
│  └───────────────┘  │     │  └───────────────┘  │
│                     │     │                     │
│  ┌───────────────┐  │     │  ┌───────────────┐  │
│  │Data Management│◄─┼─────┼─►│ Transaction   │  │
│  └───────────────┘  │     │  │ Processing    │  │
│                     │     │  └───────────────┘  │
└─────────────────────┘     └─────────────────────┘
         ▲                            ▲
         │                            │
         ▼                            ▼
┌─────────────────────┐     ┌─────────────────────┐
│   Database Layer    │     │   Encryption Layer  │
│                     │     │                     │
│  ┌───────────────┐  │     │  ┌───────────────┐  │
│  │SQLite Database│  │     │  │ Fernet Crypto │  │
│  └───────────────┘  │     │  └───────────────┘  │
│                     │     │                     │
│  ┌───────────────┐  │     │  ┌───────────────┐  │
│  │    ORM        │  │     │  │Key Management │  │
│  └───────────────┘  │     │  └───────────────┘  │
└─────────────────────┘     └─────────────────────┘
```

## 📂 Projektstruktur

```
├── app.py                  # Haupt-Flask-Anwendung
├── database.py             # Datenbankmodelle und Verbindungsmanagement
├── database_handling.py    # Datenbank- und Blockchain-Synchronisation
├── encryption.py           # Verschlüsselungs- und Entschlüsselungs-Utilities
├── key_manager.py          # Verwaltung der Verschlüsselungsschlüssel
├── marketplace.py          # Marktplatz-Blockchain-Implementierung
├── Blockchain/             # Kern-Blockchain-Implementierung
│   └── blockchain.py       # Blockchain-Funktionalität
├── Storage_IPFS_sim/       # IPFS-Simulationskomponente
│   └── simulated_ipfs.py   # Simulierte IPFS-Implementierung
├── Tests/                  # Testskripte
│   ├── blockchain_test_basics.py
│   ├── database_test.py
│   └── marketplace_test.py
└── templates/              # HTML-Vorlagen für Web-UI
```

## 📱 Benutzeroberfläche

## 🚀 Installation & Setup

### Voraussetzungen

- Python 3.8+
- pip
- Git

### Installationsschritte

1. Repository klonen
   ```bash
   git clone https://github.com/yourusername/Blockchain_Marketplace_for_Ai_Applications.git
   cd Blockchain_Marketplace_for_Ai_Applications
   ```

2. Virtuelle Umgebung erstellen und aktivieren
   ```bash
   python -m venv .venv
   
   # Unter Windows
   .\.venv\Scripts\activate
   
   # Unter macOS/Linux
   source .venv/bin/activate
   ```

3. Abhängigkeiten installieren
   ```bash
   pip install requirements.txt
   ```

4. Datenbank initialisieren (mit Neusetzung)
   ```bash
   python app.py --reset
   ```

5. Anwendung starten
   ```bash
   python app.py
   ```

6. Web-Interface unter http://localhost:5000 aufrufen

## 🔐 Sicherheitsmerkmale

- **Ende-zu-Ende-Verschlüsselung**: Alle Dateien werden mit Fernet-symmetrischer Verschlüsselung gesichert
- **Dezentrale Zugriffskontrolle**: Alle Berechtigungen werden über die Blockchain verifiziert
- **Schlüsselverwaltung**: Verschlüsselungsschlüssel werden getrennt von den Daten verwaltet
- **Blockchain-Verifikation**: Alle Transaktionen werden durch Konsensmechanismen verifiziert

## 🧪 Tests

Zum Ausführen der mitgelieferten Testsuite:

```bash
# Test der grundlegenden Blockchain-Funktionalität
python Tests/blockchain_test_basics.py

# Test der Datenbankverbindungen
python Tests/database_test.py

# Test der Marktplatzoperationen
python Tests/marketplace_test.py
```

## 👥 Autor

- [Florian Kuhlert] - Entwicklung und Konzeption

**Hinweis**: Dieses Projekt dient Demonstrations- und Bildungszwecken.