import sys

import streamlit as st
import streamlit_antd_components as sac

from chatchat import __version__
from chatchat.server.utils import api_address
from chatchat.webui_pages.dialogue.dialogue import  dialogue_page
from chatchat.webui_pages.kb_chat import kb_chat
from chatchat.webui_pages.mcp import mcp_management_page
from chatchat.webui_pages.knowledge_base.knowledge_base import knowledge_base_page
from chatchat.webui_pages.utils import *

api = ApiRequest(base_url=api_address())

if __name__ == "__main__":
    is_lite = "lite" in sys.argv  # TODO: remove lite mode

    st.set_page_config(
        "Apollo-Chatchat WebUI",
        get_img_base64("chatchat_icon_blue_square_v2.png"),
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://github.com/Joseff531/Apollo-Chatchat",
            "Report a bug": "https://github.com/Joseff531/Apollo-Chatchat/issues",
            "About": f"""Welcome to Apollo-Chatchat WebUI {__version__}!""",
        },
        layout="centered",
    )

    # use the following code to set the app to wide mode and the html markdown to increase the sidebar width
    st.markdown(
        """
        <style>
        [data-testid="stSidebarUserContent"] {
            padding-top: 20px;
        }
        .block-container {
            padding-top: 25px;
        }
        [data-testid="stBottomBlockContainer"] {
            padding-bottom: 20px;
        }
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.image(
            get_img_base64("logo-long-chatchat-trans-v2.png"), use_column_width=True
        )
        st.caption(
            f"""<p align="right">Current version: {__version__}</p>""",
            unsafe_allow_html=True,
        )

        selected_page = sac.menu(
            [
                sac.MenuItem("Multifunction Chat", icon="chat"),
                sac.MenuItem("RAG Chat", icon="database"),
                sac.MenuItem("Knowledge Base Management", icon="hdd-stack"),
                sac.MenuItem("MCP Management", icon="hdd-stack"),
            ],
            key="selected_page",
            open_index=0,
        )

        sac.divider()

    if selected_page == "Knowledge Base Management":
        knowledge_base_page(api=api, is_lite=is_lite)
    elif selected_page == "RAG Chat":
        kb_chat(api=api)
    elif selected_page == "MCP Management":
        mcp_management_page(api=api)
    else:
        dialogue_page(api=api, is_lite=is_lite)
