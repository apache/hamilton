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
📜 DAGWorks Blog Archive Updater Script

This script fetches articles from the DAGWorks blog archive and updates the README with the latest posts.
It supports filtering articles based on a cutoff date and offers an option to print articles to the console for review.

Before running this script, make sure to install the required packages by running:
pip install -r update_blogs_requirements.txt

Usage:
    1. Specify a cutoff date and update the README:
        python update_blogs_in_learning_resources.py --date 2024-10-01

    2. Print articles to the console (without updating README):
        python update_blogs_in_learning_resources.py --date 2024-10-01 --print

    3. Run interactively (no arguments required):
        python update_blogs_in_learning_resources.py

Arguments:
    --date YYYY-MM-DD : Optional. Fetches articles published on or after the given date.
    --print           : Optional. Prints fetched articles to the console without modifying the README.

Dependencies:
    - selenium: For web scraping.
    - webdriver-manager: Manages ChromeDriver installation.
    - beautifulsoup4: Parses HTML content.
    - prompt_toolkit: Enables interactive user input from the command line.

Notes:
    - Ensure Google Chrome is installed since the script uses it for scraping.
    - The README file must be present in the same directory as this script.
"""

import argparse
import time
from datetime import datetime

from bs4 import BeautifulSoup
from prompt_toolkit import HTML, prompt
from prompt_toolkit.styles import Style
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def fetch_articles(url, cutoff_date):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )

    driver.get(url)

    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    anchors = soup.find_all("a", class_="_color-pub-primary-text_q8zsn_187")
    timeEls = soup.find_all("time", class_="_date_1v6nm_1")

    # hardcoded blog links
    articles = [
        (
            "https://pyright.blogspot.com/2024/07/dag-hamilton-workflow-for-toy-text.html",
            "DAG Hamilton Workflow for Toy Text Processing Script",
            None,
        ),
        (
            "https://vyom-modi.medium.com/building-a-high-performance-rag-based-ai-with-qdrant-groq-langchain-and-dagworks-hamilton-fb1baa7415bc",
            "Building a High-Performance RAG-Based AI with Qdrant, Groq, LangChain, and DAGWorks Hamilton",
            None,
        ),
        (
            "https://blog.getwren.ai/how-do-we-rewrite-wren-ai-llm-service-to-support-1500-concurrent-users-online-9ba5c121afc3",
            "How do we rewrite Wren AI LLM Service to support 1500 concurrent users online",
            None,
        ),
    ]
    for _i, (anchor, time_el) in enumerate(zip(anchors, timeEls)):
        link = anchor["href"]
        text = anchor.get_text()

        date_str = time_el["datetime"]
        article_date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
        if article_date >= cutoff_date:
            articles.append((link, text, article_date))

    return articles


def get_cutoff_date():
    style = Style.from_dict({"prompt": "bold", "faded": "ansiblack italic"})

    date_str = prompt(
        HTML("<prompt>Enter cutoff date (YYYY-MM-DD): </prompt>"),
        default=f"{datetime.now().year}-01-01",
        style=style,
    )

    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
        return get_cutoff_date()


def print_articles(articles):
    """Prints articles to the console."""
    print("\n📰 Articles:\n")
    for link, text, date in articles:
        if date:
            print(f"* {date} - {text}: {link}")
        else:
            print(f"* {text}: {link}")


def update_readme(articles):
    external_blogs_header = "## 📰 External Blogs\n"
    external_blogs_link = (
        "For the latest blog posts, see the [DAGWorks's Blog](https://blog.dagworks.io/).\n\n"
    )
    blog_entries = []

    for link, text, date in articles:
        if date:
            blog_entries.append(f"* {date} &nbsp;&nbsp; [{text}]({link})")
        else:
            blog_entries.append(f"* [{text}]({link})")

    new_external_blogs_section = (
        external_blogs_header + external_blogs_link + "\n".join(blog_entries) + "\n"
    )

    with open("readme.md", "r") as file:
        content = file.readlines()

    new_content = []
    in_external_blogs_section = False

    for line in content:
        if line.startswith("## 📰 External Blogs"):
            in_external_blogs_section = True
            new_content.append(new_external_blogs_section)
        elif in_external_blogs_section and line.startswith("##"):
            in_external_blogs_section = False

        if not in_external_blogs_section:
            new_content.append(line)
    with open("readme.md", "w") as file:
        file.writelines(new_content)


def main():
    url = "https://blog.dagworks.io/archive"

    parser = argparse.ArgumentParser(
        description="📜 Fetch and update articles from the DAGWorks blog archive.",
        epilog="""
    ✨ Tip:
    - Use --date to specify a cutoff date to filter articles (default: prompt input).
    - Use --print to display fetched articles directly in the console.

    Examples:
    1. Fetch articles after a specific date and update README:
        python update_blogs_in_learning_resources.py --date 2024-10-01

    2. Print articles to the console without modifying the README:
        python update_blogs_in_learning_resources.py --date 2024-10-01 --print

    3. Run interactively (without --date) and choose a date via prompt:
        python update_blogs_in_learning_resources.py
        """,
        formatter_class=argparse.RawTextHelpFormatter,  # Preserve newlines and formatting
    )

    parser.add_argument(
        "--date",
        type=str,
        metavar="YYYY-MM-DD",
        help=(
            "Cutoff date to filter articles (e.g., 2024-10-01). "
            "If not provided, you will be prompted to enter a date during execution."
        ),
    )

    parser.add_argument(
        "--print",
        action="store_true",
        help=(
            "Print the fetched articles to the console instead of updating the README. "
            "Useful for reviewing articles before making changes."
        ),
    )

    args = parser.parse_args()

    cutoff_date = (
        datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else get_cutoff_date()
    )

    print(f"\n🔍 Fetching articles published after {cutoff_date}...\n")
    articles = fetch_articles(url, cutoff_date)

    if args.print:
        print_articles(articles)
    else:
        update_readme(articles)

    print(f"\n✅ Total Articles Fetched: {len(articles)}")


if __name__ == "__main__":
    main()
