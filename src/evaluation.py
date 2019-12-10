#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Apr  1 08:44:11 2018

@author: root
"""

import json
import io
import re
import csv
count=0
def extract_relation(query):
    global count
    whereString = query[query.index('{')+1:query.index('}')-1]
    triples=whereString.split(' . ')
    relations=[]
    for triple in triples:
        if '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>' in triple:
            continue
        URIs=triple.split(' ')
        URIs=[x for x in URIs if  x!='' and x!=' '] 
        relations.append(URIs[1][1:-1])
    count=count+len(relations)  
    #print(count)
    return relations

def extract_relation2(query):
    global count
    firstModified=[]
    secondModified=[]
    #print (query)
    whereString = query[query.index('{')+1:query.rfind('}')-1]
    query=whereString
    pattern="<http://dbpedia.org/ontology/[^>]+"
    first=re.findall(pattern,query)
    
    for relation in first:
        if relation[relation.rfind('/')+1:][0].istitle():
            continue
        else:
            firstModified.append(relation[1:])
    pattern="<http://dbpedia.org/property/[^>]+"
    second=re.findall(pattern,query)
    for relation in second:
        if relation[relation.rfind('/')+1:][0].istitle():
            continue
        else:
            secondModified.append(relation[1:])
    
    #print(firstModified+second)
    count=count+len(firstModified+secondModified)
    #print(count)
    return firstModified+secondModified





def extract_entities(query):
    pattern="http://dbpedia.org/resource/[^>]+"
    return re.findall(pattern,query)

def extract_entities_QALD7(query):
    firstModified=[]
    #print (query)
    if query=="OUT OF SCOPE":
        return firstModified
    whereString = query[query.index('{')+1:query.rfind('}')-1]
    if "no_query" in whereString:
        return firstModified
    whereString=whereString.replace("\n","")
    whereString=whereString.replace("\t"," ")
    query=whereString
    pattern="res:[^\s]+"
    first=re.findall(pattern,query)
    
    for entity in first:
        firstModified.append(entity.replace("res:","http://dbpedia.org/resource/"))
    pattern="http://dbpedia.org/resource/[^>]+"
    second=re.findall(pattern,query)
    #print(firstModified+second)
    return firstModified+second
    

def extract_relation_QALD7(query):
    relations=[]
    #print (query)
    if query=="OUT OF SCOPE":
        return relations
    whereString = query[query.index('{')+1:query.rfind('}')-1]
    #print (whereString)
    if "no_query" in whereString:
        return relations
    whereString=whereString.replace("\n","")
    whereString=whereString.replace("\t"," ")
    whereString=whereString.replace("OPTIONAL","")
    whereString=whereString.replace("{","")
    whereString=whereString.replace("}","")
    whereString=whereString.strip()
    triples=whereString.split(' . ')
    
    #print(whereString)
    #print (triples)
    for triple in triples:
        if '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>' in triple:
            continue
        if '<http://www.w3.org/2000/01/rdf-schema#label>' in triple:
            continue
        if 'rdf:type' in triple:
            continue
        if "FILTER" in triple:
            continue
        if "rdfs:label" in triple:
            continue
        #print (triple)
        URIs=triple.strip().split(' ')
        if URIs[1] == "":
            continue
        if  "dbo:" in URIs[1]:
            relations.append("http://dbpedia.org/ontology/"+URIs[1][(URIs[1].find(':')+1):])
        elif "dbp:" in URIs[1]:
            relations.append("http://dbpedia.org/property/"+URIs[1][(URIs[1].find(':')+1):])
        else:
            if URIs[1]=="a":
                continue
            relations.append(URIs[1][1:-1])
    #print(relations)
    return relations

def extract_relations_CSV(raw):
    relations=[]
    if "http://dbpedia.org/ontology/" in raw or "http://dbpedia.org/property/" in raw:
        for uri in raw.split(','):
            if "http://dbpedia.org/resource/" not in uri:
                relations.append(uri)
    else:
        return []
    return relations

def extract_entities_CSV(raw):
    entities=[]
    if "http://dbpedia.org/resource/" in raw:
        for uri in raw.split(','):
            if "http://dbpedia.org/resource/"  in uri:
                entities.append(uri)
    else:
        return []
    return entities        
                    
def read_csv(filename):
    f = open(filename, 'r')
    reader = csv.reader(f)
    rows=list(reader)
    f.close()
    return rows        

def extract_relations_LCQUAD_new(relations):
    result=[]
    for relation in relations:
        result.append(relation['uri'])
    return result
def extract_entities_LCQUAD_new(entities):
    result=[]
    for entity in entities:
        result.append(entity['uri'])
    return result

def extract_relations_LCQUAD_new_labels(relations):
    result=[]
    for relation in relations:
        result.append(relation['uri'])
    return result
def extract_entities_LCQUAD_new_labels(entities):
    result=[]
    for entity in entities:
        result.append(entity['uri'])
    return result
def read_LCQUAD_new():
    data = json.load(io.open('./data/FullyAnnotated_LCQuAD5000.json', encoding='utf-8'))
    questions=[[question['question'],question['sparql_query'],extract_relations_LCQUAD_new(question['predicate mapping']),extract_entities_LCQUAD_new(question['entity mapping'])] for question in data]
    return questions
def read_LCQUAD_new_labels():
    data = json.load(io.open('./data/FullyAnnotated_LCQuAD5000.json', encoding='utf-8'))
    questions=[[question['question'],question['sparql_query'],question['predicate mapping'],question['entity mapping']] for question in data]
    return questions    
def read_LCQUAD():  
    data = json.load(io.open('./data/lcquad_qaldformat.json', encoding='utf-8'))       
    questions=[[question['question'][0]['string'],question['query']['sparql'],extract_relation2(question['query']['sparql']),extract_entities(question['query']['sparql'])] for question in data['questions']]
    return questions

def read_LCQUAD2():
    questions=read_csv('./data/LC-QUAD.csv')
    queries=read_csv('./data/Question-SPARQL.csv')
    i=0
    for query in queries:
        questions[i].append(query[1])
        i=i+1   
    #data = json.load(io.open('./data/lcquad_qaldformat.json', encoding='utf-8'))       
    questions=[[question[1],question[2],extract_relation2(question[2]),extract_entities(question[2])] for question in questions]
    return questions


def read_QALD7():
    data = json.load(io.open('./data/qald-7-train-multilingual.json', encoding='utf-8')) 
    questions=[[question['question'][0]['string'],question['query']['sparql'],extract_relation_QALD7(question['query']['sparql']),extract_entities_QALD7(question['query']['sparql'])] for question in data['questions']]
    return questions

def read_QALD5():
    data = json.load(io.open('./data/qald-5_train.json', encoding='utf-8')) 
    questions=[[question['body'][0]['string'],question['query'],extract_relation_QALD7(question['query']),extract_entities_QALD7(question['query'])] for question in data['questions']]
    return questions

def read_QALD5_2():
    questions=read_csv('./data/questions_qald.csv')
    #data = json.load(io.open('../data/questions_qald.cs', encoding='utf-8')) 
    questions=[[question[1],question[1],extract_relations_CSV(question[2]),extract_entities_CSV(question[2])] for question in questions]
    return questions

def read_QALD5_207():
    questions=read_csv('./data/QALD_207.csv')
    #data = json.load(io.open('../data/questions_qald.cs', encoding='utf-8')) 
    questions=[[question[0],question[1],extract_relations_CSV(question[2]),extract_entities_CSV(question[2])] for question in questions]
    return questions

def read_QALD6():
    data = json.load(io.open('./data/qald-6-train-multilingual.json', encoding='utf-8')) 
    questions=[[question['question'][0]['string'],question['query']['sparql'],extract_relation_QALD7(question['query']['sparql']),extract_entities_QALD7(question['query']['sparql'])] for question in data['questions']]
    return questions
    