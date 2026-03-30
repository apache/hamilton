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