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

# Data

This example uses the [TMDB 5000 Movie Dataset](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata) from Kaggle.

## Download

1. Create a free Kaggle account at https://www.kaggle.com
2. Go to https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata
3. Click **Download** and unzip the archive
4. Place the following two files in this `data/` folder:

```
data/
├── tmdb_5000_movies.json
└── tmdb_5000_credits.json
```

## Note on file format

The Kaggle archive ships the files as CSV (`tmdb_5000_movies.csv`, `tmdb_5000_credits.csv`).
Several columns contain JSON strings (genres, cast, crew, production_companies).

Convert them to JSON before running ingestion:

```python
import pandas as pd, json

movies = pd.read_csv("tmdb_5000_movies.csv")
credits = pd.read_csv("tmdb_5000_credits.csv")

with open("tmdb_5000_movies.json", "w") as f:
    json.dump(movies.to_dict(orient="records"), f)

with open("tmdb_5000_credits.json", "w") as f:
    json.dump(credits.to_dict(orient="records"), f)
```

Run this script once from inside the `data/` folder, then proceed with `python run.py --mode ingest`.