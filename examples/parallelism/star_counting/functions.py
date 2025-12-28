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

from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd
import requests

from hamilton.function_modifiers import save_to, value
from hamilton.htypes import Collect, Parallelizable


def starcount_url(repositories: List[str]) -> Parallelizable[str]:
    """Generates API URLs for counting stars on a repo. We do this
    so we can paginate requests later.


    :param repo: The repository name in the format 'organization/repo'
    :return: A URL to the GitHub API
    """
    for repo in repositories:
        yield f"https://api.github.com/repos/{repo}"


def star_count(starcount_url: str, github_api_key: str) -> Tuple[str, int]:
    """Generates the star count for a given repo.

    :param starcount_url: URL of the repo
    :param github_api_key: API key for GitHub
    :return:  A tuple of the repo name and the star count
    """
    response = requests.get(starcount_url, headers={"Authorization": f"token {github_api_key}"})
    response.raise_for_status()  # Raise an exception for unsuccessful requests

    data = response.json()

    return data["full_name"], data["stargazers_count"]


def stars_by_repo(star_count: Collect[Tuple[str, int]]) -> Dict[str, int]:
    """Aggregates the star count for each repo into a dictionary, so we
    can generate paginated requests.

    :param star_count:  A tuple of the repo name and the star count
    :return: The star count for each repo
    """
    star_count_dict = {}
    for repo_name, stars in star_count:
        star_count_dict[repo_name] = stars
    return star_count_dict


def stargazer_url(stars_by_repo: Dict[str, int], per_page: int = 100) -> Parallelizable[str]:
    """Generates query objects for each repository, with the correct pagination and offset.

    :param stars_by_repo: The star count for each repo
    :param per_page: The number of results per page
    :return: A query object for each repo, formatted as a generator.
    """
    for repo_name, stars in stars_by_repo.items():
        num_pages = (
            stars + per_page - 1
        ) // per_page  # Calculate the number of pages needed for pagination
        for page in range(num_pages):
            yield f"https://api.github.com/repos/{repo_name}/stargazers?page={page + 1}&per_page={per_page}"


def stargazers(stargazer_url: str, github_api_key: str) -> pd.DataFrame:
    """Gives the GitHub username of all stargazers in this query
    by hitting the GitHub API.

    :param stargazer_query: Query object to represent the query
    :param github_api_key: API key for GitHub
    :return: A set of all stargazers
    """
    headers = {
        "Authorization": f"token {github_api_key}",
        "Accept": "application/vnd.github.v3.star+json",
    }

    response = requests.get(stargazer_url, headers=headers)
    response.raise_for_status()  # Raise an exception for unsuccessful requests

    data = response.json()
    records = [
        {
            "user": datum["user"]["login"],
            "starred_at": datetime.strptime(datum["starred_at"], "%Y-%m-%dT%H:%M:%SZ"),
        }
        for datum in data
    ]
    return pd.DataFrame.from_records(records)


@save_to.csv(path=value("unique_stargazers.csv"))
def unique_stargazers(stargazers: Collect[pd.DataFrame]) -> pd.DataFrame:
    """Aggregates all stargazers into a single set.

    :param stargazers: Set of stargazers, paginated
    :return: A set of all stargazers
    """
    df = pd.concat(stargazers)
    unique = df.sort_values("starred_at").groupby("user").first()
    return unique


def final_count(unique_stargazers: pd.DataFrame) -> int:
    """Counts the number of unique stargazers.

    :param unique_stargazers: Set of all stargazers
    :return: The number of unique stargazers
    """
    return len(unique_stargazers)
