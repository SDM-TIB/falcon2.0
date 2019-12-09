# -*- coding: utf-8 -*-

import requests
import csv
import evaluation


def open_tapioca_call(text):
    # print(text)
    text = text.replace('?','')

    headers = {
        'Accept': 'application/json',
    }
    url = "https://opentapioca.org/api/annotate"
    payload = 'query='

    data = text.split(" ");
    for s in data:
        payload=payload+s
        payload+='+'
    payload+='%3F'
    payload=payload.encode("utf-8")
    response = requests.request("POST", url, data=payload, headers=headers)
    return response.json()

def evaluate(annotations,raw):
    correctRelations=0
    wrongRelations=0
    correctEntities=0
    wrongEntities=0
    p_entity=0
    r_entity=0
    p_relation=0
    r_relation=0
    entities = []
    
    for labels in annotations:
        # print(labels)
        if len(labels)!=0:
            qid = labels['best_qid']
            entities = []
            if qid != None:
                entities.append("<http://www.wikidata.org/wiki/entity:"+str(qid)+">")

    true_entity = "<http://www.wikidata.org/entity/"+raw[0]+">"
    numberSystemEntities=len(raw[0])
        # print(true_entity, entities)
    intersection= set(true_entity).intersection([i for i in entities])
    if len(entities)!=0:
        p_entity=len(intersection)/len(entities)
    r_entity=len(intersection)/numberSystemEntities
    if true_entity in [i for i in entities]:
        correctEntities=correctEntities+1
    else:
        wrongEntities=wrongEntities+1
        correct=False

    return [correctEntities,wrongEntities]

if __name__ == "__main__":
    f = open("simple_main.txt", 'r')
    rows=f.readlines()
    correct = 0
    wrong = 0
    for q in rows:
        q = q.rstrip('\n')
        line = q.split("\t")
        if len(line) != 0: 
            output = open_tapioca_call(line[-1])
            # print(output)
            [c,w] = evaluate(output['annotations'],line)
            correct+=c
            wrong+=w
            print(c)
    print("total correct entities: ",correct)
    print("Total wrong entities: ", wrong)
    f.close()
 
