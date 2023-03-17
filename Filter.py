import pandas as pd

if __name__ == "__main__":
    project_name = "lucene-solr"
    df = pd.read_csv("Combined_Data_FL.csv")
    df = df[df['project_name'] == project_name]
    target_bug_id = df['bug_id'].map(lambda x: int(x.split("-")[-1])).tolist()
    to_be_filtered = pd.read_csv("{}.csv".format(project_name))
    to_be_filtered = to_be_filtered[to_be_filtered['bug_id'].isin(target_bug_id)]
    to_be_filtered.to_csv("{}_FL.csv".format(project_name), index=False)