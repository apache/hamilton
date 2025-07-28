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

import pyarrow as pa
import pyspark.sql.types as pt
import pytest
from pyspark.sql import SparkSession

from hamilton.plugins import h_schema


@pytest.fixture(scope="module")
def spark_session():
    spark = (
        SparkSession.builder.master("local")
        .appName("spark session")
        .config("spark.sql.shuffle.partitions", "1")
        .getOrCreate()
    )
    yield spark
    spark.stop()


@pytest.mark.parametrize(
    "spark_type,arrow_type",
    [
        (pt.NullType(), pa.null()),
        (pt.BooleanType(), pa.bool_()),
        (pt.BinaryType(), pa.binary()),
        (pt.ByteType(), pa.int8()),
        (pt.ShortType(), pa.int16()),
        (pt.IntegerType(), pa.int32()),
        (pt.LongType(), pa.int64()),
        (pt.DateType(), pa.date64()),
        (pt.FloatType(), pa.float32()),
        (pt.DoubleType(), pa.float64()),
        (pt.TimestampType(), pa.timestamp(unit="ms", tz=None)),
        (pt.TimestampNTZType(), pa.timestamp(unit="ms", tz=None)),
        (pt.StringType(), pa.string()),
        (pt.VarcharType(length=10), pa.string()),
        (pt.CharType(length=10), pa.string()),
        (pt.DayTimeIntervalType(), pa.month_day_nano_interval()),
        (pt.YearMonthIntervalType(), pa.month_day_nano_interval()),
        (pt.DecimalType(precision=5, scale=2), pa.decimal128(precision=5, scale=2)),
        (pt.ArrayType(pt.FloatType()), pa.array([], type=pa.float32())),
        (pt.MapType(pt.ByteType(), pt.StringType()), pa.map_(pa.int8(), pa.string())),
        (
            pt.StructType(
                fields=[pt.StructField("a", pt.FloatType()), pt.StructField("b", pt.StringType())]
            ),
            pa.struct(fields=[pa.field("a", pa.float32()), pa.field("b", pa.string())]),
        ),
    ],
)
def test_spark_to_arrow_type(spark_type, arrow_type):
    converted_type = h_schema._spark_to_arrow(spark_type)
    assert converted_type == arrow_type


def test_convert_schema(spark_session):
    pyspark_schema = pt.StructType(
        [
            pt.StructField("a", pt.NullType()),
            pt.StructField("b", pt.StringType()),
            pt.StructField("c", pt.FloatType()),
        ]
    )
    empty_df = spark_session.createDataFrame([], pyspark_schema)
    expected_arrow_schema = pa.schema(
        [
            pa.field("a", pa.null()),
            pa.field("b", pa.string()),
            pa.field("c", pa.float32()),
        ]
    )

    converted_schema = h_schema._get_spark_schema(empty_df)

    assert expected_arrow_schema.equals(converted_schema)
