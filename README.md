# 🔐 Blockchain Marketplace for AI Applications

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A decentralized marketplace for AI data and machine learning models, leveraging blockchain technology for transparency, security, and data ownership.

## 🌟 Overview

This project implements a secure, decentralized platform where AI researchers, data scientists, and organizations can share, discover, purchase, and monetize datasets and machine learning models. By utilizing blockchain technology, all transactions are transparent and immutable, while maintaining privacy through end-to-end encryption.

## ✨ Key Features

- **🔗 Blockchain Integration**: All transactions recorded on an immutable blockchain
- **🔒 End-to-End Encryption**: All data is encrypted with only authorized users having access
- **🏪 Decentralized Marketplace**: Upload, sell, purchase, and manage datasets and models
- **👤 User Authentication**: Secure blockchain-based user identification
- **🔍 Data Transparency**: View and verify all blockchain transactions
- **🛡️ Data Ownership**: Clear provenance and ownership records
- **⚙️ Admin Dashboard**: Comprehensive administrative interface with analytics
- **📊 Database Management**: Synchronized relational database with blockchain data

## 🛠️ Technology Stack

- **Backend**: Python, Flask
- **Database**: SQLite via SQLAlchemy ORM
- **Encryption**: Cryptography library with Fernet symmetric encryption
- **Frontend**: HTML, CSS, Bootstrap 5, JavaScript
- **Blockchain**: Custom Python blockchain implementation

## 🏗️ Architecture

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

## 📂 Project Structure

```
├── app.py                  # Main Flask application
├── database.py             # Database models and connection management
├── database_handling.py    # Database and blockchain synchronization
├── encryption.py           # Encryption and decryption utilities
├── key_manager.py          # Encryption key management
├── marketplace.py          # Marketplace blockchain implementation
├── db_manager_tool.py      # CLI tool for database management
├── Blockchain/             # Core blockchain implementation
│   └── blockchain.py       # Blockchain functionality
├── Tests/                  # Test scripts
│   ├── blockchain_test_basics.py
│   ├── database_test.py
│   └── marketplace_test.py
└── templates/              # HTML templates for web UI
```

## 🚀 Installation & Setup

### Prerequisites

- Python 3.8+
- pip
- Git

### Installation Steps

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/Blockchain_Marketplace_for_Ai_Applications.git
   cd Blockchain_Marketplace_for_Ai_Applications
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv .venv
   
   # On Windows
   .\.venv\Scripts\activate
   
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. Install dependencies
   ```bash
   pip install flask sqlalchemy cryptography
   ```

4. Initialize the database (with fresh reset)
   ```bash
   python app.py --reset
   ```

5. Run the application
   ```bash
   python app.py
   ```

6. Access the web interface at http://localhost:5000

## 📱 Usage Guide

### For Users

1. **Home Page**: Navigate through the main features of the marketplace
2. **Upload Dataset**: Share datasets securely with optional pricing
3. **View Blockchain**: Explore and verify all blockchain transactions

### For Data Scientists & Researchers

1. **Data Access**: Purchase and securely access datasets and models
2. **Encryption**: All transferred data is encrypted end-to-end
3. **Verification**: Verify data authenticity through the blockchain

### For Administrators

1. **Admin Dashboard**: Access with password "passwort"
2. **Database View**: Monitor all data, both encrypted and decrypted
3. **System Reset**: Reset database and blockchain when needed
4. **Data Management**: Download and manage all datasets

## 🔐 Security Features

- **End-to-End Encryption**: All files are encrypted with Fernet symmetric encryption
- **Decentralized Access Control**: All permissions are verified via blockchain
- **Key Management**: Encryption keys are managed separately from data
- **Blockchain Verification**: All transactions verified through consensus mechanisms

## 🧪 Testing

To run the included test suite:

```bash
# Test basic blockchain functionality
python Tests/blockchain_test_basics.py

# Test database connections
python Tests/database_test.py

# Test marketplace operations
python Tests/marketplace_test.py
```

## 🛠️ Administration

### Database Management Tool

A command-line tool is included for database operations:

```bash
# Reset the database entirely
python db_manager_tool.py --reset

# View database status
python db_manager_tool.py --status

# Clear encryption keys only
python db_manager_tool.py --clean-keys
```

### System Reset

You can also reset the system through the admin dashboard using the "Reset Entire System" button.

## 🚧 Future Development

- Peer-to-peer networking for true decentralization
- Integration with IPFS for distributed storage
- Smart contracts for automated transactions
- Web3 wallet integration for cryptocurrency payments
- Advanced analytics and recommendation engine
- Mobile applications for iOS and Android


## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- Florian Kuhlert - Initial development and concept

## 🙏 Acknowledgments

- Bitcoin whitepaper for inspiration on blockchain architecture
- Cryptography.io for encryption libraries
- Flask and SQLAlchemy for web application foundation

---

**Note**: This project is for demonstration and educational purposes.