import client
import streamlit as st


def add_logo():
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                background-image: url(https://mintlify.s3-us-west-1.amazonaws.com/dagworksinc/logo/dark.png);
                background-repeat: no-repeat;
                background-size: 70%;
                background-position: 20px 20px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def app() -> None:
    """Streamlit entrypoint for PDF Summarize frontend"""
    # config
    st.set_page_config(
        page_title="Retrieval Augmented Generation",
        page_icon="📚",
        layout="centered",
        menu_items={"Get help": None, "Report a bug": None},
    )
    add_logo()

    st.title("📚 Retrieval Augmented Generation")

    if client.get_fastapi_status() is False:
        st.warning("FastAPI is not ready. Make sure your backend is running")
        st.stop()  # exit application after displaying warning if FastAPI is not available

    st.header("Information")
    st.markdown(
        """
    This application allows you to search arXiv for PDFs or import arbitrary PDF files and search over them using LLMs. For each file, the text is divided in chunks that are embedded with OpenAI and stored in Weaviate. When you query the system, the most relevant chunks are retrieved and a summary answer is generated using OpenAI.

    The ingestion and retrieval steps are implemented as dataflows with Hamilton and are exposed via FastAPI endpoints. The frontend is built with Streamlit and exposes the different functionalities via a simple web UI. Everything is packaged as containers with docker compose.

    View the FastAPI docs at http://localhost:8082/docs

    Find the code on [Hamilton's GitHub](https://github.com/apache/hamilton) page.
    """
    )

    st.subheader("Hello from DAGWorks 👋")
    st.markdown(
        """
        We are building and maintaining the Hamitlon project and we're excited to share this RAG example with you!

    📣 join our community on [Slack](https://hamilton-opensource.slack.com/join/shared_invite/zt-1bjs72asx-wcUTgH7q7QX1igiQ5bbdcg#/shared-invite/email) - we're more than happy to help answer questions you might have or get you started.

    ⭐️ us on [GitHub](https://github.com/apache/hamilton)

    📝 leave us an [issue](https://github.com/apache/hamilton/issues) if you find something
    """
    )


if __name__ == "__main__":
    # run as a script to test streamlit app locally
    app()
