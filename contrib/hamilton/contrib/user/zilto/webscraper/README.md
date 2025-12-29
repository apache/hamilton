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

This module implements a simple webscraper that collects the specified HTML tags and removes undesirable ones. Simply give it a list of URLs.

Timeout and retry logic for HTTP request is implemented using the `tenacity` package.

# Configuration Options
This module doesn't receive any configuration.

## Inputs
 - `urls` (Required): a list of valid url to scrape
 - `tags_to_extract`: a list of HTML tags to extract
 - `tags_to_remove`: a list of HTML tags to remove

## Overrides
 - `parsed_html`: if the function doesn't provide enough flexibility, another parser can be provided as long as it has parameters `url` and `html_page` and outputs a `ParsingResult` object.

# Limitations
- The timeout and retry values need to be edited via the decorator of `html_page()`.
