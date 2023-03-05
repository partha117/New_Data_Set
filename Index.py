from uuid import uuid4
from datetime import datetime
import math
from elasticsearch_dsl import Document, Date, Integer, Keyword, Text, Float, Boolean, InnerDoc, Nested
from elasticsearch_dsl.connections import connections
import json
from tqdm import tqdm
from datetime import datetime
# Define a default Elasticsearch client
connections.create_connection(hosts=['localhost'])
# Bug Id and Id is intended to identify unique bugs. However, bugs from two projects may have same id but not same bug_id. Cid  has been used to uniquely identify document
# + - = && || > < ! ( ) { } [ ] ^ " ~ * ? : \ / cant be used
def sanitize(text):
    char_list = ['+', '-', '=', '&&', '||', '<', '<', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~', '*', '?', ':', '\\', '/']
    sanitized_text = ''
    for char in text:
        if char not in char_list:
            sanitized_text += char
    return sanitized_text
class Others(InnerDoc):
    class_name = Keyword(multi=True,analyzer='standard')
    interface_name = Keyword(multi=True, analyzer='standard')
    method_name = Keyword(multi=True, analyzer='standard')
class Position(InnerDoc):
    class_position = Integer()
    interface_position = Integer()
    method_position = Integer()
class Bugs(Document):
    doc_id = Keyword()
    unique_bug_id = Keyword()
    codes = Text(analyzer='standard', fields={'raw': Keyword()})
    report = Text(analyzer='standard', fields={'raw': Keyword()})
    buggy = Boolean()
    bug_id = Keyword()
    names = Nested(Others)
    project_name = Keyword()
    mode = Keyword()
    position = Nested(Position)
    timestamp = Date()
    path = Text(fields={'raw': Text(index='not_analyzed')})
    file_name = Keyword()

    class Index:
        name = 'bugs'
        settings = {
          "number_of_shards": 2,
        }

    def save(self, ** kwargs):
        return super(Bugs, self).save(** kwargs)

if __name__ == "__main__":
    project_name = 'jackrabbit'
    with open("{}/{}.json".format(project_name, project_name), "rb") as file:
        content = file.read().decode(errors='replace')
        data = json.loads(content)
    for item in tqdm(data):
        #if str(item['id']) == '14406' and item['bug_id'] == "89ab88c0-ec00-467e-a081-22e5d7a8a0dd":
            name_object = Others(class_name=item['NER']['Class_Name'], interface_name=item['NER']['Interface_Name'], method_name=item['NER']['Method_Name'])
            position_object = Position(class_position=sorted(item['position']['class']), method_position=sorted(item['position']['Method']), interface_position=sorted(item['position']['interface']))
            # id is cid and bug_id is id
            if not math.isnan(item['report_timestamp']):
                bug_object = Bugs(doc_id=item['doc_uuid'], unique_bug_id=item['unique_bug_id'], bug_id=item['id'].split("-")[-1],codes=item['contents'],names=name_object, position=position_object, project_name=project_name, report=item['report'], buggy=item['buggy'], timestamp=datetime.fromtimestamp(item['report_timestamp']), path=item['file_path'].split("/")[0:-1],file_name=item['file_path'].split("/")[-1])
            else:
                bug_object = Bugs(doc_id=item['doc_uuid'], unique_bug_id=item['unique_bug_id'], bug_id=item['id'].split("-")[-1],
                              codes=item['contents'], names=name_object, position=position_object,
                              project_name=project_name, report=item['report'], buggy=item['buggy'],
                              timestamp=None,
                              path=item['file_path'].split("/")[0:-1], file_name=item['file_path'].split("/")[-1])
            bug_object.save()