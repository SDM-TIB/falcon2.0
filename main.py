


import re
import csv
import sys
import spacy
import time
import statistics

from src import stopwords as wiki_stopwords
from Elastic import searchIndex as wiki_search_elastic
from evaluation import evaluation as wiki_evaluation
#from evaluateFalcon2 import read_dataset
from SPARQLWrapper import SPARQLWrapper, JSON, POST
from multiprocessing.pool import ThreadPool
from difflib import SequenceMatcher


nlp = spacy.load('en_core_web_sm')
#wikidataSPARQL="https://17d140f2.ngrok.io/sparql"
wikidataSPARQL="http://node3.research.tib.eu:4010/sparql"

stopWordsList=wiki_stopwords.getStopWords()
comparsion_words=wiki_stopwords.getComparisonWords()
evaluation = False


def get_verbs(question):
    verbs=[]
    text = nlp(question)
    for token in text:
        if token.pos_=="VERB" or token.dep_=="ROOT":
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
                 
                


def word_is_verb(word,question):
    text = nlp(question)
    for token in text:
        if token.text==word and (token.pos_=="VERB" or token.dep_ == "ROOT"):
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




def get_question_word_type(questionWord):
    if questionWord.lower()=="who":
        return "http://www.wikidata.org/wiki/Q215627"


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
                relation_wiki="<http://www.wikidata.org/prop/direct/"+relation[1][relation[1].rfind('/')+1:]
                sparql.setQuery("""
                                    ASK WHERE { 
                                        """+entity[1]+""" """+relation_wiki+""" ?o
                                    }    
                                """)
                sparql.setReturnFormat(JSON)
                sparql.setMethod(POST)
                results1 = sparql.query().convert()
                if results1['boolean']:
                    targetType=get_question_word_type(questionWord)
                    if "/property/" not in relation[1] and  targetType is not None:
                        if check_relation_range_type(relation[1],targetType) :
                            correctRelations.append(relation)
                            entity[3]+=15
                            relation[3]+=15
                    else:
                        correctRelations.append(relation)
                        
                        entity[3]+=12
                        relation[3] += 12
                    continue
                #############################################################
                sparql.setQuery("""
                    ASK WHERE { 
                        ?s """+relation_wiki+""" """+entity[1]+"""
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
                            entity[3]+=10
                            relation[3] += 10
                    else:
                        correctRelations.append(relation)
                        entity[3]+=8
                        relation[3] += 8   
                    continue
                #################################################################
                sparql.setQuery("""
                    ASK WHERE { 
                         """+entity[1]+""" ?p ?o. ?o """+relation_wiki+""" ?z}    
                """)
                sparql.setReturnFormat(JSON)
                if questionRelationsNumber > 1:
                    results3 = sparql.query().convert()
                    if results3['boolean']:
                        targetType=get_question_word_type(questionWord)
                        if "/property/" not in relation[1] and  targetType is not None :
                            
                            if check_relation_range_type(relation[1],targetType) :
                                correctRelations.append(relation)
                                entity[3]+=5
                                relation[3] += 5
                        else:
                            correctRelations.append(relation)
                            entity[3]+=3
                            relation[3] += 3  
                        continue
                sparql.setQuery("""
                    ASK WHERE { 
                        ?s ?p """+entity[1]+""". ?s """+relation_wiki+""" ?z
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
    global count
    k=1

    entities=[]
    
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
        ontologyResults=wiki_search_elastic.ontologySearch(term)
        propertyResults=wiki_search_elastic.propertySearch(term)
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
            entityResults=wiki_search_elastic.entitySearch(term)
            if len(entityResults)>0:
                entities.append([entity+[term] for entity in entityResults])
            
    except:
        return []
    results=[]
    for raw in entities:
        for entity in sorted(raw, reverse=True, key=lambda x: x[2])[:k]:
            results.append(entity)
    return [[entity[1],entity[4]] for entity in results]

def process_word_E(question):
    #print(question)
    startTime=time.time() 
    global count
    k=1

    entities=[]
    question=question.replace("?","")
    question=question.replace(".","")
    question=question.replace("!","")
    question=question.replace("'s","")
    question=question.replace("'","")
    question=question.replace("\\","")
    question=question.replace("#","")
    
  
    try:
        entityResults=wiki_search_elastic.entitySearch(question)
    except:
        return []
    for entity in sorted(entityResults, reverse=True, key=lambda x: x[2])[:k]:
        entities.append(entity)
   
    #print("Entities:")
    #print(entities)
    return [[entity[1],entity[2]] for entity in entities]

def process_text_E_R(question,k=1):
    raw=evaluate([question])
    #time=raw[1]
    #print(raw)
    question=question.replace("?","")
    question=question.strip()
 
    print(raw)
    entities=raw[2]
    
   
    relations=raw[1]
    return entities,relations

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
            

def check_entities_in_text(text,term):
    doc = nlp(text)
    if len(doc.ents)>0:       
        for ent in doc.ents:
            if ent.text==term or ent.text in term:
                return True

    
def extract_stop_words_question(text):
    stopwords=[]
    doc = nlp(text)
    for token in doc:
        if token.is_stop:
            stopwords.append((token.text))

    return stopwords


def upper_all_entities(combinations,text):
    doc = nlp(text)
    relations=[]
    final_combinations=[]
    for token in doc:
        if  (not token.is_stop) and ( (token.dep_=="compound" and token.pos_!="PROPN") or token.pos_=="VERB" or token.dep_ == "ROOT"):
            relations.append(token.text)
    for comb in combinations:
        if len(relations)==0:
            if comb.capitalize() not in final_combinations:
                final_combinations.append(comb.capitalize())
        for relation in relations:
            if relation in comb:
                if comb.lower() not in [x.lower() for x in final_combinations]:
                    final_combinations.append(comb.lower())
                    break 
        if comb.lower() not in [x.lower() for x in final_combinations]:
            final_combinations.append(comb.capitalize())
    return final_combinations



        

def evaluate(raw):
    evaluation=True
    relations_flag=False
    startTime=time.time()
    oneQuestion=False
    global correctRelations
    #correctRelations=0
    global wrongRelations
    #wrongRelations=0
    global correctEntities
    #correctEntities=0
    global wrongEntities
    #wrongEntities=0
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
    questionWord=raw[0].strip().split(' ')[0]
    mixedRelations=[]
    #beforeMixRelations=[]
    question=raw[0]
    #print(question)
    originalQuestion=question
    question=question[0].lower() + question[1:]
    question=question.replace("?","")
    question=question.replace(".","")
    question=question.replace("!","")
    question=question.replace("\\","")
    question=question.replace("#","")

    questionStopWords=extract_stop_words_question(question)
    # print('questionStopWords: ', questionStopWords)
    combinations=get_question_combinatios(question,questionStopWords)
    # print('combinations: ',combinations)
    combinations=merge_comb_stop_words(combinations,question,questionStopWords)
    #print(combinations)

    combinations=split_base_on_verb(combinations,originalQuestion)
    combinations=split_base_on_s(combinations)
    oldCombinations=combinations
    
    for idx,term in enumerate(combinations):
        if len(term)==0:
            continue
        if term[0].istitle():
            continue;

        propertyResults=wiki_search_elastic.propertySearch(term)

        if len(propertyResults) == 0:    
            combinations[idx]=term.capitalize()
            question=question.replace(term,term.capitalize())
            
    combinations=merge_comb_stop_words(combinations,question,questionStopWords)
    combinations=sort_combinations(combinations,question)
    combinations=merge_entity_prefix(question,combinations,originalQuestion)
    combinations,compare_found=split_bas_on_comparison(combinations)
    combinations=extract_abbreviation(combinations)
    combinations=upper_all_entities(combinations,originalQuestion)
    i=0
    nationalityFlag=False
    for term in combinations:
        properties=[]
        entities_term=[]
        if len(term)==0:
            continue

        if check_entities_in_text(originalQuestion,term):
            term=term.capitalize()
        
        if any(x.isupper() for x in term) :
            # print(term," ", i)
            entityResults=wiki_search_elastic.entitySearch(term)
            if " and " in term:
                for word in term.split(' and '):
                    entityResults.extend(wiki_search_elastic.entitySearch(word.strip()))
            if " or " in term:
                for word in term.split(' or '):
                    entityResults.extend(wiki_search_elastic.entitySearch(word.strip()))
            if len(entityResults)!=0:
                for result in entityResults:
                    if result[1] not in [e[1] for e in entities_term]:
                        entities_term.append(result+[term])
                #print(len(entities_term))
                entities.append(entities_term)
                    #print(entities)
        else:
            propertyResults=wiki_search_elastic.propertySearch(term)
            if len(propertyResults)!=0:
                    propertyResults=[result+[term] for result in propertyResults]
                    properties=properties+propertyResults
            mixedRelations.append("")
            mixedRelations[i]=properties
            i=i+1

    questionRelationsNumber=len(mixedRelations)
    oldEnities=entities
    if (len(mixedRelations)==0 and questionWord.lower()=="when") or compare_found:
        mixedRelations.append([["time","<http://www.wikidata.org/wiki/Property:P569>",0,20,"when"]])
        compare_found=False

    for i in range(len(mixedRelations)):
        #print(i)
        mixedRelations[i]=distinct_relations(mixedRelations[i])
        mixedRelations[i],entities=reRank_relations(entities,mixedRelations[i],questionWord,questionRelationsNumber,question,k)
        
    mixedRelations=mix_list_items(mixedRelations,k)
    entities=mix_list_items_entities(entities,k)
    
    if nationalityFlag:
        mixedRelations.append(["country","<https://www.wikidata.org/wiki/Property:P17>",20,"country"])

    if evaluation:
        if relations_flag:
            prop = "<http://www.wikidata.org/wiki/Property:"+raw[2][0]+">"
            #prop =raw[2]
            #numberSystemRelations=len(raw[1])
            numberSystemRelations = 1
            intersection= set(raw[2]).intersection([tup[1][tup[1].rfind('/')+1:-1] for tup in mixedRelations])
            if numberSystemRelations!=0 and len(mixedRelations)!=0:
                p_relation=len(intersection)/len(mixedRelations)
                r_relation=len(intersection)/numberSystemRelations

            if relation[relation.rfind('/')+1:] in [tup[1][tup[1].rfind('/')+1:] for tup in mixedRelations]:
                correctRelations=correctRelations+1

            else:
                wrongRelations=wrongRelations+1
                correct=False
                global questions_labels


        true_entity=[]
        for e in raw[1]:
            true_entity.append(e)
        #true_entity = raw[1]
        numberSystemEntities=len(raw[1])
        # print(true_entity, entities)
        intersection= set(true_entity).intersection([tup[1][tup[1].rfind('/')+1:-1] for tup in entities])

        #true_entity = "<http://www.wikidata.org/entity/"+raw[0]+">"
        numberSystemEntities=len(raw[1])

        if numberSystemEntities!=0 and len(entities)!=0 :
            p_entity=len(intersection)/len(entities)
            r_entity=len(intersection)/numberSystemEntities
        for e in true_entity:
            if e in [tup[1][tup[1].rfind('/')+1:-1] for tup in entities]:
                correctEntities=correctEntities+1
            else:
                wrongEntities=wrongEntities+1
                correct=False

        count=count+1
    #endTime=time.time()
    #raw.append(endTime-startTime)
  
    ############        
    raw.append([[tup[1],tup[4]] for tup in mixedRelations])        
    raw.append([[tup[1],tup[4]] for tup in entities])
    raw.append(p_entity)
    raw.append(r_entity)
    #raw.append(p_relation)
    #raw.append(r_relation)
    return raw


def datasets_evaluate():
    threading=False
    
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
    count=1
    startQ=0
    endQ=5000
    errors=0
    results=[]
    p_e=0
    p_r=0

    #questions=read_dataset('datasets/simplequestions.txt')
    
    
    #filepath = 'datasets/'+dataset_file
    questions=wiki_evaluation.read_test_set()

    
    if threading:
        pool = ThreadPool(12)
        pool.map(evaluate, questions[:50])
        pool.close()
        pool.join()
    else:
        for question in questions:
            #try:
            single_result=evaluate(question)
            print(count)
            count=count+1
            #print( "#####" + str((correctRelations * 100) / (correctRelations + wrongRelations)))
            print("#####" + str((correctEntities * 100) / (correctEntities + wrongEntities)))
            results.append(single_result)
            
            '''except:
                errors+=1
                print("error"+str(errors))
                continue'''
     
        
    with open('datasets/results/FALCON_webqsp.csv', mode='w', newline='', encoding='utf-8') as results_file:
        writer = csv.writer(results_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerows(results)    
    #print("Correct Relations:",correctRelations)
    #print("Relations:")
    #print((correctRelations*100)/(correctRelations+wrongRelations))
    print("Correct Entities:",correctEntities)
    print("Entities:")
    print((correctEntities*100)/(correctEntities+wrongEntities))
    print(correctEntities+wrongEntities)
    ''''print("p_entity:")
    print(p_entity)
    print("p_relation:")
    print(p_relation)'''
    
    #x=[i for i in range (len(questions))]
    #y=[question[4] for question in questions]

if __name__ == '__main__':
    datasets_evaluate()
    #process_text_E_R('What is the operating income for Qantas?')


    
