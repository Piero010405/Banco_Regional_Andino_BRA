# database/db.py
import psycopg2
import pandas as pd
import hashlib
import streamlit as st
import os

# Cargar secrets de Streamlit Cloud (o .env en local)
if os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

DB_USER = os.getenv("DB_USER", st.secrets.get("DB_USER"))
DB_PASSWORD = os.getenv("DB_PASSWORD", st.secrets.get("DB_PASSWORD"))
DB_HOST = os.getenv("DB_HOST", st.secrets.get("DB_HOST"))
DB_PORT = os.getenv("DB_PORT", st.secrets.get("DB_PORT"))
DB_NAME = os.getenv("DB_NAME", st.secrets.get("DB_NAME"))

# Función para obtener una conexión a la base de datos
@st.cache_resource
def get_connection():
    """
    Establece y retorna una conexión a la base de datos de Supabase.
    Usa st.cache_resource para reutilizar la conexión entre re-ejecuciones de la app.
    """
    try:
        connection = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME
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
    
# --- Consultas por cliente ---
def get_accounts_summary(customer_id):
    """Resumen de cuentas del cliente."""
    conn = get_connection()
    query = """
    SELECT account_id, account_type, account_number, balance, currency, status
    FROM accounts
    WHERE customer_id=%s
    """
    return pd.read_sql(query, conn, params=(customer_id,))

def get_transactions_by_customer(customer_id):
    """Movimientos de todas las cuentas del cliente."""
    conn = get_connection()
    query = """
    SELECT t.transaction_id, a.account_number, t.date, t.type, t.description, t.amount, t.balance_after
    FROM transactions t
    JOIN accounts a ON a.account_id = t.account_id
    WHERE a.customer_id=%s
    ORDER BY t.date DESC
    """
    return pd.read_sql(query, conn, params=(customer_id,))

def get_loans_summary(customer_id):
    """Préstamos solicitados/activos del cliente."""
    conn = get_connection()
    query = """
    SELECT loan_id, loan_amount, loan_term_months, loan_type, existing_monthly_debt,
           application_date, status
    FROM loans
    WHERE customer_id=%s
    ORDER BY application_date DESC
    """
    return pd.read_sql(query, conn, params=(customer_id,))

def get_loan_evaluations(customer_id):
    """Evaluaciones de préstamos para el cliente."""
    conn = get_connection()
    query = """
    SELECT le.evaluation_id, le.loan_id, le.pred_class, le.risk_level,
           le.monthly_payment, le.dti, le.decision, le.evaluated_at
    FROM loan_evaluations le
    JOIN loans l ON l.loan_id = le.loan_id
    WHERE l.customer_id=%s
    ORDER BY le.evaluated_at DESC
    """
    return pd.read_sql(query, conn, params=(customer_id,))

# --- Para módulo admin / revisión manual ---
def get_pending_loans():
    """Préstamos pendientes de revisión/aprobación (admin)."""
    conn = get_connection()
    query = """
    SELECT l.loan_id, c.full_name, l.loan_amount, l.loan_term_months, l.loan_type,
           l.existing_monthly_debt, l.application_date, l.status,
           le.pred_class, le.risk_level, le.monthly_payment, le.dti, le.decision
    FROM loans l
    JOIN customers c ON l.customer_id=c.customer_id
    LEFT JOIN loan_evaluations le ON le.loan_id=l.loan_id
    WHERE le.decision='Revisión Manual'
    ORDER BY l.application_date DESC
    """
    return pd.read_sql(query, conn)

# --- Insertar nueva solicitud de préstamo ---
def insert_loan(customer_id, loan_amount, loan_term_months, loan_type, existing_monthly_debt, status='Pendiente'):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO loans (customer_id, loan_amount, loan_term_months, loan_type, existing_monthly_debt, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING loan_id;
            """, (customer_id, loan_amount, loan_term_months, loan_type, existing_monthly_debt, status))
            loan_id = cur.fetchone()[0]
        conn.commit()
        return loan_id
    except Exception as e:
        st.error(f"Error al insertar préstamo: {e}")
        return None

# --- Insertar evaluación de préstamo ---
def insert_loan_evaluation(loan_id, pred_class, risk_level, monthly_payment, dti, decision):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO loan_evaluations (loan_id, pred_class, risk_level, monthly_payment, dti, decision)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (loan_id, pred_class, risk_level, monthly_payment, dti, decision))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error al insertar evaluación de préstamo: {e}")
        return False

def get_customer_profile(customer_id):
    from .connection import get_connection  # si tienes un helper para conexión
    conn = get_connection()
    query = """
        SELECT c.full_name, c.marital_status, c.gender, c.birth_date,
               p.age, p.net_monthly_income, p.credit_score,
               p.time_with_curr_empr, p.tot_active_tl, p.tot_missed_pmnt
        FROM customers c
        LEFT JOIN customer_profiles p ON c.customer_id = p.customer_id
        WHERE c.customer_id = %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (customer_id,))
        row = cur.fetchone()
    conn.close()
    if row:
        cols = ['full_name', 'marital_status', 'gender', 'birth_date',
                'age', 'net_monthly_income', 'credit_score',
                'time_with_curr_empr', 'tot_active_tl', 'tot_missed_pmnt']
        return dict(zip(cols, row))
    return {}