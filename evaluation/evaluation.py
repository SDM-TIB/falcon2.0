#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Apr  1 08:44:11 2018

@author: root
"""

import json
import io
import re
count=0

def isLineEmpty(line):
	return len(line) == 0

def process_lcquad_2(questions):
    dataset=[]
    i=0
    for question in questions:
        wikidata_sparql=question['sparql_wikidata']
        #if wikidata_sparql.count(':P') > 1:
            #continue
        #if 'Tell me' in question['question']:
            #continue
        entities_pattern=":Q\d*"
        relations_pattern=":P\d*"
        entities=re.findall(entities_pattern,wikidata_sparql)
        relations=re.findall(relations_pattern,wikidata_sparql)
        entities=[x[1:] for x in entities]
        relations=[x[1:] for x in relations]
        if question['question'] != "n/a":
            question_text=question['question']
        elif question['paraphrased_question'] != []:
            question_text=question['paraphrased_question']
        else:
            question_text=question['NNQT_question'].replace('{','').replace('}','').replace('<','').replace('>','')
        dataset.append([question_text,entities,relations])
        i=i+1
    return dataset
        
        
        


def read_lcquad_2():
    data = json.load(io.open('./datasets/lcquad2_test.json', encoding='utf-8'))
    questions=process_lcquad_2(data)
    return questions
    



def read_test_set():
    data = json.load(io.open('./datasets/webqsp.test.entities.with_classes.json', encoding='utf-8')) 
    questions=[[question['utterance'],[x   for x in question['entities'] if x is not None]] for question in data]
    return questions

def read_simplequestions_entities():
	f = open('./datasets/simplequestions.txt', 'r',encoding='utf-8')
	rows=f.readlines()
	ans = []
	for q in rows:
		q = q.rstrip('\n')
		line = q.split("\t")
		if 'R' in line[1]:
			line[1].replace('R','P')
		if not isLineEmpty(line):
			ans.append([line[3],[line[0]]])
		# if(len(line)!=4):
		# 	print(q," has more elements")
	f.close()
	return ans

def read_simplequestions():
	f = open('./datasets/simplequestions.txt', 'r',encoding='utf-8')
	rows=f.readlines()
	ans = []
	for q in rows:
		q = q.rstrip('\n')
		line = q.split("\t")
		if 'R' in line[1]:
			line[1].replace('R','P')
		if not isLineEmpty(line):
			ans.append([line[3],[line[0]],[line[1].replace('R','P')]])
		# if(len(line)!=4):
		# 	print(q," has more elements")
	f.close()
	return ans

def read_simplequestions_entities_upper():
    f = open('./datasets/simplequestions.txt', 'r',encoding='utf-8')
    rows=f.readlines()
    ans = []
    for q in rows:
        q = q.rstrip('\n')
        line = q.split("\t")
        if 'R' in line[1]:
            line[1].replace('R','P')
        if not isLineEmpty(line):
            line[3]=line[3][0].lower()+line[3][1:]
            if (any(x.isupper() for x in line[3])):
              ans.append([line[3],[line[0]]])
        # if(len(line)!=4):
        # 	print(q," has more elements")
    f.close()
    return ans