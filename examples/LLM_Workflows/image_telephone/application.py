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

"""
This module demonstrates a telephone application
using Burr that:
 - captions an image
 - creates caption embeddings (for analysis)
 - creates a new image based on the created caption
"""

import importlib
import logging
import os

import click
from burr.core import ApplicationBuilder, State, default, expr
from burr.core.action import action
from burr.tracking import client

from hamilton import dataflows, driver
from hamilton.io.materialization import to

# import hamilton modules
importlib.import_module("adapters")
caption_images = dataflows.import_module("caption_images", "elijahbenizzy")
generate_images = dataflows.import_module("generate_images", "elijahbenizzy")


logger = logging.getLogger(__name__)


@action(
    reads=["current_image_location", "descriptiveness"],
    writes=["current_image_caption", "image_location_history"],
)
def image_caption(state: State, caption_image_driver: driver.Driver) -> tuple[dict, State]:
    """Action to caption an image."""
    current_image = state["current_image_location"]
    result = caption_image_driver.execute(
        ["generated_caption"],
        inputs={"image_url": current_image, "descriptiveness": state["descriptiveness"]},
    )
    updates = {
        "current_image_caption": result["generated_caption"],
    }
    # You could save to S3 here
    return result, state.update(**updates).append(image_location_history=current_image)


@action(
    reads=[
        "current_image_caption",
        "storage_mode",
        "run_name",
        "storage_params",
        "image_caption_history",
    ],
    writes=["caption_analysis"],
)
def caption_embeddings(state: State, caption_image_driver: driver.Driver) -> tuple[dict, State]:
    """Action to analyze the caption by creating embeddings."""
    iteration = len(state["image_caption_history"])
    storage_mode = state["storage_mode"]
    storage_params = state["storage_params"]
    run_name = state["run_name"]
    metadata_save_path = os.path.join(run_name, f"metadata_{iteration}.json")
    if storage_mode == "s3":
        bucket = storage_params["bucket"]
        materializers = [
            to.json_s3(
                bucket=bucket,
                key=f"{run_name}/metadata_{iteration}.json",
                dependencies=["metadata"],
                id="save_metadata",
            ),
        ]
    elif storage_mode == "local":
        base_dir = storage_params["base_dir"]
        materializers = [
            to.json(
                path=os.path.join(base_dir, metadata_save_path),
                dependencies=["metadata"],
                id="save_metadata",
            ),
        ]
    else:
        raise ValueError(f"Storage mode {storage_mode} not supported.")
    _, result = caption_image_driver.materialize(
        *materializers,
        additional_vars=["metadata"],
        inputs={
            "image_url": state["current_image_location"],
        },
        overrides={"generated_caption": state["current_image_caption"]},
    )
    return result, state.append(caption_analysis=result["metadata"])


@action(
    reads=[
        "current_image_caption",
        "storage_mode",
        "storage_params",
        "image_caption_history",
        "run_name",
    ],
    writes=["current_image_location", "image_caption_history", "openai_image"],
)
def image_generation(state: State, generate_image_driver: driver.Driver) -> tuple[dict, State]:
    """Action to create an image."""
    storage_mode = state["storage_mode"]
    storage_params = state["storage_params"]
    iteration = len(state["image_caption_history"])
    run_name = state["run_name"]
    if storage_mode == "s3":
        bucket = storage_params["bucket"]
        materializers = [
            to.image_s3(
                bucket=bucket,
                key=f"{run_name}/image_{iteration}.png",
                dependencies=["generated_image"],
                id="save_image_png_s3",
                format="png",
            )
        ]
        saved_image_path = f"s3://{bucket}/{run_name}/image_{iteration}.png"
    elif storage_mode == "local":
        base_dir = storage_params["base_dir"]
        saved_image_path = os.path.join(base_dir, f"{run_name}/image_{iteration}.png")
        materializers = [
            to.image(
                path=saved_image_path,
                dependencies=["generated_image"],
                id="save_image_png",
                format="png",
            )
        ]
    else:
        raise ValueError(f"Storage mode {storage_mode} not supported.")

    current_caption = state["current_image_caption"]
    inputs = {"image_generation_prompt": current_caption}
    materializer_meta, result = generate_image_driver.materialize(
        *materializers, additional_vars=["generated_image"], inputs=inputs
    )

    updates = {
        "current_image_location": saved_image_path,
        "openai_image": result["generated_image"],
    }
    # You could save to S3 here
    return result, state.update(**updates).append(image_caption_history=current_caption)


@action(reads=["image_location_history", "image_caption_history", "caption_analysis"], writes=[])
def terminal_step(state: State) -> tuple[dict, State]:
    result = {
        "image_location_history": state["image_location_history"],
        "image_caption_history": state["image_caption_history"],
        "caption_analysis": state["caption_analysis"],
    }
    # Could save everything to S3 here.
    return result, state


def build_application(
    initial_state: dict,
    entry_point: str,
    number_of_images_to_caption: int = 4,
):
    """Builds the telephone application."""
    # instantiate hamilton drivers and then bind them to the actions.
    caption_image_driver = (
        driver.Builder()
        .with_config({"include_embeddings": True})
        .with_modules(caption_images)
        .build()
    )
    generate_image_driver = driver.Builder().with_config({}).with_modules(generate_images).build()
    app = (
        ApplicationBuilder()
        .with_state(**initial_state)
        .with_actions(
            caption=image_caption.bind(caption_image_driver=caption_image_driver),
            analysis=caption_embeddings.bind(caption_image_driver=caption_image_driver),
            generate=image_generation.bind(generate_image_driver=generate_image_driver),
            terminal=terminal_step,
        )
        .with_transitions(
            ("caption", "analysis", default),
            (
                "analysis",
                "terminal",
                expr(f"len(image_caption_history) == {number_of_images_to_caption}"),
            ),
            ("analysis", "generate", default),
            ("generate", "caption", default),
        )
        .with_entrypoint(entry_point)
        .with_tracker(project="dagworks-image-telephone")
        .with_identifiers(app_id=initial_state["run_name"])
        .build()
    )
    return app


@click.command()
@click.option(
    "-r",
    "--run-name",
    required=True,
    help="Name of this run. Must be globally unique.",
    type=str,
)
@click.option(
    "-n",
    "--num-iterations",
    required=False,
    help="Number of iterations to run",
    type=int,
    default=150,
)
@click.option(
    "-i",
    "--image",
    required=True,
    help="Image to start with",
    type=str,
)
@click.option(
    "-m",
    "--mode",
    required=True,
    help="Mode to use, either 's3' or 'local'",
    type=click.Choice(["s3", "local"]),
)
@click.option(
    "-b",
    "--bucket-or-base",
    required=False,
    help="S3 bucket to use use if mode=='s3'; else base directory to us if mode=='local'",
    type=str,
    default=None,
)
@click.option(
    "-d",
    "--descriptiveness",
    required=False,
    help="Descriptiveness of the image. Adverb to describe how descriptive it is. E.G. "
    "'quite', 'somewhat', 'not particularly'",
    type=str,
    default=None,
)
def run(
    run_name: str,
    image: str,
    mode: str,
    bucket_or_base: str,
    num_iterations: int,
    descriptiveness: str,
):
    logger.info(f"Running image telephone for {run_name}")
    if mode == "local":
        assert bucket_or_base is not None, "Must provide base_dir if mode is local"
    if mode == "s3":
        assert bucket_or_base is not None, "Must provide bucket if mode is s3"
    storage_params = {"bucket": bucket_or_base} if mode == "s3" else {"base_dir": bucket_or_base}
    if mode == "local" and not os.path.exists(image_path := os.path.join(bucket_or_base, run_name)):
        os.makedirs(image_path)

    try:
        state, entry_point = client.LocalTrackingClient.load_state(
            "dagworks-image-telephone",
            run_name,
        )
        logger.info(f"Found existing state for {run_name} to start from.")
        initial_state = state.get_all()
    except ValueError:
        logger.info(f"No state found, starting from scratch for {run_name}")
        initial_state = {
            "current_image_location": image,
            "current_image_caption": "",
            "image_location_history": [],
            "image_caption_history": [],
            "caption_analysis": [],
            "storage_mode": mode,
            "storage_params": storage_params,
            "run_name": run_name,
            "descriptiveness": descriptiveness,
        }
        entry_point = "caption"

    app = build_application(
        initial_state,
        entry_point=entry_point,
        number_of_images_to_caption=num_iterations,
    )
    app.visualize(output_file_path="statemachine", include_conditions=True, view=True, format="png")

    # run until the end:
    # last_action, result, state = app.run(halt_after=["terminal"])
    # or execute one step at a time:
    while True:
        _action, _result, _state = app.step()
        print("action=====\n", _action)
        print("result=====\n", _result)
        # you could save to S3 / download images etc. here.
        if _action.name == "terminal":
            break

    logger.info(f"Finished {num_iterations} iterations of image telephone for {run_name}.")


if __name__ == "__main__":
    run()
    # app = build_application({}, "caption", 4)
    # app.visualize(output_file_path="statemachine", include_conditions=True, view=True, format="png")
