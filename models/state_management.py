from datetime import datetime
import streamlit as st

state_expiry = 30

def set_state(email_input, password_input):
    st.session_state['username'] = email_input
    st.session_state['password'] = password_input
    st.session_state['session_start'] = datetime.now()
    return st.session_state

def write_state():
    st.write(st.session_state)

def clear_state():
    state = st.session_state
    now = datetime.now()
    try:
        session_duration = now - state['session_start']
        time_diff = session_duration.total_seconds() / 60
        if time_diff > state_expiry:
            for key in state.keys():
                del state[key]
    except:
        pass
    return state