import pandas as pd

def file_processor(file_name):
    with open("BugReports/{}.txt".format(file_name), "rb") as f:
        content = f.read().decode('utf-8', errors='ignore')
        content = content.split("Description:")
        return content[0].replace("\r", "").replace("\n", " ").replace("\t", " "), content[1].replace("\r", "").replace("\n", " ").replace("\t", " ")
if __name__ == "__main__":
    localized_bugs = pd.read_excel("Partially Localized.xlsx", header=None)
    commits = pd.read_csv("OldNewCommits.csv", header=None)
    joined_df = pd.merge(left=localized_bugs, right=commits, left_on=0, right_on=2)
    joined_df.drop(columns=['key_0', 2], inplace=True)
    joined_df.rename(columns={'0_x': 'bug_id', '0_y': 'before', 1: 'after', 3: 'project_name'}, inplace=True)
    data = joined_df['bug_id'].map(lambda x: file_processor(x))
    data = list(zip(*data.tolist()))
    joined_df['title'] = data[0]
    joined_df['description'] = data[1]
    joined_df.to_csv('Combined_Data_PL.csv', index=False)

