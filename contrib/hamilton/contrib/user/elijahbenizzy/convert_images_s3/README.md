<!--
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
-->

# Purpose of this module
This module allows you to convert a variety of images in S3, placing them next to the originals.

It handles anything that [pillow](https://pillow.readthedocs.io/en/stable/) can handle.

# Configuration Options
This modules takes in no configuration options. It does take in the following parameters as inputs:
- `path_filter` -- a lambda function to take in a path and return `True` if you want to convert it and `False` otherwise. This defaults to checking if the path extension is `.png`.
- `prefix` -- a prefix inside the bucket to look for images.
- `bucket` -- the bucket to look for images in.
- `new_format` -- the format to convert the images to.
- `image_params` -- a dictionary of parameters to pass to the `Image.save` function. This defaults to `None`, which gets read as an empty dictionary.

# Limitations
Assumes:
1. The files are labeled by extension correctly
2. They are all in the same format
