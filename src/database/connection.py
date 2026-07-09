# src/database/connection.py
from sqlalchemy import create_index, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Usamos SQLite por simplicidad y compatibilidad rápida en Streamlit Cloud
DATABASE_URL = "sqlite:///./operaciones.db"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Requerido para que Streamlit use múltiples hilos sin bloquearse
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
