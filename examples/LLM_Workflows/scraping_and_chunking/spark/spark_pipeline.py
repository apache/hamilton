"""
This module creates a spark job that
uses the sitemap.xml file to create a dataframe with a URL column,
that we then process using a Hamilton module to create a dataframe with
columns for the article text and the chunked text.
"""

import re

import doc_pipeline
import pyspark.sql as ps
import requests

from hamilton.plugins import h_spark


def spark_session(app_name: str) -> ps.SparkSession:
    return ps.SparkSession.builder.appName(app_name).getOrCreate()


def sitemap_text(sitemap_url: str = "https://hamilton.apache.org/sitemap.xml") -> str:
    """Takes in a sitemap URL and returns the sitemap.xml file.

    :param sitemap_url: the URL of sitemap.xml file
    :return:
    """
    try:
        sitemap = requests.get(sitemap_url)
    except Exception as e:
        raise RuntimeError(
            f"Failed to fetch sitemap from {sitemap_url}. Original error: {str(e)}"
        ) from e
    return sitemap.text


def urls_from_sitemap(
    sitemap_text: str, spark_session: ps.SparkSession, num_partitions: int = 4
) -> ps.DataFrame:
    """Takes in a sitemap.xml file contents and creates a df of all the URLs in the file.

    :param sitemap_text: the contents of a sitemap.xml file
    :return: df of URLs
    """
    urls = re.findall(r"<loc>(.*?)</loc>", sitemap_text)
    df = (
        spark_session.createDataFrame(urls, "string")
        .toDF("url")
        .repartition(numPartitions=num_partitions)
    )
    return df


# with_columns makes some assumptions:
# (a) that all functions in the with_columns subdag take in some part of the dataframe
# (b) that all intermediate functions in the with_columns subdag need to become columns in the dataframe
@h_spark.with_columns(
    *doc_pipeline.spark_safe,
    select=["article_text", "chunked_text"],
    columns_to_pass=["url"],
)
def chunked_url_text(urls_from_sitemap: ps.DataFrame) -> ps.DataFrame:
    """Creates dataframe with chunked text from URLs appended as columns.

    I.e. `urls_from_sitemap` declares the dependency, and then
    `with_columns` runs and appends columns to it, and then the
    internal part of this function is called.

    :param urls_from_sitemap:
    :return:
    """
    return urls_from_sitemap  # this has the new columns article_text and chunked_text


if __name__ == "__main__":
    import spark_pipeline

    from hamilton import driver

    dr = driver.Builder().with_modules(doc_pipeline, spark_pipeline).with_config({}).build()
    dr.visualize_execution(
        ["chunked_url_text"],
        output_file_path="pipeline.png",
        inputs={"app_name": "chunking_spark_job", "num_partitions": 4},
    )
    result = dr.execute(
        ["chunked_url_text"],
        inputs={"app_name": "chunking_spark_job", "num_partitions": 4},
    )
    print(result["chunked_url_text"].show())
