import streamlit as st

# Credenciales por defecto (usadas si no hay st.secrets disponibles)
_DEFAULT_USERS = {
    "demo": {"name": "Demo", "password": "1234", "premium": False},
    "admin": {"name": "Admin", "password": "adminpass", "premium": True},
}

# Alias público para que otros módulos puedan importar USERS_DB
USERS_DB = _DEFAULT_USERS


def _get_secrets_credentials():
    """
    Intenta leer credenciales desde st.secrets["auth"].
    Retorna (username, password) o None si no están definidas.
    """
    try:
        return st.secrets["auth"]["username"], st.secrets["auth"]["password"]
    except (KeyError, AttributeError):
        return None


def login():
    """
    Muestra campos de login en el sidebar y valida contra st.secrets o USERS_DB.
    Tras autenticación exitosa establece st.session_state["logged_in"] y
    st.session_state["user"] y llama a st.rerun() para rerenderizar el sidebar.
    """
    st.sidebar.header("Iniciar sesión")
    username = st.sidebar.text_input("Usuario")
    password = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Entrar"):
        secrets_creds = _get_secrets_credentials()
        if secrets_creds:
            valid_user, valid_pass = secrets_creds
            if username == valid_user and password == valid_pass:
                user = {"name": username, "premium": True}
                st.session_state["logged_in"] = True
                st.session_state["user"] = user
                st.rerun()
            else:
                st.sidebar.error("Credenciales inválidas")
        else:
            user = USERS_DB.get(username)
            if user and user["password"] == password:
                st.session_state["logged_in"] = True
                st.session_state["user"] = user
                st.rerun()
            else:
                st.sidebar.error("Credenciales inválidas")


def is_premium_user(user):
    return user and user.get("premium", False)
