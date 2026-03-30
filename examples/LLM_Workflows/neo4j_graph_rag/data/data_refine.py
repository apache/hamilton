import pandas as pd, json
 
movies = pd.read_csv("examples/LLM_Workflows/neo4j_graph_rag/data/tmdb_5000_movies.csv")
credits = pd.read_csv("examples/LLM_Workflows/neo4j_graph_rag/data/tmdb_5000_credits.csv")
 
with open("examples/LLM_Workflows/neo4j_graph_rag/data/tmdb_5000_movies.json", "w") as f:
    json.dump(movies.to_dict(orient="records"), f)
 
with open("examples/LLM_Workflows/neo4j_graph_rag/data/tmdb_5000_credits.json", "w") as f:
    json.dump(credits.to_dict(orient="records"), f)