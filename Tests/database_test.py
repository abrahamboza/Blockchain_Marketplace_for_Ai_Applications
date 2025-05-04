# simple_test.py
from database import DatabaseManager, User


def test_database_connection():
    print("Teste Datenbankverbindung...")
    db_manager = DatabaseManager()
    session = db_manager.get_session()

    # Prüfe, ob die Verbindung erfolgreich ist
    try:
        # Versuche, einen Testbenutzer zu erstellen
        user = User(address="test_user", public_key="test_key")
        session.add(user)
        session.commit()

        # Benutzer abrufen
        saved_user = session.query(User).filter_by(address="test_user").first()
        print(f"Benutzer erfolgreich erstellt mit ID: {saved_user.id}")

        # Benutzer löschen (zum Aufräumen)
        session.delete(saved_user)
        session.commit()

        print("Datenbankverbindung erfolgreich getestet!")
    except Exception as e:
        print(f"Fehler bei Datenbankverbindung: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    test_database_connection()