import pandas as pd
import pyspark.sql as ps
from hamilton_sdk.tracking import pyspark_stats


def test_compute_stats_pyspark():
    df = pd.DataFrame(
        [["a", 1, 2], ["b", 3, 4]],
        columns=["one", "two", "three"],
        index=[5, 6],
    )
    spark_session = ps.SparkSession.builder.getOrCreate()
    result = spark_session.createDataFrame(df)
    # result = Table({"a": "int", "b": "string"})
    node_name = "test_node"
    node_tags = {}
    actual = pyspark_stats.compute_stats_psdf(result, node_name, node_tags)
    expected = {
        "observability_schema_version": "0.0.2",
        "observability_type": "dict",
        "observability_value": {
            "type": "<class 'pyspark.sql.classic.dataframe.DataFrame'>",
            "value": {
                "columns": [
                    {
                        "base_data_type": "str",
                        "data_type": "string",
                        "name": "one",
                        "nullable": True,
                        "pos": 0,
                    },
                    {
                        "base_data_type": "numeric",
                        "data_type": "long",
                        "name": "two",
                        "nullable": True,
                        "pos": 1,
                    },
                    {
                        "base_data_type": "numeric",
                        "data_type": "long",
                        "name": "three",
                        "nullable": True,
                        "pos": 2,
                    },
                ],
                "cost_explain": "== Optimized Logical Plan "
                "==\n"
                "LogicalRDD [one#0, two#1L, "
                "three#2L], false, "
                "Statistics(sizeInBytes=8.0 "
                "EiB)\n"
                "\n"
                "== Physical Plan ==\n"
                "*(1) Scan "
                "ExistingRDD[one#0,two#1L,three#2L]\n"
                "\n",
                "extended_explain": "== Parsed Logical Plan "
                "==\n"
                "LogicalRDD [one#0, "
                "two#1L, three#2L], "
                "false\n"
                "\n"
                "== Analyzed Logical "
                "Plan ==\n"
                "one: string, two: "
                "bigint, three: bigint\n"
                "LogicalRDD [one#0, "
                "two#1L, three#2L], "
                "false\n"
                "\n"
                "== Optimized Logical "
                "Plan ==\n"
                "LogicalRDD [one#0, "
                "two#1L, three#2L], "
                "false\n"
                "\n"
                "== Physical Plan ==\n"
                "*(1) Scan "
                "ExistingRDD[one#0,two#1L,three#2L]\n",
            },
        },
    }
    assert actual == expected
    spark_session.stop()
