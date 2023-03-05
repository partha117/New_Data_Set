import pandas as pd
import  json

if __name__ == "__main__":
    project_name = "lucene-solr"
    with open("{}/{}_ES_Search_Result.json".format(project_name, project_name), "r") as f:
        json_file = json.load(f)
    bug_id = []
    doc_id = []
    unique_bug_id_list = []
    score = []
    match = []
    for unique_bug_id in json_file.keys():
        unique_bug_id_list.extend([unique_bug_id] * len(json_file[unique_bug_id]['score']))
        bug_id.extend(json_file[unique_bug_id]['bug_id'])
        doc_id.extend(json_file[unique_bug_id]['doc_id'])
        score.extend(json_file[unique_bug_id]['score'])
        match.extend(json_file[unique_bug_id]['match'])
    df = pd.DataFrame({
        "unique_bug_id": unique_bug_id_list,
        "bug_id": bug_id,
        "doc_id": doc_id,
        "score": score,
        "match": [int(item) for item in match]
    })
    df.to_csv("{}/{}.csv".format(project_name, project_name), index=False)
