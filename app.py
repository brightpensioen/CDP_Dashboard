import streamlit as st

st.set_page_config(
    page_title="CDP Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from pages import overview, profiles, source_tracking

PAGES = {
    "Overview": overview,
    "Profiles": profiles,
    "Source Tracking": source_tracking,
}

def main():
    with st.sidebar:
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:24px;">
                <div style="width:8px;height:8px;border-radius:50%;background:#1d9e75;animation:none;"></div>
                <span style="font-size:18px;font-weight:600;letter-spacing:-0.02em;">CDP Intelligence</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Navigation")
        page_name = st.radio(
            "Go to",
            list(PAGES.keys()),
            label_visibility="collapsed",
        )

        st.divider()

        st.markdown(
            """
            <div style="font-size:11px;color:#888;line-height:1.6;">
                <b>Data sources</b><br>
                <code>ds_cdp.tab_profiles</code><br>
                <code>ds_cdp.vw_source_tracking_enriched</code>
            </div>
            """,
            unsafe_allow_html=True,
        )

    PAGES[page_name].render()


if __name__ == "__main__":
    main()
