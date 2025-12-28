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
Code courtesy of the FalkorDB.
"""

from datetime import datetime


# convert hight in feet and inches to centimeters
def height_to_cm(height):
    # Split the height string into feet and inches
    feet, inches = height.split("'")
    feet = int(feet)
    inches = int(inches.replace('"', ""))

    # Convert feet and inches to centimeters
    total_inches = feet * 12 + inches
    cm = total_inches * 2.54

    return cm


# Convert reach from inches to centimeters
def reach_to_cm(reach):
    # Convert inches to centimeters
    inches = int(reach.replace('"', ""))
    return inches * 2.54


# Convert datetime to UNIX timestamp
def date_to_timestamp(date_str):
    # Parse the date string into a datetime object
    try:
        date_obj = datetime.strptime(date_str, "%b %d, %Y")
    except ValueError:
        try:
            date_obj = datetime.strptime(date_str, "%B %d, %Y")
        except ValueError:
            return None

    # Convert the datetime object to a Unix timestamp
    timestamp = date_obj.timestamp()

    return int(timestamp)


# Convert time in min:seconds format to number of seconds
def time_to_seconds(time):
    # 1:58
    minutes, seconds = map(int, time.split(":"))
    return minutes * 60 + seconds


# Convert percentage to float
def percentage_to_float(precentage):
    p = int(precentage.replace("%", ""))
    return float(p / 100.0)


# Convert ratio in the format x of y to float
def percentage_from_ratio(ratio):
    # 41 of 103
    count, total = map(int, ratio.split(" of "))
    if total == 0:
        return 0.0

    return float(count / total)
