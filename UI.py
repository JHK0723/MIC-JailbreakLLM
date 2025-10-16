import streamlit as st, requests
prompt = st.text_area("Enter your prompt:")
if st.button("Submit"):
    res = requests.post("http://localhost:8000/attack", json={"team_id": 1, "prompt": prompt})
    st.write(res.json())
