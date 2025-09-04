import streamlit as st
import pyrebase
from firebase_config import firebase_config
from dotenv import load_dotenv
import json
import os

# --- Load Environment Variables ---
load_dotenv()
firebase_key = os.getenv("FIREBASE_API_KEY")

if not firebase_key:
    st.error("Missing FIREBASE_API_KEY. Please check your .env file or Render environment settings.")
    st.stop()

# --- Firebase Setup ---
@st.cache_resource
def init_firebase():
    firebase = pyrebase.initialize_app(firebase_config)
    auth = firebase.auth()
    db = firebase.database()
    return auth, db

auth, db = init_firebase()

# --- Helper Functions ---
def sanitize_email(email):
    return email.replace(".", "_").replace("@", "_at_")

def get_user_role(email):
    safe_email = sanitize_email(email)
    role_data = db.child("users").child(safe_email).get().val()
    return role_data.get("role", "viewer") if role_data else "viewer"

def add_match(token, p1, p2, match_type):
    db.child("matches").child(token).set({
        "first_player": p1,
        "second_player": p2,
        "match_type": match_type,
        "created_by": st.session_state.get("email", "unknown")
    })

def delete_match(token):
    db.child("matches").child(token).remove()

def get_all_matches():
    data = db.child("matches").get().val()
    if data:
        return [{"token": k, **v} for k, v in data.items()]
    return []

# --- Streamlit UI ---
st.set_page_config(page_title="MatchTracker", page_icon="🎯")

st.markdown("<h1 style='text-align: center; color: green;'>🕉️ BABA BOTAL SHAH JI MAHARAJ 🕉️</h1>", unsafe_allow_html=True)
st.markdown("---")

menu = st.sidebar.selectbox("Menu", ["Login", "Sign Up"])

# --- Sign Up ---
if menu == "Sign Up":
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["admin", "viewer"])
    if st.button("Create Account"):
        if not email or not password:
            st.warning("Please fill in all fields.")
        else:
            with st.spinner("Creating account..."):
                try:
                    auth.create_user_with_email_and_password(email, password)
                    safe_email = sanitize_email(email)
                    db.child("users").child(safe_email).set({"role": role})
                    st.success("Account created successfully!")
                except Exception as e:
                    try:
                        error_json = e.args[1]
                        error = json.loads(error_json)['error']['message']
                        st.error(f"Signup failed: {error}")
                    except:
                        st.error(f"Error: {e}")

# --- Login ---
elif menu == "Login":
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if not email or not password:
            st.warning("Please fill in all fields.")
        else:
            with st.spinner("Logging in..."):
                try:
                    user = auth.sign_in_with_email_and_password(email, password)
                    st.session_state["email"] = email
                    st.session_state["role"] = get_user_role(email)
                    st.success(f"Welcome {email}!")
                    st.rerun()
                except Exception as e:
                    try:
                        error_json = e.args[1]
                        error = json.loads(error_json)['error']['message']
                        st.error(f"Login failed: {error}")
                    except:
                        st.error(f"Login failed: {e}")

# --- Dashboard ---
if "email" in st.session_state:
    st.subheader(f"Dashboard ({st.session_state['role'].capitalize()})")

    if st.button("Logout"):
        st.session_state.clear()
        st.success("Logged out successfully.")
        st.rerun()

    st.markdown("## MatchTracker")

    # --- Admin Controls ---
    if st.session_state["role"] == "admin":
        st.markdown("### ➕ Add New Match")
        with st.form("match_form"):
            token = st.text_input("Token No")
            p1 = st.text_input("First Player")
            p2 = st.text_input("Second Player")
            match_type = st.selectbox("Match Type", ["normal", "special"])
            submit_match = st.form_submit_button("Add Match")

            if submit_match:
                if token and p1 and p2:
                    add_match(token, p1, p2, match_type)
                    st.success("Match added successfully!")
                    st.rerun()
                else:
                    st.warning("Please fill all fields.")

        st.markdown("### 🗑️ Delete Match")
        all_matches = get_all_matches()
        match_tokens = [m["token"] for m in all_matches]
        selected_token = st.selectbox("Select Token to Delete", match_tokens)
        if st.button("Delete Match"):
            delete_match(selected_token)
            st.success("Match deleted.")
            st.rerun()

    # --- Refresh Button for All Users ---
    st.markdown("### 🔄 Refresh Match List")
    if st.button("Refresh"):
        st.rerun()

    # --- Match List for All Users ---
    st.markdown("### 📋 All Matches")
    matches = get_all_matches()
    if matches:
        for match in matches:
            with st.expander(f"🎯 Token: {match['token']}"):
                st.write(f"👤 {match['first_player']} vs {match['second_player']}")
                st.write(f"🏷️ Type: {match['match_type']}")
                st.write(f"🛠️ Added by: {match.get('created_by', 'N/A')}")
    else:
        st.info("No matches found.")

# --- Footer ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; font-size: 14px;'>© All rights reserved BABA BOTAL SHAH JI MAHARAJ | Developed by Sidharth</p>",
    unsafe_allow_html=True
)