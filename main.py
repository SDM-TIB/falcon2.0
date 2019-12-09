

import nltk
import re
import csv
import sys
import nltk
import spacy
import time
import statistics

from src import stopwords
from Elastic import searchIndex
from src import evaluation
from nltk.corpus import wordnet as wn
from evaluateFalcon2 import read_dataset
from SPARQLWrapper import SPARQLWrapper, JSON, POST
from multiprocessing.pool import ThreadPool
from difflib import SequenceMatcher

nlp = spacy.load('en')
wikidataSPARQL="https://17d140f2.ngrok.io/sparql"

stopWordsList=stopwords.getStopWords()
comparsion_words=stopwords.getComparisonWords()

def get_verbs(question):
    verbs=[]
    text = nlp(question)
    for token in text:
        if token.pos_=="VERB":
            verbs.append(token.text)
    return verbs

def split_base_on_verb(combinations,question):
    newCombinations=[]
    verbs=get_verbs(question)
    flag=False
    for comb in combinations:
        flag=False
        if len(comb.strip().split(' '))==1:
            newCombinations.append(comb)
            continue
        for word in comb.split(' '):
            if word in verbs:
                flag=True
                newCombinations.append(word.strip())
                for term in comb.split(word):
                    if term!="":
                        newCombinations.append(term.strip())
        if not flag:
            newCombinations.append(comb)
        
        
    return newCombinations

def split_base_on_titles(combinations):
    newCombinations=[]
    temp=""
    for comb in combinations:
        if len(comb.split(' '))==1:
            newCombinations.append(comb)
            continue
        if not any(c.isupper() for c in comb):
            newCombinations.append(comb)
            continue
        else:
            for word in comb.split(' '):
                if word.isdigit():
                    temp=temp+word+" "
                    continue
                if len(word)<=2:
                    temp=temp+word+" "
                    continue
                if word[0].istitle():
                    if temp=="":
                        temp=temp+word+" "
                    else:
                        if temp[0].istitle():
                            temp=temp+word+" "
                        else:    
                            newCombinations.append(word)
                else:
                    if temp=="":
                        newCombinations.append(word)
                    else:
                        if any(c.isupper() for c in temp):
                            newCombinations.append(temp.strip())
                            temp=word+" "
                        else:
                            temp=temp+word+" "
        if temp!="":
            newCombinations.append(temp.strip())
            temp=""
    return newCombinations
                 
                
def check_verb_exist(text):
    if len(text.split(' '))==1:
        return True
    text = nltk.word_tokenize(text)
    tags=nltk.pos_tag(text)
    for tag in tags:
        if tag[1][:2]=="VB":
            return True
    return False

def word_is_verb(word,question):
    text = nlp(question)
    for token in text:
        if token.text==word and token.pos_=="VERB":
            return True
    return False

def no_words_between(comb1,comb2,question):
    check=question[question.find(comb1)+len(comb1):question.rfind(comb2)]
    if check.strip()=="":
        return True
    else:
        return False

def merge_entity_prefix(question,combinations,originalQuestion):
    newCombinations=[]
    i=0
    while i < len(combinations):
        if i+1 < len(combinations):
            if not word_is_verb(combinations[i],originalQuestion) and not word_is_verb(combinations[i+1],originalQuestion):
                if no_words_between(combinations[i],combinations[i+1],originalQuestion):
                    newCombinations.append(combinations[i]+" "+combinations[i+1])
                    i=i+1
                else:
                    newCombinations.append(combinations[i])         
            else:
                newCombinations.append(combinations[i])
            i=i+1
        if i==len(combinations)-1:
            newCombinations.append(combinations[i])
            i=i+1
    return newCombinations     
            
def get_question_combinatios(question,questionStopWords):
    combinations=[]
    tempCombination=""

    for word in question.split(' '):
        if word in questionStopWords:
            if tempCombination != "":
                combinations.append(tempCombination.strip())
                tempCombination=""
        else:
            tempCombination=tempCombination+word+" "
    if tempCombination != "":
          combinations.append(tempCombination.strip())  
    return combinations

def check_only_stopwords_exist(question,comb1,comb2,questionStopWords):
    check=question[question.find(comb1)+len(comb1):question.rfind(comb2)]
    if check==" ":
        return True
    flag=True
    count=1
    for word in check.strip().split(' '):
        if count == 3:
            flag=False
            break
        if word not in questionStopWords:
            flag=False
            break
        if word=="is":
            flag=False
            break
        if word =="and" and (len(comb1.split(' ')) > 1 or  len(comb2.split(' ')) > 1):
            flag=False
            break
        count=count+1
            
    return flag
    
    
def sort_combinations(combinations,question):
    question=question.replace("'s","")
    question=question.replace("'","")
    sorted_combinations=[]
    questionWords=question.strip().split(' ')
    i=0
    while i < len(questionWords):
        word=questionWords[i]
        match=[s for s in combinations if any(word == x for x in s.split(' '))]
        if match != []:
            #print(match)
            sorted_combinations.append(match[0])
            combinations.remove(match[0])
            i=i+len(match[0].strip().split(' '))
            continue
        i=i+1
    return sorted_combinations
    
def merge_comb_stop_words(combinations,question,questionStopWords):
    mergedCombinations=[]
    remainCombinations=[]
    questionWords=question.split(' ')
    for comb in combinations:
        if len(comb)==0:
            continue
        if any(x.istitle() for x in comb):
            remainCombinations.append(comb)
        else:
            mergedCombinations.append(comb)
    temp=""      

    i=0
    if len(remainCombinations)==1:
        mergedCombinations.append(remainCombinations[0])
        return mergedCombinations
    while i < len(remainCombinations):

        if i+1<len(remainCombinations):
            if temp=="":
                current=remainCombinations[i]
            else:
                current=temp
            if check_only_stopwords_exist(question,current,remainCombinations[i+1],questionStopWords):
                temp=current+question[question.find(current)+len(current):question.rfind(remainCombinations[i+1])]+remainCombinations[i+1]
                i=i+2
                continue
            else:
                if temp!="":
                    mergedCombinations.append(temp.strip())
                    temp=""
                    continue
                else:
                    mergedCombinations.append(remainCombinations[i])
                temp=""
        else:
            if temp!="":
                if check_only_stopwords_exist(question, temp, remainCombinations[i], questionStopWords):
                    final=temp+question[question.find(temp)+len(temp):question.rfind(remainCombinations[i])]+remainCombinations[i]
                    mergedCombinations.append(final)
                else:
                    mergedCombinations.append(temp)
                    mergedCombinations.append(remainCombinations[i])
            else:
                mergedCombinations.append(remainCombinations[i])
        i=i+1
    if temp!="":
        mergedCombinations.append(temp)

    return mergedCombinations

def reRank_results(relation,results):
    count=0
    results_indexes=[]
    for result in results:
        distance=nltk.edit_distance(relation[relation.rfind('/')+1:],result[1][result[1].rfind('/')+1:])
        results_indexes.append([count,distance])
        count=count+1
    results_indexes.sort(key=lambda tup: tup[1])
    final_results=[]
    for result in results_indexes:
        final_results.append(results[result[0]])
    return final_results

# not used in Falcon 2.0
def get_relation_range(relation):
    sparql = SPARQLWrapper(wikidataSPARQL)
    sparql.setQuery("""
               PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
               SELECT ?range WHERE {<relation> rdfs:range ?range}  
            """)
    sparql.setReturnFormat(JSON)
    results1 = sparql.query().convert()
    if len(results1['results']['bindings'])==0:
        return ""
    else:
        return results1['results']['bindings'][0]['range']['value']


def get_question_word_type(questionWord):
    if questionWord.lower()=="who":
        return "http://www.wikidata.org/wiki/Q215627"

# not used in Falcon 2.0  
def check_entity_type(entity,rangeType):
    sparql = SPARQLWrapper(wikidataSPARQL)
    sparql.setQuery("""
               PREFIX rdf: <http://www.w3.org/2000/01/rdf-schema#label>
               ASK {<entity[1]> rdf:type <rangeType>}  
            """)
    sparql.setReturnFormat(JSON)
    results1 = sparql.query().convert()
    return results1['boolean']


def rank_triple(entities,relations,questionWord,question,k):
    correctRelations=[]
    sparql = SPARQLWrapper(wikidataSPARQL)
    entity1Candidates=entities[0]
    entity2Candidates=entities[1]
    for entity1 in entity1Candidates:
        for entity2 in entity2Candidates:
            for relation in relations:
                sparql.setQuery("""
                        ASK WHERE { 
                            <entity1[1]> <relation[1]> <entity2[1]>
                        }    
                    """)
                sparql.setReturnFormat(JSON)
                results1 = sparql.query().convert()
                if results1['boolean']:
                    targetType=get_question_word_type(questionWord)
                    if "/property/" not in relation[1] and  targetType is not None :
                        if check_relation_range_type(relation[1],targetType) :
                            correctRelations.append(relation)
                            entity1[2]+=50
                            entity2[2]+=50
                            
                    else:
                        correctRelations.append(relation)
                        entity1[2]+=50
                        entity2[2]+=50
                    continue
                sparql.setQuery("""
                        ASK WHERE { 
                            <entity2[1]> <relation[1]> <entity1[1]>
                        }    
                    """)
                sparql.setReturnFormat(JSON)
                results2 = sparql.query().convert()
                if results2['boolean']:
                    targetType=get_question_word_type(questionWord)
                    if "/property/" not in relation[1] and  targetType is not None :
                        #rangeType=get_relation_range(relation[1])
                        if check_relation_range_type(relation[1],targetType) :
                            correctRelations.append(relation)
                            #entity_raw[0]=entity
                            entity1[2]+=50
                            entity2[2]+=50
                            
                            #print("query 1")
                    #print(relation)
                    else:
                        correctRelations.append(relation)
                        #entity_raw[0]=entity
                        entity1[2]+=50
                        entity2[2]+=50
                    #return correctRelations[:k],entities
                    continue
    entities=[]
    entities.append(entity1Candidates)
    entities.append(entity2Candidates)
    if len(correctRelations)==0:
        return relations,entities
    else:
        correctRelations=distinct_relations(correctRelations)
        return correctRelations ,entities
    
def reRank_relations(entities,relations,questionWord,questionRelationsNumber,question,k):
    correctRelations=[]
    sparql = SPARQLWrapper(wikidataSPARQL)
    for entity_raw in entities:
        for entity in entity_raw:
            for relation in relations:
                flag=False
                sparql.setQuery("""
                                    ASK WHERE { 
                                        <entity[1]> <relation[1]> ?o
                                    }    
                                """)
                sparql.setReturnFormat(JSON)
                sparql.setMethod(POST)
                results1 = sparql.query().convert()
                if results1['boolean']:
                    targetType=get_question_word_type(questionWord)
                    if "/property/" not in relation[1] and  targetType is not None:
                        #rangeType=get_relation_range(relation[1])
                        if check_relation_range_type(relation[1],targetType) :
                            correctRelations.append(relation)
                            #entity_raw[0]=entity
                            entity[3]+=15
                            relation[3]+=15
                            #print(relation)
                            #print(entity)
                            
                            #print("query 1")
                    #print(relation)
                    else:
                        correctRelations.append(relation)
                        #entity_raw[0]=entity
                        
                        entity[3]+=12
                        relation[3] += 12
                        #print(relation)
                        #print(entity)
                    #return correctRelations[:k],entities
                    continue
                #############################################################
                sparql.setQuery("""
                    ASK WHERE { 
                        ?s <relation[1]> <entity[1]> 
                    }    
                """)
                sparql.setReturnFormat(JSON)
                sparql.setMethod(POST)
                results2 = sparql.query().convert()
                if results2['boolean']:
                    targetType=get_question_word_type(questionWord)
                    if "/property/" not in relation[1] and  targetType is not None :
                        #rangeType=get_relation_range(relation[1])
                        
                        if check_relation_range_type(relation[1],targetType) :
                            correctRelations.append(relation)
                            #entity_raw[0]=entity
                            entity[3]+=10
                            relation[3] += 10
                            #print(relation)
                            #print(entity)
                            #print("query 2")
                    #print(relation)
                    else:
                        correctRelations.append(relation)
                        #entity_raw[0]=entity
                        entity[3]+=8
                        relation[3] += 8
                        #print(relation)
                        #print(entity)
                        #return correctRelations[:k],entities    
                    continue
                #################################################################
                sparql.setQuery("""
                    ASK WHERE { 
                         <entity[1]> ?p ?o. ?o <relation[1]> ?z.}    
                """)
                sparql.setReturnFormat(JSON)
                if questionRelationsNumber > 1:
                    results3 = sparql.query().convert()
                    if results3['boolean']:
                        targetType=get_question_word_type(questionWord)
                        if "/property/" not in relation[1] and  targetType is not None :
                            #rangeType=get_relation_range(relation[1])
                            
                            if check_relation_range_type(relation[1],targetType) :
                                correctRelations.append(relation)
                                #entity_raw[0]=entity
                                #print(entity)
                                entity[3]+=5
                                relation[3] += 5
                                #print(relation)
                                #print(entity)
                                #print("query 3")
                        #print(relation)
                        else:
                            correctRelations.append(relation)
                            entity[3]+=3
                            relation[3] += 3
                            #print(relation)
                            #print(entity)
                            #entity_raw[0]=entity
                        #return correctRelations[:k],entities    
                        continue
                sparql.setQuery("""
                    ASK WHERE { 
                        ?s ?p <entity[1]>. ?s <relation[1]> ?z
                    }    
                """)
  
    return relations,entities


def distinct_relations(relations):
    result=[]
    #print(len(relations))
    if len(relations)==1:
        return relations
    for relation in relations:
        #print(relations)
        if relation[1] not in [tup[1] for tup in result]: 
            result.append(relation)
    return result

def mix_list_items(mixedRelations,k):
    relations=[]
    for raw in mixedRelations:
        if any(relation[3]>0 for relation in raw):
            for relation in sorted(raw, reverse=True, key=lambda x: x[3])[:k]:
                relations.append(relation)
        else:
            for relation in sorted(raw, reverse=True, key=lambda x: x[2])[:k]:
                relations.append(relation)
    return relations

def mix_list_items_entities(mixedEntities,k):
    entities=[]
    for raw in mixedEntities:
        if any(entity[3]>0 for entity in raw):
            for entity in sorted(raw, reverse=True, key=lambda x: x[3])[:k]:
                entities.append(entity)
        else:
            for entity in sorted(raw, reverse=True, key=lambda x: x[2])[:k]:
                entities.append(entity)         
    return entities

def rank_entities_string_similarity(entities):
    for raw in entities:
        for entity in raw:
            if entity[2]!=0:
                entity[2]+=(SequenceMatcher(None, entity[3], entity[1][entity[1].rfind('/')+1:]).ratio())*10
                entity[2]+=(SequenceMatcher(None, entity[3], entity[0]).ratio())*20
    return entities
            
            

#try not using first trial
def relations_improvement_country(entities):
    # country check
    relations=[]
    for entity in entities:
            sparql = SPARQLWrapper(wikidataSPARQL)
            sparql.setQuery("""
                       ASK {?s <http://dbpedia.org/ontology/language> <"""+entity[1]+"""_language>. ?s rdf:type <http://dbpedia.org/ontology/Country>}     
                    """)
            sparql.setReturnFormat(JSON)
            results1 = sparql.query().convert()
            if results1['boolean']:
                relations.append(["country","http://dbpedia.org/ontology/country",0,20])    
    return relations

#try not using first trial
def relations_entities_country_improvement(terms):
    # country check
    for term in terms.split(' '):
        sparql = SPARQLWrapper(wikidataSPARQL)
        sparql.setQuery("""
                   SELECT ?s WHERE { ?s <http://dbpedia.org/ontology/demonym> '"""+term+"""'@en}
                """)
        sparql.setReturnFormat(JSON)
        results1 = sparql.query().convert()
        if len(results1['results']['bindings'])==0:
            return ""
        else:
            return results1['results']['bindings'][0]['s']['value']

def check_relation_range_type(relation,qType):
    return True
    sparql = SPARQLWrapper(wikidataSPARQL)
    sparql.setQuery("""
               PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
               ASK {<"""+relation+"""> rdfs:range <"""+qType+"""> }
            """)
    sparql.setReturnFormat(JSON)
    results1 = sparql.query().convert()
    if results1['boolean']:
        return True
    else:
        sparql.setQuery("""
               PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
               ASK {<"""+relation+"""> rdfs:range ?range. ?range rdfs:subClassOf ?t. ?t rdfs:subClassOf <"""+qType+""">}
            """)
        sparql.setReturnFormat(JSON)
        results2 = sparql.query().convert()
        if results2['boolean']:
            return True
        else:
            return False
    return results1['boolean']
 
def split_base_on_s(combinations):
    result=[]
    for comb in combinations:
        if "'s" in comb:
            result.extend(comb.split("'s"))
        elif "'" in comb:
            result.extend(comb.split("'"))
        else:
            result.append(comb)
    return result

def process_word_E_long(question):
    #print(question)
    #startTime=time.time() 
    global count
    k=1

    entities=[]
    
    #question=question[0].lower() + question[1:]
    originalQuestion=question
    question=question.replace("?","")
    question=question.replace(".","")
    question=question.replace("!","")
    question=question.replace("'s","")
    question=question.replace("'","")
    question=question.replace("\\","")
    question=question.replace("#","")
    question=question[0].lower()+question[1:]
    questionStopWords=stopwords.extract_stop_words_question(question,stopWordsList)
    combinations=get_question_combinatios(question,questionStopWords)  
    combinations=split_base_on_verb(combinations,originalQuestion)
    for idx,term in enumerate(combinations):
        if len(term)==0:
            continue
        if term[0].istitle():
            continue;
        ontologyResults=searchIndex.ontologySearch(term)
        propertyResults=searchIndex.propertySearch(term)
        if len(ontologyResults) > 2 or len(propertyResults) > 0:
            del combinations[idx]
            
    combinations=merge_comb_stop_words(combinations,question,questionStopWords)
    combinations=sort_combinations(combinations,question)
    combinations=merge_entity_prefix(question,combinations,originalQuestion)
    combinations,compare_found=split_bas_on_comparison(combinations)
    combinations=extract_abbreviation(combinations)
    try:
        for term in combinations:
            #print(term)
            entityResults=searchIndex.entitySearch(term)
            if len(entityResults)>0:
                entities.append([entity+[term] for entity in entityResults])
            
    except:
        return []
    results=[]
    for raw in entities:
        for entity in sorted(raw, reverse=True, key=lambda x: x[2])[:k]:
            results.append(entity)
   
    #print("Entities:")
    #print(entities)
    return [[entity[1],entity[4]] for entity in results]
def process_word_E(question):
    #print(question)
    startTime=time.time() 
    global count
    k=1

    entities=[]
    #question=question[0].lower() + question[1:]
    question=question.replace("?","")
    question=question.replace(".","")
    question=question.replace("!","")
    question=question.replace("'s","")
    question=question.replace("'","")
    question=question.replace("\\","")
    question=question.replace("#","")
    
  
    try:
        entityResults=searchIndex.entitySearch(question)
    except:
        return []
    for entity in sorted(entityResults, reverse=True, key=lambda x: x[2])[:k]:
        entities.append(entity)
   
    #print("Entities:")
    #print(entities)
    return [[entity[1],entity[2]] for entity in entities]

def extract_abbreviation(combinations):
    new_comb=[]
    for com in combinations:
        abb_found=False
        for word in com.strip().split(' '):
            if word.isupper():
                abb_found=True
                new_comb.append(word)
                remain=com.replace(word,"").strip()
                if remain !="":
                    new_comb.append(remain)
        if not abb_found:
            new_comb.append(com)
    return new_comb
                
def split_bas_on_comparison(combinations):
    compare_found=False
    new_comb=[]
    for com in combinations:     
        comp_found=False
        for word in com.split(' '):
            if word in comparsion_words:
                compare_found=True
                comp_found=True
                comp_word=word
        if comp_found:
            com=com.replace("than","").strip()
            new_comb.extend(com.split(comp_word))
        else:
            new_comb.append(com)
    return new_comb,compare_found
            

def evaluate(raw):
    evaluation=True
    startTime=time.time()
    oneQuestion=False
    global correctRelations
    correctRelations=0
    global wrongRelations
    wrongRelations=0
    global correctEntities
    correctEntities=0
    global wrongEntities
    wrongEntities=0
    global count
    count=1
    p_entity=0
    r_entity=0
    p_relation=0
    r_relation=0
    k=1
    correct=True
    questionRelationsNumber=0
    entities=[]
    questionWord=raw[-1].strip().split(' ')[0]
    mixedRelations=[]
    #beforeMixRelations=[]
    question=raw[-1]
    print(question)
    originalQuestion=question
    question=question[0].lower() + question[1:]
    question=question.replace("?","")
    question=question.replace(".","")
    question=question.replace("!","")
    #question=question.replace("'s","")
    #question=question.replace("'","")
    question=question.replace("\\","")
    question=question.replace("#","")
    questionStopWords=stopwords.extract_stop_words_question(question,stopWordsList)
    # print('questionStopWords: ', questionStopWords)
    combinations=get_question_combinatios(question,questionStopWords)
    # print('combinations: ',combinations)
    #combinations=merge_comb_stop_words(combinations,question,questionStopWords)
    #print(combinations)
    combinations=split_base_on_verb(combinations,originalQuestion)
    # print('N-gram tilin: ',combinations)
    #combinations=split_base_on_titles(combinations)
    #print(combinations)
    combinations=split_base_on_s(combinations)
    # print("Combos: ",combinations)
    oldCombinations=combinations
    
    for idx,term in enumerate(combinations):
        if len(term)==0:
            continue
        if term[0].istitle():
            continue;
        # ontologyResults=searchIndex.ontologySearch(term)
        propertyResults=searchIndex.propertySearch(term)
        # if len(ontologyResults) == 0 and len(propertyResults) == 0:
        if len(propertyResults) == 0:    
            combinations[idx]=term.capitalize()
            question=question.replace(term,term.capitalize())
            
    combinations=merge_comb_stop_words(combinations,question,questionStopWords)
    combinations=sort_combinations(combinations,question)
    combinations=merge_entity_prefix(question,combinations,originalQuestion)
    combinations,compare_found=split_bas_on_comparison(combinations)
    combinations=extract_abbreviation(combinations)
    # print("Combos: ",combinations)
    i=0
    nationalityFlag=False
    for term in combinations:
        #print(term)
        properties=[]
        entities_term=[]
        if len(term)==0:
            continue
        
        if (not word_is_verb(term,originalQuestion)) and (term[0].istitle() or len(term.split(' ')) > 2 or (len(term)>1 and  len(searchIndex.propertySearch(term)) < 2 ) or (any(x.isupper() for x in term))) :
            # print(term," ", i)
            entityResults=searchIndex.entitySearch(term)
            if " and " in term:
                for word in term.split(' and '):
                    entityResults.extend(searchIndex.entitySearch(word.strip()))
            if " or " in term:
                for word in term.split(' or '):
                    entityResults.extend(searchIndex.entitySearch(word.strip()))
            if len(entityResults)!=0:
                for result in entityResults:
                    if result[1] not in [e[1] for e in entities_term]:
                        entities_term.append(result+[term])
                #print(len(entities_term))
                entities.append(entities_term)
                    #print(entities)
        else:
            propertyResults=searchIndex.propertySearch(term)
            if len(propertyResults)!=0:
                    propertyResults=[result+[term] for result in propertyResults]
                    properties=properties+propertyResults
            mixedRelations.append("")
            mixedRelations[i]=properties
            i=i+1

    questionRelationsNumber=len(mixedRelations)
    oldEnities=entities
    if (len(mixedRelations)==0 and questionWord.lower()=="when") or compare_found:
        # mixedRelations.append([["date","http://dbpedia.org/ontology/date",0,20],["date","http://dbpedia.org/property/date",0,20]])
        mixedRelations.append([["time","http://www.wikidata.org/wiki/Property:P569",0,20]])
        compare_found=False

    for i in range(len(mixedRelations)):
        #print(i)
        mixedRelations[i]=distinct_relations(mixedRelations[i])
        mixedRelations[i],entities=reRank_relations(entities,mixedRelations[i],questionWord,questionRelationsNumber,question,k)
        
    mixedRelations=mix_list_items(mixedRelations,k)
    entities=mix_list_items_entities(entities,k)
    # print(entities)
    # mixedRelations.extend(relations_improvement_country(entities))
    
    if nationalityFlag:
        mixedRelations.append(["country","https://www.wikidata.org/wiki/Property:P17",20])

    if evaluation:
        prop = "<http://www.wikidata.org/wiki/Property:"+raw[1]+">"
        numberSystemRelations=len(raw[1])
        intersection= set(raw[1]).intersection([tup[1] for tup in mixedRelations])
        if numberSystemRelations!=0 and len(mixedRelations)!=0:
            p_relation=len(intersection)/len(mixedRelations)
            r_relation=len(intersection)/numberSystemRelations
        if relation[relation.rfind('/')+1:] in [tup[1][tup[1].rfind('/')+1:] for tup in mixedRelations]:
            #p_relation=1/numberSystemRelations
            correctRelations=correctRelations+1
            #print(raw[0])
        else:
            wrongRelations=wrongRelations+1
            correct=False
            global questions_labels

        true_entity = "<http://www.wikidata.org/entity/"+raw[0]+">"
        numberSystemEntities=len(raw[0])
        # print(true_entity, entities)
        intersection= set(true_entity).intersection([tup[1] for tup in entities])
        if numberSystemEntities!=0 and len(entities)!=0 :
            p_entity=len(intersection)/len(entities)
            r_entity=len(intersection)/numberSystemEntities
        if true_entity in [tup[1] for tup in entities]:
            correctEntities=correctEntities+1
        else:
            wrongEntities=wrongEntities+1
            correct=False

        count=count+1
    endTime=time.time()
    raw.append(endTime-startTime)
  
    ############        
    raw.append([[tup[1],tup[4]] for tup in mixedRelations])        
    raw.append([[tup[1],tup[4]] for tup in entities])
    return raw


def datasets_evaluate():
    threading=True
    k=1
    kMax=10
    p_entity=0
    p_relation=0
    global correctRelations
    correctRelations=0
    global wrongRelations
    wrongRelations=0
    global correctEntities
    correctEntities=0
    global wrongEntities
    wrongEntities=0
    global count
    count=1
    startQ=0
    endQ=5000
    errors=0

    questions=read_dataset('datasets/simplequestions.txt')
    
    if threading:
        pool = ThreadPool(12)
        pool.map(evaluate, questions)
        pool.close()
        pool.join()
    else:
        for question in questions:
            #print(question[0])
            try:
                evaluate(question)
            except:
                errors+=1
                print(errors)
                continue
        
    print("Correct Relations:",correctRelations)
    print("Relations:")
    print((correctRelations*100)/(correctRelations+wrongRelations))
    print("Correct Entities:",correctEntities)
    print("Entities:")
    print((correctEntities*100)/(correctEntities+wrongEntities))
    print(correctEntities+wrongEntities)
    print("p_entity:")
    print(p_entity)
    print("p_relation:")
    print(p_relation)
    
    x=[i for i in range (len(questions))]
    y=[question[4] for question in questions]

if __name__ == '__main__':
    datasets_evaluate()

    

