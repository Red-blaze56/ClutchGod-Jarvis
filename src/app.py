import streamlit as st
from dotenv import load_dotenv
import os
import subprocess

load_dotenv()

st.set_page_config(
    page_title="My Streamlit App",
    layout="wide"
)

st.title("My Streamlit App with Environment Variables")


