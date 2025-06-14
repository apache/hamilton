import collections
import concurrent
import json
import os
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import altair as alt
import boto3
import numpy as np
import pandas as pd
import streamlit as st

# much faster implementation -- this makes it work on streamlit with limited resources
from openTSNE import TSNE
from PIL import Image
from streamlit.components.v1 import html
from streamlit_super_slider import st_slider

BUCKET = "dagworks-image-telephone"


def info_sidebar():
    """Basic information sidebar for navigation/documentation"""
    with st.sidebar:
        st.markdown(
            "# Getting Started 🚦 \n"
            "This application lets you explore what happens when GPT-4 plays the telephone game with Dall-E-3.\n\n"
            "We start by asking GPT-4 to create a caption for an input picture. "
            "Then, we generates an image from the caption. Rinse-and-repeat ♻\n\n"
            "This app shows the result of many such iterations. Select a seed image on the dropdown to view! "
            "Note that this app does *not* run everything live -- this would be slow and expensive. Instead, we've ran it on a selection of images. "
            "Note that occasionally the chart breaks -- feel free to refresh the page to fix it.\n\n"
        )
        st.markdown(
            "#  Exploring 🚀\n"
            "Once you've selected an image, you'll see a few options. Click on 'caption' to expand. Adjust the slider to move through "
            "the iteration history."
            "The embeddings plot is the result of projecting the caption embeddings into 2-dimensional space using "
            "[TSNE](https://en.wikipedia.org/wiki/T-distributed_stochastic_neighbor_embedding). The dimensions (in all likelihood) mean nothing."
            "\n\n"
        )
        st.markdown(
            "# Brought to you by [Hamilton](https://github.com/apache/hamilton) ✨\n"
            "You can see the code + DAGs used to generate the data in the `Build` tab."
            "The dataflow to prompt GPT-4 and create images was built using the [Hamilton]"
            "(https://github.com/apache/hamilton) library.\n\n"
            "Generate your own images by pulling the dataflow from the "
            "[Hamilton Dataflow Hub](https://hub.dagworks.io/docs/Users/elijahbenizzy/caption_images/) and specify your ["
            "OpenAI API key](https://platform.openai.com/overview) to get started!"
        )

        st.markdown(
            "### ⭐ Please leave a star on [GitHub](https://github.com/apache/hamilton)\n"
            "### 🤓 Join our [Slack](https://hamilton-opensource.slack.com/join/shared_invite/zt-1bjs72asx-wcUTgH7q7QX1igiQ5bbdcg#/shared-invite/email) channel if you have any question!"
        )


def download_s3_file(s3_client, bucket_name, file_key, _transform=lambda x: x):
    """
    Function to download a file from S3 and return its content.
    """
    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    file_content = response["Body"].read()
    file_content = _transform(file_content)
    return file_key, file_content


@st.cache_data(ttl=100)
def query_data(bucket: str, paths: Tuple[str, ...], _s3_client, _transform) -> Any:
    """Function to query metadata from the s3 bucket"""
    file_contents = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Start the load operations and mark each future with its file key
        future_to_file = [
            executor.submit(download_s3_file, _s3_client, bucket, file, _transform)
            for file in paths
        ]
        for future in concurrent.futures.as_completed(future_to_file):
            data = future.result()
            file_contents[data[0]] = data[1]
    return [file_contents[p] for p in paths]


def get_url(key: str) -> str:
    """Link to our CDN, given an S3 key"""
    return f"https://d1lf8m1wnxcl0a.cloudfront.net/{key}"


def list_prompts_and_images(prompt: str, paths: Tuple[str, ...]) -> tuple[list[str], list[str]]:
    """Lists out prompts and images paths, given an image name (prompt)"""
    prompt_entries = [p for p in paths if p.endswith(".json")]
    image_entries = [p for p in paths if p.endswith(".jpeg") & ("original" not in p.split("/")[-1])]
    sorting_key = lambda i: int(str(i).split("/")[-1].split("_")[-1].split(".")[0])  # noqa E731
    sorted_prompt_entries = sorted(prompt_entries, key=sorting_key)
    sorted_image_entries = [prompt + "/original.jpeg"] + sorted(image_entries, key=sorting_key)
    sorted_image_entries = [get_url(key) for key in sorted_image_entries]
    return sorted_prompt_entries, sorted_image_entries


@st.cache_data(ttl=None)
def tsne(_prompt_entries, max_iteration: int, name: str):
    """Performs basic clustering on the embeddings to represent in 2d space.
    Note this takes in max_iteration + name purely for caching -- caching _prompt_entries is unstable.
    Once the max_iteration is reached, that means we've expanded it out."""
    embeddings = [item["caption_embeddings"] for item in _prompt_entries]
    tsne = TSNE(
        n_components=2,
        perplexity=min(max(0, len(_prompt_entries) - 1), 15),
        random_state=500,
        learning_rate=200,
        initialization="random",
    )
    return tsne.fit(np.array(embeddings))


def embedding_path_plot(vis_dims, image_list, highlight_idx, image_name):
    custom_css = """
    <style>
        /* Custom styles for tooltips with a specific ID */
        #vg-tooltip-element img {
            width: 200px; /* Adjust width as needed */
            height: auto; /* Maintain aspect ratio */
        }
        #vg-tooltip-element {
            transition: opacity 0.5s ease-out; /* Adjust time as needed */
            opacity: 1; /* Fully visible by default */
        }

        /* Styles to apply when the tooltip is about to be hidden */
        #vg-tooltip-element[aria-hidden='true'] {
            opacity: 0; /* Fully transparent */
        }
    </style>
    """

    # Inject custom CSS
    st.markdown(custom_css, unsafe_allow_html=True)

    # Create a DataFrame from the numpy array for easier manipulation
    df = pd.DataFrame(vis_dims, columns=["x", "y"]).copy()
    df["idx"] = range(vis_dims.shape[0])
    df["image"] = image_list

    # Create a color scale
    df["color"] = df["idx"] / df["idx"].max()
    # Quick hack to get the base URL
    session = st.runtime.get_instance()._session_mgr.list_active_sessions()[0]
    st_base_url = urllib.parse.urlunparse(
        [session.client.request.protocol, session.client.request.host, "", "", "", ""]
    )

    # Display the chart with custom tooltip
    scatter_plot = (
        alt.Chart(df)
        .transform_calculate(
            url=f"'{st_base_url}?seed_image={image_name}&iteration=' + {alt.datum.idx}"
        )
        .mark_circle(size=60)
        .encode(
            x="x",
            y="y",
            color=alt.Color("color", scale=alt.Scale(scheme="redblue"), legend=None),
            tooltip=["image"],
            href="url:N",
        )
    )

    df_line = pd.concat(
        [df[:-1].reset_index(drop=True), df[1:].reset_index(drop=True)], axis=1
    ).copy()
    df_line.columns = [
        "x1",
        "y1",
        "idx1",
        "image1",
        "color1",
        "x2",
        "y2",
        "idx2",
        "image2",
        "color2",
    ]
    line_plot = (
        alt.Chart(df_line)
        .mark_line(tooltip=None)
        .encode(
            x="x1",
            y="y1",
            x2="x2",
            y2="y2",
            color=alt.Color("color1", scale=alt.Scale(scheme="redblue"), legend=None),
        )
    )

    # Convert highlight_idx to a list if it's not already
    if not isinstance(highlight_idx, list):
        highlight_idx = [highlight_idx]

    # Highlight specific points
    highlight = (
        alt.Chart(df[df["idx"].isin(highlight_idx)])
        .mark_circle(size=250, color="black")
        .encode(x="x", y="y", tooltip=["image"])
    )

    # Combine all plots
    final_chart = scatter_plot + line_plot + highlight

    altair_chart = final_chart.configure_axis(
        grid=False, labelFontSize=0, title=None
    ).configure_view(strokeWidth=0)
    st.altair_chart(altair_chart, use_container_width=True, theme="streamlit")


def prompt_dropdown(items: List[str], incomplete_items) -> str:
    """Selects the seed image (prompt) -- also updates the URL state"""
    query_params = st.experimental_get_query_params()
    key = "seed_image"
    # start it initially
    if key in query_params:
        selected_item = query_params[key][0]
        if key not in st.session_state:
            st.session_state[key] = selected_item
    else:
        selected_item = items[0]
    # selected_item = query_params.get(key, [items[0]])[0]  # Default to first item
    selected = st.selectbox(
        "Select Initial Image (* means incomplete)",
        items,
        label_visibility="collapsed",
        key=key,
        format_func=lambda x: f"*{x}" if x in incomplete_items else x,
    )
    if selected != st.session_state.get(key):
        st.session_state[key] = selected
    if selected != selected_item:
        new_params = query_params.copy()
        new_params.update({key: selected})
        st.experimental_set_query_params(**new_params)

    return selected


def entry_slider(prompt_files):
    """Slider to tell which iteration we're on/change it. Note this has a lot of complex
    stuff to syncrhonize with the URL state"""
    slider_key = "iteration"

    query_params = st.experimental_get_query_params()

    # Check if the slider value is already in the session state
    if slider_key not in st.session_state:
        # Initialize slider value from URL parameter or default to 0
        default_value = 0
        if slider_key in query_params:
            try:
                # Convert URL parameter to an integer and ensure it's within range
                default_value = int(query_params[slider_key][0])
                default_value = max(0, min(default_value, len(prompt_files) - 1))
            except ValueError:
                default_value = 0

        # Set the initial value in session state
        st.session_state[slider_key] = default_value

    # Create the slider using the value from session state
    selected_entry = st_slider(
        0,
        len(prompt_files) - 1,
        default_value=st.session_state[slider_key],
        key=slider_key,
    )

    # Update the session state and URL parameter when the slider moves
    if selected_entry != st.session_state[slider_key]:
        st.session_state[slider_key] = selected_entry
    if selected_entry != int(query_params.get(slider_key, [0])[0]):
        new_params = query_params.copy()
        new_params.update({slider_key: selected_entry})
        st.experimental_set_query_params(**new_params)

    return selected_entry


def create_gif(prompt, sorted_image_entries, size: int = 200, ms_duration: int = 300):
    """Unused (but hopefully soon used) function to create a GIF from the images."""
    if st.button("Create GIF"):
        images = []
        for png_file in sorted_image_entries:
            img = Image.open(png_file)
            images.append(img.resize((size, size)))

        images[0].save(
            "./rabbit_hole.gif",
            save_all=True,
            append_images=images[1:],
            duration=ms_duration,
            loop=0,
        )

        st.session_state["gif_prompt"] = prompt


def gif_container(prompt_path: Path, image_entries: list[str]):
    """Unused (but hopefully soon used) function to contain the GIF that we generated"""
    inner_left, inner_right = st.columns(2)
    with inner_left:
        img_size: int = st.number_input("Image size", value=200, min_value=100, max_value=2000)
    with inner_right:
        frame_duration: int = st.number_input(
            "GIF frame duration", value=300, min_value=100, help="Duration in ms"
        )
    with inner_left:
        create_gif(str(prompt_path), image_entries, img_size, frame_duration)
    with inner_right:
        if st.session_state.get("gif_prompt") == str(prompt_path):
            with open("./rabbit_hole.gif", "rb") as f:
                st.download_button("Download GIF", data=f)

    if st.session_state.get("gif_prompt") == str(prompt_path):
        st.image("./rabbit_hole.gif", width=img_size)


def gallery(sorted_image_entries, n_cols=3):
    """Displays a gallery of the images, in order"""
    quotient, _ = divmod(len(sorted_image_entries), n_cols)
    n_rows = quotient + 1
    n_entries = len(sorted_image_entries)

    # Display the images in a grid
    for i in range(n_rows):
        row = st.columns(n_cols)
        for j in range(n_cols):
            idx = i * n_cols + j
            if idx >= n_entries:
                break
            with row[j]:
                st.image(sorted_image_entries[idx], caption=f"{idx}")


@st.cache_resource
def s3():
    """Returns a boto3 client for S3"""
    return boto3.client("s3")


@st.cache_data(ttl=100)  # every 20 seconds we'll update?
def list_files_in_bucket(_s3_client, bucket) -> Dict[str, tuple[str, ...]]:
    """Gets name of all files in the s3 bucket grouped by the prefix (first directory)."""
    paginator = _s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket)
    out = collections.defaultdict(list)
    for page in pages:
        for obj in page["Contents"]:
            out[obj["Key"].split("/")[0]].append(obj["Key"])
    out = {k: tuple(v) for k, v in out.items()}
    return out


def parse_date_from_prompt_path(prompt_path: str):
    """Parses the date from the prompt path"""
    try:
        return datetime.strptime(prompt_path.split("_")[-1], "%Y%m%d")
    except ValueError:
        return None


def explore_display():
    """Section for the explore tab"""
    # Use the s3 connection for loading individual files as its a little cleaner and streamlit supported
    s3_client = s3()

    all_files_by_header = list_files_in_bucket(s3_client, BUCKET)
    prompt_dropdowns_in_order = sorted(
        all_files_by_header.keys(), reverse=True, key=lambda x: parse_date_from_prompt_path(x)
    )
    incomplete_items = [
        item
        for item in prompt_dropdowns_in_order
        if len(all_files_by_header[item]) < 300  # 100 iterations
    ]
    prompt_path: str = prompt_dropdown(prompt_dropdowns_in_order, incomplete_items)
    prompt_data, image_urls = list_prompts_and_images(
        prompt_path, all_files_by_header.get(prompt_path, ())
    )
    all_prompt_data = query_data(
        BUCKET, prompt_data, s3_client, _transform=lambda x: json.loads(str(x, "utf-8"))
    )
    all_prompt_data.sort(key=lambda item: item["iteration"])
    max_iter = max([item["iteration"] for item in all_prompt_data])
    projection = tsne(all_prompt_data, max_iter, prompt_path)

    left, right = st.columns(2)
    # TODO -- ensure we're not off by one with the images...
    with left:
        selected_entry = entry_slider(all_prompt_data)

        # plot
        image_urls_to_display = image_urls[0 : len(projection)]
        if len(image_urls_to_display) != len(projection):
            image_url_length = len(image_urls_to_display)
            image_urls_to_display.append(image_urls[image_url_length - 1])
        embedding_path_plot(projection, image_urls_to_display, selected_entry, prompt_path)
        # highlight_point(projection, selected_entry)

        # TODO -- get gifs working
        # gif widget
        # gif_container(prompt_path, image_urls)

    with right:
        st.image(image=str(image_urls[selected_entry]))
        with st.expander("Caption"):
            st.write(all_prompt_data[selected_entry]["generated_caption"])

    with st.expander("Gallery", expanded=True):
        gallery(image_urls, n_cols=4)


@st.cache_data()
def load_resources() -> Tuple[str, str, str, str]:
    """Returns the code for the dataflow and the code for the adapter"""
    # TODO -- get this to work when we have hamilton contrib
    is_local_mode = os.environ.get("LOCAL_MODE", "false").lower() == "true"
    if is_local_mode:
        caption_base_path = "../../../contrib/hamilton/contrib/user/elijahbenizzy/caption_images"
        generate_base_path = "../../../contrib/hamilton/contrib/user/elijahbenizzy/generate_images"
    else:
        caption_base_path = "contrib/hamilton/contrib/user/elijahbenizzy/caption_images"
        generate_base_path = "contrib/hamilton/contrib/user/elijahbenizzy/generate_images"
    caption = open(f"{caption_base_path}/__init__.py").read()
    generate_images = open(f"{generate_base_path}/__init__.py").read()
    dag_img_caption = f"{caption_base_path}/dag.png"
    dag_img_generate = f"{generate_base_path}/dag.png"

    def remove_after_mainline(s):
        return s.split("if __name__ == ")[0]

    return (
        remove_after_mainline(caption),
        remove_after_mainline(generate_images),
        dag_img_caption,
        dag_img_generate,
    )


def build_display():
    """Section for the build tab"""
    caption_images, generate_images, caption_dag, generate_dag = load_resources()
    st.markdown(
        "# Using [Hamilton](https://github.com/apache/hamilton) to build pipelines \n"
        "The code to generate the data for this app is built using Hamilton, a declarative framework"
        "for building clean, self-documenting, and extensible data pipelines. The basics of this is simple -- "
        "we have two modules, one for captioning images and one for generating images from captions. Each one "
        "represents a [DAG](https://en.wikipedia.org/wiki/Directed_acyclic_graph) of functions, "
        "and allows a variety of inputs. We then call them together in a while loop, tracking state, and saving the results "
        "to a public S3 bucket, which is served by a cloudfront CDN. \n"
        "These modules are published to the [hamilton hub](hub.dagworks.io), which allows you to share and reuse other people's pipelines. "
        "We've drawn the DAGs below. \n\n"
        "Our broader vision is two-fold:\n"
        "1. That everyone will build their data pipelines in a well-structured, composable, and self-documenting manner (such as Hamilton).\n"
        "2. That people get more productive by reusing other people's pipelines, with a bustling community around it!\n"
        "We're still early in our journey and would love you to be part of it! See our [github repo](https://github.com/apache/hamilton) to get started."
    )
    tab_1, tab_2, tab_3 = st.tabs(
        ["Captioning module", "Image generation module", "The loop"],
    )
    with tab_1:
        st.markdown(
            "## Generating captions from images\n"
            "This dataflow generates a caption from an image, "
            "and captures embeddings for this caption. "
            "These embeddings allow us to generate the TSNE plot. You can read"
            " more about it [here](https://hub.dagworks.io/docs/Users/elijahbenizzy/generate_images/)"
        )
        with st.expander("dag", expanded=True):
            st.image(caption_dag)
        with st.expander("code", expanded=False):
            st.code(caption_images)
    with tab_2:
        st.markdown(
            "## Generating images from captions\n"
            "This dataflow is simple -- it just generates an image from a caption. "
            "It does a little bit of prompt manipulation, then queries "
            "out to a (specifiable) image model (default DALL-E-3). You can read "
            "more about it [here](https://hub.dagworks.io/docs/Users/elijahbenizzy/generate_images/)."
        )
        with st.expander("dag", expanded=True):
            st.image(generate_dag)
        with st.expander("code", expanded=False):
            st.code(generate_images)
    with tab_3:
        st.markdown(
            "## Running them together\n"
            "While we've represented the logic above as individual components, "
            "we need to do a few more things to generate the data you just looked at:\n"
            "1. Create a Burr application that orchestrates calling them\n"
            "2. Add in some persistence.\n"
            "The following shows some simplified code doing (1). For (2) see full example in the [Hamilton repo](https://github.com/apache/hamilton/tree/main/examples/LLM_Workflows/image_telephone)."
        )
        code = '''@action(
    reads=["current_image_location"],
    writes=["current_image_caption", "image_location_history"],
)
def image_caption(state: State, caption_image_driver: driver.Driver) -> tuple[dict, State]:
    """Action to caption an image."""
    current_image = state["current_image_location"]
    result = caption_image_driver.execute(
        ["generated_caption"], inputs={"image_url": current_image}
    )
    updates = {
        "current_image_caption": result["generated_caption"],
    }
    return result, state.update(**updates).append(image_location_history=current_image)

@action(
    reads=["current_image_caption"],
    writes=["caption_analysis"],
)
def caption_embeddings(state: State, caption_image_driver: driver.Driver) -> tuple[dict, State]:
    """Action to caption embeddings for analysis"""
    result = caption_image_driver.execute(
        ["metadata"],
        overrides={"generated_caption": state["current_image_caption"]}
    )
    return result, state.append(caption_analysis=result["metadata"])


@action(
    reads=["current_image_caption"],
    writes=["current_image_location", "image_caption_history"],
)
def image_generation(state: State, generate_image_driver: driver.Driver) -> tuple[dict, State]:
    """Action to create an image."""
    current_caption = state["current_image_caption"]
    result = generate_image_driver.execute(
        ["generated_image"], inputs={"image_generation_prompt": current_caption}
    )
    updates = {
        "current_image_location": result["generated_image"],
    }
    return result, state.update(**updates).append(image_caption_history=current_caption)


@action(
    reads=["image_location_history", "image_caption_history", "caption_analysis"],
    writes=[]
)
def terminal_step(state: State) -> tuple[dict, State]:
    result = {"image_location_history": state["image_location_history"],
              "image_caption_history": state["image_caption_history"],
              "caption_analysis": state["caption_analysis"]}
    return result, state

caption_image_driver = (
        driver.Builder().with_config({}).with_modules(caption_images).build()
    )
generate_image_driver = (
    driver.Builder().with_config({}).with_modules(generate_images).build()
)
app = (
    ApplicationBuilder()
    .with_state(
        current_image_location=starting_image,
        current_image_caption="",
        image_location_history=[],
        image_caption_history=[],
        caption_analysis=[],
    )
    .with_actions(
        caption=image_caption.bind(caption_image_driver=caption_image_driver),
        caption_embeddings=caption_embeddings.bind(caption_image_driver=generate_image_driver),
        image=image_generation.bind(generate_image_driver=generate_image_driver),
        terminal=terminal_step,
    )
    .with_transitions(
        ("caption", "caption_embeddings", default),
        ("caption_embeddings", "image", default),
        ("image", "terminal", expr(f"len(image_caption_history) == {number_of_images_to_caption}")),
        ("image", "caption", default),
    )
    .with_entrypoint("caption")
    .with_hooks(ImageSaverHook())
    .with_tracker(project="image-telephone")
    .build()
)
# run until the end:
last_action, result, state = app.run(halt_after=["terminal"])
# save / download images etc. here from the result/state.
'''
        st.code(code)


def posthog_telemetry():
    """Adds posthog telemetry so we can see general usage stats.
    TBD whether it actually gets executed in the head prior to execution, but it appears to work...
    """
    head_js = """
        !function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.async=!0,p.src=s.api_host+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="capture identify alias people.set people.set_once set_config register register_once unregister opt_out_capturing has_opted_out_capturing opt_in_capturing reset isFeatureEnabled onFeatureFlags getFeatureFlag getFeatureFlagPayload reloadFeatureFlags group updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures getActiveMatchingSurveys getSurveys onSessionId".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);
       posthog.init('phc_nH4OuoEjRwzhEKhWStd9PDRPELceYUsm95ZwmFqWSNR',{api_host:'https://app.posthog.com'})
       """

    # HTML to inject the script into the head
    inject_js = f"""
       <script>
       var head = document.head;
       var script = document.createElement('script');
       script.type = 'text/javascript';
       script.innerHTML = `{head_js}`;
       head.appendChild(script);
       </script>
       """

    # Use Streamlit's HTML component to inject your JavaScript
    html(inject_js, height=0)


def app():
    """Main app"""
    st.set_page_config(
        page_title="Image Telephone",
        page_icon="☎️",
        layout="wide",
        menu_items={"Get help": None, "Report a bug": None},
    )
    posthog_telemetry()
    # Your JavaScript code
    st.title("Image Telephone ☎️")
    info_sidebar()
    tab_1, tab_2 = st.tabs(
        ["Explore", "Build"],
    )
    css = """
    <style>
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size:1.4rem;
        }
    </style>
    """

    html(css)
    with tab_2:
        build_display()
    with tab_1:
        explore_display()


if __name__ == "__main__":
    app()
