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


def process_lcquad_2(questions):
    dataset=[]
    i=0
    for question in questions:
        if i==1000:
            return dataset
        wikidata_sparql=question['sparql_wikidata']
        if wikidata_sparql.count(':P') > 1:
            continue
        if 'Tell me' in question['question']:
            continue
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
        
        
        


def read_lcquad_2():
    data = json.load(io.open('../datasets/lcquad.json', encoding='utf-8'))
    questions=process_lcquad_2(data)
    return questions
    