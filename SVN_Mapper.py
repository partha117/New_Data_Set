import pandas as pd
import re


if __name__ == "__main__":
    # git svn clone http://svn.apache.org/repos/asf/jackrabbit/trunk
    # git svn log --show-commit --oneline >> commit_log.csv
    regex = r"JCR-\d*"
    regex_finder = re.compile(regex)
    df = pd.read_csv("commit_log.csv", delimiter="|", header=None, on_bad_lines='skip')
    issue_list = []
    for row in df.iterrows():
        temp = regex_finder.findall(row[1][2])
        issue_list.append(temp[0] if len(temp) > 0 else None)
    df['issue_id'] = issue_list

    df.to_csv("commit_log.csv", index=False, header=["svn_commit", "git_commit", "title", "issue_id"])

