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
    relations=[]
    payload = '{"text":"'+text+'"}'
    r = requests.post(url, data=payload.encode('utf-8'), headers=headers)
    if r.status_code == 200:
        response=r.json()
        for result in response['entities_wikidata']:
            entities.append(result[0])
        for result in response['relations_wikidata']:
            relations.append(result[0])
    else:
        r = requests.post(url, data=payload.encode('utf-8'), headers=headers)
        if r.status_code == 200:
            response=r.json()
            for result in response['entities_wikidata']:
                entities.append(result[0])
            for result in response['relations_wikidata']:
                relations.append(result[0])
            
    return entities,relations

def evaluate(entities_falcon,relations_falcon, entities_goldstandard,relations_goldstandard):
    p_entity = 0
    r_entity = 0
    p_relation = 0
    r_relation = 0
    
    for i in range(len(entities_falcon)):
        entities_falcon[i]= entities_falcon[i][entities_falcon[i].rfind('/')+1:-1]
        
    for i in range(len(relations_falcon)):
        relations_falcon[i]= relations_falcon[i][relations_falcon[i].rfind('/')+1:-1]
    
    numberSystemEntities = len(entities_goldstandard)
    intersection = set(entities_goldstandard).intersection(entities_falcon)
    if len(entities_falcon) != 0:
        p_entity = len(intersection) / len(entities_falcon)
    r_entity = len(intersection) / numberSystemEntities
    
    ################################################################
    numberSystemRelations = len(relations_goldstandard)
    intersection = set(relations_goldstandard).intersection(relations_falcon)
    if len(relations_falcon) != 0:
        p_relation = len(intersection) / len(relations_falcon)
    r_relation = len(intersection) / numberSystemRelations


    return p_entity, r_entity , p_relation, r_relation

result = []
result.append(["Question", "Gold Standard Entities", "Gold Standard Relations", "FALCON_Entities","P_E", "R_E","FALCON_Relations","P_R","R_R"])
questions = wiki_evaluation.read_lcquad_2()
#questions= wiki_evaluation.read_lcquad_2()
counter = 0
for question in questions[:10]:
    if len(question[1])==0:
        continue
    entities_falcon,relations_falcon = falcon_call(question[0])        
    p_e, r_e, p_r , r_r = evaluate(entities_falcon, relations_falcon,question[1],question[2])
    result.append([question[0], question[1], question[2],entities_falcon, p_e, r_e ,relations_falcon, p_r , r_r])
    print(str(counter))
    counter = counter + 1
    
with open('datasets/results/test_api/falcon_lcquad2.csv', mode='w', newline='', encoding='utf-8') as results_file:
    writer = csv.writer(results_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerows(result)
