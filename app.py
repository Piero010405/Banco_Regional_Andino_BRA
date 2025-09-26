import streamlit as st
from pathlib import Path
from database.db import verify_user 

# --- DB Functions ---
from database.db import (
    verify_user,
    get_accounts_summary,
    get_transactions_by_customer,
    get_loans_summary,
    get_loan_evaluations,
    insert_loan,
    insert_loan_evaluation
)

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

## MODELO
# Riesgo Crediticio
@st.cache_resource
def load_credit_model():
    try:
        with open('components/demo_model.pkl', 'rb') as f:
            model = pickle.load(f)
        return model
    except FileNotFoundError:
        st.error("No se encontró el archivo del modelo de crédito.")
        return None

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

# =============================
# DASHBOARD
# =============================
else:
    st.sidebar.title("Menú")
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.experimental_rerun()

    customer_id = st.session_state.user['customer_id']
    st.title("🏦 Dashboard – Posición Consolidada")
    st.write(f"Bienvenido **{st.session_state.user['full_name']}**")

    # --- Tabs ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Cuentas", "💳 Movimientos", "📄 Préstamos", "📝 Solicitud de Crédito"])

    # =============================
    # TAB 1 – Cuentas
    # =============================
    with tab1:
        st.subheader("Resumen de Cuentas")
        accounts_df = get_accounts_summary(customer_id)
        if not accounts_df.empty:
            st.dataframe(accounts_df, use_container_width=True)

            # Gráfico de barras balances
            chart_df = accounts_df.groupby('account_type')['balance'].sum().reset_index()
            st.bar_chart(chart_df.set_index('account_type'))
        else:
            st.info("No se encontraron cuentas para este cliente.")

    # =============================
    # TAB 2 – Movimientos
    # =============================
    with tab2:
        st.subheader("Movimientos Recientes")
        tx_df = get_transactions_by_customer(customer_id)
        if not tx_df.empty:
            st.dataframe(tx_df, use_container_width=True)
        else:
            st.info("No hay transacciones registradas.")

    # =============================
    # TAB 3 – Préstamos
    # =============================
    with tab3:
        st.subheader("Préstamos")
        loans_df = get_loans_summary(customer_id)
        evals_df = get_loan_evaluations(customer_id)

        if not loans_df.empty:
            st.write("### Solicitudes y Préstamos")
            st.dataframe(loans_df, use_container_width=True)

            if not evals_df.empty:
                st.write("### Evaluaciones")
                st.dataframe(evals_df, use_container_width=True)
        else:
            st.info("No se encontraron préstamos para este cliente.")

    # =============================
    # TAB 4 – Solicitud de Crédito
    # =============================
    with tab4:
        st.subheader("Nueva Solicitud de Crédito")

        credit_model = load_credit_model()

        col1, col2 = st.columns(2)
        with col1:
            loan_amount = st.number_input("Monto solicitado (S/.)", min_value=0.0, value=10000.0, step=100.0)
            loan_term_months = st.number_input("Plazo (meses)", min_value=1, value=24, step=1)
            loan_type = st.selectbox("Tipo de crédito", ["Libre inversión", "Hipotecario", "Auto", "Consumo"])
            existing_monthly_debt = st.number_input("Deuda mensual actual (S/.)", min_value=0.0, value=0.0, step=50.0)
        with col2:
            net_income = st.number_input("Ingreso mensual neto (S/.)", min_value=0.0, value=2000.0, step=100.0)
            credit_score = st.number_input("Puntaje Crediticio", min_value=0, value=600, step=10)
            age = st.number_input("Edad", min_value=18, value=30, step=1)
            time_employed = st.number_input("Tiempo con empleador (meses)", min_value=0, value=12, step=1)

        # Cálculo cuota mensual
        interest_rates_by_type = {
            "Libre inversión": 0.25,
            "Hipotecario": 0.10,
            "Auto": 0.18,
            "Consumo": 0.30
        }
        r_annual = interest_rates_by_type[loan_type]
        r_month = r_annual / 12
        n = loan_term_months
        PV = loan_amount

        if r_month == 0:
            monthly_payment = PV / n
        else:
            monthly_payment = r_month * PV / (1 - (1 + r_month) ** (-n))

        st.write(f"**Cuota mensual estimada:** S/. {monthly_payment:,.2f}")

        dti = (existing_monthly_debt + monthly_payment) / max(1e-6, net_income)
        st.write(f"**DTI estimado:** {dti:.2%}")

        # Predicción con modelo
        if credit_model is not None:
            # Aquí armas tu vector según tu modelo entrenado
            features = np.array([[age, net_income, credit_score, time_employed]])
            pred_class = credit_model.predict(features)[0]
        else:
            pred_class = "P2"  # placeholder

        class_risk_map = {
            "P1": "alto",
            "P2": "medio",
            "P3": "bajo",
            "P4": "muy bajo"
        }
        risk = class_risk_map.get(pred_class, "desconocido")

        # Decisión simple
        decision = "Revisión Manual"
        if (risk in ["bajo", "muy bajo"]) and (dti <= 0.35):
            decision = "Aprobado"
        elif (risk == "alto") or (dti > 0.50):
            decision = "Rechazado"

        st.success(f"**Decisión recomendada:** {decision} — Perfil: {pred_class} ({risk})")

        if st.button("Enviar Solicitud"):
            # Insertar en DB
            loan_id = insert_loan(customer_id, loan_amount, loan_term_months, loan_type, existing_monthly_debt, status='Pendiente')
            if loan_id:
                ok = insert_loan_evaluation(loan_id, pred_class, risk, monthly_payment, dti * 100, decision)
                if ok:
                    st.success("Solicitud y evaluación guardadas correctamente.")
                else:
                    st.error("Error al guardar la evaluación del préstamo.")
            else:
                st.error("Error al guardar la solicitud de préstamo.")