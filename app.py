import streamlit as st

st.set_page_config(
    page_title="CDP Intelligence",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from pages import profiles


def main():
    profiles.render()


if __name__ == "__main__":
    main()
