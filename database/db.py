# database/db.py
import psycopg2
import pandas as pd
import hashlib
import streamlit as st

# CADENA SUPABASE
# postgresql://postgres.fqqsexqrfplgoyrrdocv:[YOUR-PASSWORD]@aws-1-us-east-2.pooler.supabase.com:6543/postgres

USER = "postgres.fqqsexqrfplgoyrrdocv" #os.getenv("user")
PASSWORD = "USIL$2025$#%" # os.getenv("password")
HOST = "aws-1-us-east-2.pooler.supabase.com" #os.getenv("host")
PORT = "6543" #os.getenv("port")
DBNAME = "postgres" #os.getenv("dbname")

# Función para obtener una conexión a la base de datos
@st.cache_resource
def get_connection():
    """
    Establece y retorna una conexión a la base de datos de Supabase.
    Usa st.cache_resource para reutilizar la conexión entre re-ejecuciones de la app.
    """
    try:
        connection = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME
        )
        return connection
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return None

def verify_user(dni: str, card_number: str, password: str):
    """
    Verifica usuario por DNI + Tarjeta + Clave (en hash SHA-256).
    Retorna row con datos del usuario o None.
    """
    conn = get_connection()
    if conn is None:
        return None

    # Hasheamos la clave para comparar con internet_password_hash
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    try:
        query = """
            SELECT customer_id, full_name, email
            FROM customers
            WHERE dni=%s AND card_number=%s AND internet_password_hash=%s
            LIMIT 1
        """
        with conn.cursor() as cur:
            cur.execute(query, (dni, card_number, password_hash))
            row = cur.fetchone()
        if row:
            return {"customer_id": row[0], "full_name": row[1], "email": row[2]}
        else:
            return None
    except Exception as e:
        st.error(f"Error al verificar usuario: {e}")
        return None
