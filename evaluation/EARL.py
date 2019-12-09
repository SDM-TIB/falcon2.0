# -*- coding: utf-8 -*-
import evaluation
import requests
import csv

headers = {
    'Content-Type': 'application/json',
}


#questions=evaluation.read_LCQUAD()
questions=evaluation.read_LCQUAD2()
#questions=evaluation.read_QALD7()
#questions=evaluation.read_QALD5()
#questions=evaluation.read_QALD6()
correctRelations=0
wrongRelations=0
correctEntities=0
wrongEntities=0
noAnswer=[]
count=1
for question in questions:    
    p_relation=0
    r_relation=0
    p_entity=0
    r_entity=0
    print(count)
    print(question[0])
    data = '{"nlquery":"'+question[0]+'","pagerankflag": false}'
    data=data.encode("utf-8")
    response = requests.post('http://sda.tech/earl/api/processQuery', headers=headers, data=data)
    if response.status_code != 200:
        noAnswer.append(question[0])
        wrongRelations=wrongRelations+len(question[2])
        wrongEntities=wrongEntities+len(question[3])
        continue
    print(response)
    results=response.json()
    relations=[]
    entities=[]
    
    for i in range(len(results["rerankedlists"])):
        if 'http://dbpedia.org/resource/' in results["rerankedlists"][str(i)][0][1]:
            entities.append(results["rerankedlists"][str(i)][0][1])
        else:
            relations.append(results["rerankedlists"][str(i)][0][1])
    print(relations)
    print(entities)
    
    
    numberSystemRelations=len(question[2])
    intersection= set(question[2]).intersection(relations)
    if numberSystemRelations!=0 and len(relations)!=0:
        p_relation=len(intersection)/len(relations)
        r_relation=len(intersection)/numberSystemRelations
    
    numberSystemEntities=len(question[3])
    intersection= set(question[3]).intersection(entities)
    if numberSystemEntities!=0 and len(entities)!=0 :
        p_entity=len(intersection)/len(entities)
        r_entity=len(intersection)/numberSystemEntities
    question.append(relations)
    question.append(entities)
    question.append(p_relation)   
    question.append(r_relation)   
    question.append(p_entity)   
    question.append(r_entity)   
    '''for relation in question[2]:
        if relation in relations:
            correctRelations=correctRelations+1
        else:
            wrongRelations=wrongRelations+1
    for entity in question[3]:
        if entity in entities:
            correctEntities=correctEntities+1
        else:
            wrongEntities=wrongEntities+1'''
    count=count+1

with open('data/EARL_LCQUAD-2.csv',  mode='w' ) as results_file:
    writer=csv.writer(results_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for question in questions:
        if len(question)==4:
            question.append([])
            question.append([])
            question.append(0)
            question.append(0)
            question.append(0)
            question.append(0)
        writer.writerow([question[0],question[2],question[4],question[3],question[5],question[6],question[7],question[8],question[9]])
        
  
