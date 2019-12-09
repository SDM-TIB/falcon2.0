"""


@author: Sakor
"""
from elasticsearch import Elasticsearch
import json
from multiprocessing.pool import ThreadPool



docType = "doc"
# by default we connect to localhost:9200
es = Elasticsearch(['https://5e9acbee.ngrok.io/'])
path_to_data = '/app/'
# path_to_data = '../'

def addToIndexThread(line):
    try:
        lineObject=json.loads(line, strict=False)
        return addToIndex(lineObject["uri"],lineObject["label"])
    except:
        print ("error")
        return 'error'
    
    

def addToIndex(uri,label):
    try:
        es.index(index=indexName, doc_type=docType, body={"uri":uri, "label":label})
        print (label)
        return True
    except:
        return 'error'

def propertyIndexAdd():
    global indexName
    indexName= "wikidatapropertyindex"
    with open('../data/dbpredicateindex.json',encoding="utf8") as f:
        lines = f.readlines()
        pool = ThreadPool(10)
        pool.map(addToIndexThread, lines)
        pool.close()
        pool.join()      

def OntologyIndexAdd():
    global indexName
    indexName= "dbontologyindex"
    with open('../data/dbontologyindex.json',encoding="utf8") as f:
        lines = f.readlines()
        pool = ThreadPool(10)
        pool.map(addToIndexThread, lines)
        pool.close()
        pool.join()    
    
def entitiesIndexAdd():
    global indexName
    indexName = "wikidataentityindex"
    with open('../data/dbentityindex.json',encoding="utf8") as f:
        lines = f.readlines()
        pool = ThreadPool(10)
        pool.map(addToIndexThread, lines)
        pool.close()
        pool.join()
        
def classesIndexAdd():
    global indexName
    indexName = "dbclassindex"
    with open('../data/dbClassIndex.json',encoding="utf8") as f:
        lines = f.readlines()
        pool = ThreadPool(12)
        pool.map(addToIndexThread, lines)
        pool.close()
        pool.join()
    
    

#if __name__ == '__main__':
    #classesIndexAdd()
