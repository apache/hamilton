# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import base64
from pathlib import Path

import requests
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile


@st.cache_data
def pdf_to_base64(uploaded_file: UploadedFile) -> str:
    """Display the PDF as an embedded b64 string in a markdown component"""
    base64_pdf = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
    return f'<embed src="data:application/pdf;base64,{base64_pdf}" width=100% height=800 type="application/pdf">'


def post_pdf(
    uploaded_file: UploadedFile,
    openai_gpt_model: str,
    content_type: str,
    user_query: str,
) -> requests.Response:
    """POST request to `http://fastapi_server` which exists in the Docker stack"""
    server_url = "http://fastapi_server:8080/summarize_sync"
    files = {"pdf_file": uploaded_file}
    response = requests.post(
        server_url,
        files=files,
        data=dict(
            openai_gpt_model=openai_gpt_model,
            content_type=content_type,
            user_query=user_query,
        ),
    )
    return response


def set_output_filename_state(filename: str) -> None:
    """Set the output filename in the streamlit state"""
    filename = Path(filename)
    st.session_state["ouput_filename"] = f"summary_{filename.stem}.txt"


def set_summary_state(summary: str) -> None:
    """Set the summary in the streamlit state"""
    st.session_state["summary"] = summary


def summarize_callback(
    uploaded_file: UploadedFile,
    openai_gpt_model: str,
    content_type: str,
    user_query: str,
) -> None:
    """`Summarize` button callback; handle input validation and logic"""
    # is None when button is pressed without any file selected
    if uploaded_file is None:
        return

    response = post_pdf(uploaded_file, openai_gpt_model, content_type, user_query)
    if response.status_code != requests.codes.ok:
        # this will display the status code in the `Summary` UI
        set_summary_state(f"Requests error. Receive status code: {response.status_code}")
        return

    # parse FastAPI response as JSON and set streamlit state
    content = response.json()
    set_output_filename_state(uploaded_file.name)
    set_summary_state(content["summary"])


def app() -> None:
    """Streamlit entrypoint for PDF Summarize frontend"""
    st.set_page_config(
        page_title="PDF-Summarizer",
        page_icon="📝",
        layout="centered",
        menu_items={"Get help": None, "Report a bug": None},
    )
    st.title("PDF-Summarizer 📝")

    with st.sidebar:
        uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="hidden")
        form = st.form(key="user_input")
        model = form.selectbox(
            "OpenAI Model",
            options=(
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-0613",
                "gpt-3.5-turbo-16k",
                "gpt-3.5-turbo-16k-0613",
                "gpt-4",
                "gpt-4-0613",
                "gpt-4-32k",
                "gpt-4-32k-0613",
            ),
            help="[Learn more about models](https://platform.openai.com/docs/models)",
        )
        content_type = form.text_input("Content type", value="Scientifc article")
        prompt = form.text_input("Prompt", value="Can you ELI5 the paper?")

        form.form_submit_button(
            "Summarize",
            on_click=summarize_callback,
            args=(uploaded_file, model, content_type, prompt),
        )

        # is True only after a successful request
        if output_name := st.session_state.get("ouput_filename", None):
            summary = st.session_state.get("summary", None)
            st.download_button(
                "Download Summary", data=summary, file_name=output_name, use_container_width=True
            )

    # with col1:
    # could be a successful requests or status code
    if summary := st.session_state.get("summary", None):
        with st.expander("Summary", expanded=True):
            st.write(summary)

    if uploaded_file:
        pdf_display = pdf_to_base64(uploaded_file)
        st.markdown(pdf_display, unsafe_allow_html=True)


if __name__ == "__main__":
    # run as a script to test streamlit app locally
    app()
