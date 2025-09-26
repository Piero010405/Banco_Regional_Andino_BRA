# app.py
import streamlit as st
from database.db import verify_user
from pathlib import Path

# Configuración página
st.set_page_config(page_title="Banco Regional Andino", page_icon="🏦", layout="centered")

# Cargar estilos CSS
with open("styles/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Variables de sesión para login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# Logo
logo_path = Path("resources/BRA-LOGO-BG.png")
if logo_path.exists():
    st.image(str(logo_path), width=200)

# Si no está logeado → mostrar login
if not st.session_state.logged_in:
    st.title("Acceso Seguro – Banco Regional Andino")

    dni = st.text_input("DNI", max_chars=9, placeholder="Ingresa tu DNI")
    card_number = st.text_input("Número de Tarjeta", placeholder="Ingresa tu Nº de tarjeta")
    password = st.text_input("Clave de Internet (6 dígitos)", type="password", max_chars=6)

    if st.button("Ingresar"):
        if dni and card_number and password:
            user = verify_user(dni, card_number, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.success(f"Bienvenido {user['full_name']}")
                st.experimental_rerun()
            else:
                st.error("Credenciales inválidas. Verifique sus datos.")
        else:
            st.warning("Completa todos los campos para ingresar.")

else:
    # Si está logeado → mostrar dashboard en blanco (futuro)
    st.sidebar.title("Menú")
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.experimental_rerun()

    st.title("Dashboard - Posición Consolidada")
    st.write(f"Bienvenido **{st.session_state.user['full_name']}**. Aquí aparecerá tu dashboard.")
    st.info("Esta pantalla es temporalmente en blanco. Aquí iremos poniendo el dashboard con cuentas, saldos y créditos.")
