# -*- coding: utf-8 -*-
import requests
from evaluation import evaluation as wiki_evaluation
import csv
from elasticsearch import Elasticsearch
from SPARQLWrapper import SPARQLWrapper, JSON


headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
es = Elasticsearch(['http://node1.research.tib.eu:9200/'])
docType = "doc"
dbpediaSPARQL="http://node1.research.tib.eu:4001/sparql"


def SPARQL_call(query,endpoint):
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results

def get_same_as_DBpedia(entity):
    link=""
    query="""
               PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
               SELECT ?links WHERE {<"""+entity+"""> <http://www.w3.org/2002/07/owl#sameAs> ?links}  
            """
    results = SPARQL_call(query,dbpediaSPARQL)
    if len(results['results']['bindings'])==0:
        return link
    else:
        for item in [item['links']['value'] for item in results['results']['bindings']]:
            if "http://www.wikidata.org" in item:
                link=item[item.rfind("/")+1:]
    return link
    
    
def falcon_call(text):
    url = 'https://labs.tib.eu/falcon/falcon2/api?mode=long'
    entities=[]
    payload = '{"text":"'+text+'"}'
    r = requests.post(url, data=payload.encode('utf-8'), headers=headers)
    if r.status_code == 200:
        response=r.json()
        for result in response['entities_wikidata']:
            entities.append(result[0])
    else:
        r = requests.post(url, data=payload.encode('utf-8'), headers=headers)
        if r.status_code == 200:
            response=r.json()
            for result in response['entities_wikidata']:
                entities.append(result[0])
            
    return entities

def evaluate(entities_falcon, entities_goldstandard):
    p_entity = 0
    r_entity = 0

    for i in range(len(entities_falcon)):
        entities_falcon[i]= entities_falcon[i][entities_falcon[i].rfind('/')+1:-1]
        
    numberSystemEntities = len(entities_goldstandard)
    intersection = set(entities_goldstandard).intersection(entities_falcon)
    if len(entities_falcon) != 0:
        p_entity = len(intersection) / len(entities_falcon)
    r_entity = len(intersection) / numberSystemEntities
    

    return p_entity, r_entity 

result = []
result.append(["Question", "Gold Standard Entities","FALCON_Entities","P_E", "R_E"])
questions = wiki_evaluation.read_simplequestions_entities_upper()
#questions = wiki_evaluation.read_test_set()
counter = 0
for question in questions:
    if len(question[1])==0:
        continue
    entities_falcon = falcon_call(question[0])        
    p_e, r_e = evaluate(entities_falcon,question[1])
    result.append([question[0], question[1],entities_falcon, p_e, r_e ])
    print(str(counter))
    counter = counter + 1
    
with open('datasets/falcon_simple_test.csv', mode='w', newline='', encoding='utf-8') as results_file:
    writer = csv.writer(results_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerows(result)
