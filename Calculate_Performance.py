import pandas as pd
from Ranking_Metrics import mean_reciprocal_rank, mean_average_precision, top_k

if __name__ == "__main__":
    project_name = "lucene-solr"
    df = pd.read_csv("{}/{}.csv".format(project_name, project_name))
    positions = []
    for item in df['unique_bug_id'].unique().tolist():
        temp_df = df[df['unique_bug_id'] == item]
        positions.append(temp_df['match'].tolist())
    #at_10_positions = [item[:50] for item in positions]
    print(mean_reciprocal_rank(positions))
    print(mean_average_precision(positions))
    print(top_k(positions, k=20))
    print(sum(top_k(positions, k=5).values()))