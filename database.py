from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, Table, Text, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os
import json
from datetime import datetime

Base = declarative_base()

# Viele-zu-viele Beziehungstabelle für Datenkäufer
data_purchases = Table('data_purchases', Base.metadata,
                       Column('user_id', Integer, ForeignKey('users.id')),
                       Column('data_id', Integer, ForeignKey('data_entries.id'))
                       )

# Viele-zu-viele Beziehungstabelle für Modellkäufer
model_purchases = Table('model_purchases', Base.metadata,
                        Column('user_id', Integer, ForeignKey('users.id')),
                        Column('model_id', Integer, ForeignKey('model_entries.id'))
                        )


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    address = Column(String(64), unique=True, nullable=False)
    public_key = Column(String(256), nullable=True)

    # Beziehungen
    owned_data = relationship("DataEntry", back_populates="owner")
    owned_models = relationship("ModelEntry", back_populates="owner")
    purchased_data = relationship("DataEntry", secondary=data_purchases, back_populates="purchased_by")
    purchased_models = relationship("ModelEntry", secondary=model_purchases, back_populates="purchased_by")


class DataEntry(Base):
    __tablename__ = 'data_entries'

    id = Column(Integer, primary_key=True)
    data_id = Column(String(64), unique=True, nullable=False)  # Blockchain-Transaktions-ID
    owner_id = Column(Integer, ForeignKey('users.id'))
    data_metadata = Column(Text)  # JSON-Metadaten (vorher: metadata)
    price = Column(Float, nullable=False)
    timestamp = Column(Float, nullable=False)

    # Beziehungen
    owner = relationship("User", back_populates="owned_data")
    purchased_by = relationship("User", secondary=data_purchases, back_populates="purchased_data")
    encrypted_file = relationship("EncryptedFile", uselist=False, back_populates="data_entry")


class ModelEntry(Base):
    __tablename__ = 'model_entries'

    id = Column(Integer, primary_key=True)
    model_id = Column(String(64), unique=True, nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'))
    model_metadata = Column(Text)  # Umbenannt von metadata
    price = Column(Float, nullable=False)
    timestamp = Column(Float, nullable=False)

    # Beziehungen
    owner = relationship("User", back_populates="owned_models")
    purchased_by = relationship("User", secondary=model_purchases, back_populates="purchased_models")
    encrypted_file = relationship("EncryptedFile", uselist=False, back_populates="model_entry")


# Modification to database.py - EncryptedFile class

class EncryptedFile(Base):
    __tablename__ = 'encrypted_files'

    id = Column(Integer, primary_key=True)
    file_hash = Column(String(64), unique=True)
    encrypted_content = Column(LargeBinary, nullable=True)  # Now optional since we can use IPFS
    ipfs_cid = Column(String(64), nullable=True)  # New: IPFS Content Identifier
    encryption_key_hash = Column(String(64))
    data_entry_id = Column(Integer, ForeignKey('data_entries.id'), nullable=True)
    model_entry_id = Column(Integer, ForeignKey('model_entries.id'), nullable=True)

    # Beziehungen
    data_entry = relationship("DataEntry", back_populates="encrypted_file")
    model_entry = relationship("ModelEntry", back_populates="encrypted_file")


class DatabaseManager:
    def __init__(self, db_url='sqlite:///marketplace.db'):
        """Initialisiert die Datenbankverbindung

        Args:
            db_url: Verbindungsstring zur Datenbank
                    (sqlite:///marketplace.db für lokale SQLite-DB)
                    (postgresql://username:password@localhost/dbname für PostgreSQL)
        """
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        """Gibt eine neue Datenbanksitzung zurück"""
        return self.Session()

# In database.py hinzufügen (nach den anderen Klassen wie User, DataEntry, etc.)
class BlockEntry(Base):
    __tablename__ = 'blocks'

    id = Column(Integer, primary_key=True)
    index = Column(Integer, nullable=False, unique=True)
    previous_hash = Column(String(64), nullable=False)
    timestamp = Column(Float, nullable=False)
    proof = Column(Integer, nullable=False)
    block_hash = Column(String(64), nullable=False)
    # JSON-Repräsentation der Transaktionen
    transactions_json = Column(Text, nullable=False)