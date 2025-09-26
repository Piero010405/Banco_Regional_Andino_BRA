import streamlit as st
from pathlib import Path
from database.db import verify_user  # tu función para validar login

# =============================
# CONFIGURACIÓN DE LA PÁGINA
# =============================
st.set_page_config(page_title="Banco Regional Andino", page_icon="🏦", layout="centered")

# =============================
# CARGAR ESTILOS CSS
# =============================
style_path = Path("styles/style.css")
if style_path.exists():
    with open(style_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# =============================
# LOGO
# =============================
logo_path = Path("resources/BRA-LOGO-BG.png")
if logo_path.exists():
    st.image(str(logo_path), width=200)

# =============================
# VARIABLES DE SESIÓN
# =============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

# =============================
# LOGIN
# =============================
if not st.session_state.logged_in:
    st.title("Acceso Seguro – Banco Regional Andino")

    dni = st.text_input("DNI", max_chars=9, placeholder="Ingresa tu DNI")
    card_number = st.text_input("Número de Tarjeta", placeholder="Ingresa tu Nº de tarjeta")
    password = st.text_input("Clave de Internet (6 dígitos)", type="password", max_chars=6)

    if st.button("Ingresar"):
        if dni and card_number and password:
            user = verify_user(dni, card_number, password)  # tu función db.py
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                # No usamos st.experimental_rerun()
                st.success(f"Bienvenido {user['full_name']}")
            else:
                st.error("Credenciales inválidas. Verifique sus datos.")
        else:
            st.warning("Completa todos los campos para ingresar.")

# =============================
# DASHBOARD (placeholder)
# =============================
else:
    st.sidebar.title("Menú")
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.experimental_rerun()  # Aquí sí está bien porque vuelve a login

    st.title("Dashboard - Posición Consolidada")
    st.write(f"Bienvenido **{st.session_state.user['full_name']}**. Aquí aparecerá tu dashboard.")
    st.info("Esta pantalla es temporalmente en blanco. Aquí iremos poniendo el dashboard con cuentas, saldos y créditos.")
