import csv
import spacy
from src import stopwords as wiki_stopwords
from Elastic import searchIndex as wiki_search_elastic
from evaluation import evaluation as wiki_evaluation
from SPARQLWrapper import SPARQLWrapper, JSON, POST
from multiprocessing.pool import ThreadPool


nlp = spacy.load('en_core_web_sm')

wikidataSPARQL="http://node3.research.tib.eu:4010/sparql"

stopWordsList=wiki_stopwords.getStopWords()
comparsion_words=wiki_stopwords.getComparisonWords()
evaluation = False




def get_verbs(question):
    verbs=[]
    entities=[]
    text = nlp(question)
    entities=[x.text for x in text.ents]
    for token in text:
        if (token.pos_=="VERB") and not token.is_stop:
            isEntity=False
            for ent in entities: 
                ent=ent.replace("?","")
                ent=ent.replace(".","")
                ent=ent.replace("!","")
                ent=ent.replace("\\","")
                ent=ent.replace("#","")
                if token.text in ent:
                    ent_list=ent.split(' ')
                    next_token=text[token.i+1]
                    if ent_list.index(token.text)!= len(ent_list)-1 and next_token.dep_ =="compound":
                        isEntity=True
                        break
            if not isEntity:
                verbs.append(token.text)
    return verbs

def split_base_on_verb(combinations,combinations_relations,question):
    newCombinations=[]
    verbs=get_verbs(question)
    flag=False
    for comb in combinations:
        flag=False
        for word in comb.split(' '):
            if word in verbs:
                flag=True
                combinations_relations.append(word.strip())
                #newCombinations.append(word.strip())
                for term in comb.split(word):
                    if term!="":
                        newCombinations.append(term.strip())
        if not flag:
            newCombinations.append(comb)
        
        
    return newCombinations,combinations_relations


                 
              
            
def get_question_combinatios(question,questionStopWords):
    combinations=[]
    tempCombination=""
    if len(questionStopWords)==0:
        combinations = question.split(' ')
    else:
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
    doc = nlp(question)
    verbs=[]
    for token in doc:
        if token.tag_ == "VBD" or token.tag_=="VBZ":
            verbs.append(token.text)
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
        if word in questionStopWords and word in verbs:
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
    
def merge_comb_stop_words(combinations,combinations_relations,question,questionStopWords):
    final_combinations=[]   
    only_stopwords_exist=True
    i=0
    temp=combinations[i]
    while only_stopwords_exist and i+1<len(combinations):
        if wiki_search_elastic.propertySearchExactmatch(temp):
            if not check_only_stopwords_exist(question,temp,combinations[i+1],questionStopWords):
                combinations_relations.append(temp)
                i=i+1
                if (i<len(combinations)):
                    temp = combinations[i]
                    continue
                else:
                    break
            else:
                old_temp=temp
                temp=temp+question[question.find(temp)+len(temp):question.rfind(combinations[i+1])+len(combinations[i+1])]
                if wiki_search_elastic.propertySearchExactmatch(temp):
                    combinations_relations.append(temp)
                    i=i+2
                    if (i<len(combinations)):
                        temp = combinations[i]
                        continue
                    else:
                        break
                else:
                    combinations_relations.append(old_temp)
                    i = i + 1
                    if (i<len(combinations)):
                        temp = combinations[i]
                        continue
                    else:
                        break

        if check_only_stopwords_exist(question,temp,combinations[i+1],questionStopWords):
            temp=temp+question[question.find(temp)+len(temp):question.rfind(combinations[i+1])+len(combinations[i+1])]
            i=i+1
        else:
            if temp=="":
                final_combinations.append(combinations[i])
                i=i+1
                if (i<len(combinations)):
                    temp = combinations[i]
                else:
                    break
            else:
                final_combinations.append(temp)
                i=i+1
                if (i<len(combinations)):
                    temp = combinations[i]
                else:
                    break
                    
    if temp!="":
        final_combinations.append(temp)

    return final_combinations,combinations_relations




def get_question_word_type(questionWord):
    if questionWord.lower()=="who":
        return "http://www.wikidata.org/wiki/Q215627"



def reRank_relations(entities,relations,questionWord,questionRelationsNumber,question,k,head_rule):
    correctRelations=[]
    sparql = SPARQLWrapper(wikidataSPARQL)
    for entity_raw in entities:
        link_found_flag=False
        for entity in entity_raw:
            if not link_found_flag:
                for relation in relations:
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
                        if head_rule:
                            targetType=get_question_word_type(questionWord)
                            if targetType is not None:
                                if check_relation_range_type(relation[1],targetType) :
                                    correctRelations.append(relation)
                                    entity[3]+=45
                                    relation[3]+=45
                            else:
                                correctRelations.append(relation)
                                entity[3]+=40
                                relation[3] += 40
                        else: 
                            correctRelations.append(relation)
                            entity[3]+=12
                            relation[3] += 12
                        link_found_flag=True
                        break
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
                        if head_rule:
                            targetType=get_question_word_type(questionWord)
                            if  targetType is not None :
                                #rangeType=get_relation_range(relation[1])
                                
                                if check_relation_range_type(relation[1],targetType) :
                                    correctRelations.append(relation)
                                    entity[3]+=15
                                    relation[3] += 15
                            else:
                                correctRelations.append(relation)
                                entity[3]+=12
                                relation[3] += 12
                        else: 
                            correctRelations.append(relation)
                            entity[3]+=13
                            relation[3] += 13
                        #link_found_flag=True
                        #break
                #################################################################

  
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
            for relation in sorted(raw, key=lambda x: (-x[3],int(x[1][x[1].rfind("/")+2:-1]),-x[2]))[:k]:
                relations.append(relation)
        else:
            raw= sorted(raw, key = lambda x: (-x[2],int(x[1][x[1].rfind("/")+2:-1])))
            for relation in raw[:k]:
                relations.append(relation)
    return relations

def mix_list_items_entities(mixedEntities,k):
    entities=[]
    for raw in mixedEntities:
        if any(entity[3]>0 for entity in raw):
            for entity in sorted(raw , key=lambda x: (-x[3],-x[2],int(x[1][x[1].rfind("/")+2:-1])))[:k]:
                entities.append(entity)
        else:
            raw= sorted(raw, key = lambda x: (-x[2],int(x[1][x[1].rfind("/")+2:-1])))
            for entity in raw[:k]:
                entities.append(entity)         
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



def process_text_E_R(question,rules,k=1):
    raw=evaluate([question],rules,evaluation=False)
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
        if token.is_stop and token.text!="name":
            stopwords.append((token.text))

    return stopwords

def token_index(doc,token_):
    i=0
    for token in doc:
        if token_ ==token.text:
            return i
        i=i+1
    return -1

def upper_all_entities(combinations,text):
    doc = nlp(text)
    relations=[]
    entities = [x.text for x in doc.ents]
    final_combinations=[]
    for token in doc:
        if  (not token.is_stop) and ( (token.dep_=="compound" and token.pos_!="PROPN") or token.pos_=="VERB" or token.dep_ == "ROOT"):
            isEntity=False
            for ent in entities: 
                ent=ent.replace("?","")
                ent=ent.replace(".","")
                ent=ent.replace("!","")
                ent=ent.replace("\\","")
                ent=ent.replace("#","")
                if token.text in ent:
                    ent_list=ent.split(' ')
                    next_token=doc[token.i+1]
                    if ent_list.index(token.text)!= len(ent_list)-1 and next_token.dep_ =="compound":
                        isEntity=True
                        break
            if not isEntity:
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


def split_base_on_entities(combinations,combinations_relations,text):
    doc = nlp(text)
    #entities = [x.text for x in doc.ents]
    final_combinations=[]
    for comb in combinations:
        comb_processed=False
        for ent in doc.ents: 
            ent_text=ent.text
            ent_text=ent_text.replace("?","")
            ent_text=ent_text.replace(".","")
            ent_text=ent_text.replace("!","")
            ent_text=ent_text.replace("\\","")
            ent_text=ent_text.replace("#","")
            if ent_text in comb and ent.label_ =="PERSON":
                remaining_comb=comb.replace(ent_text,'').strip()
                combinations_relations.append(remaining_comb)
                entity_text=ent_text
                for rem_comb in remaining_comb.split(' '):
                    rem_comb_index=token_index(doc,rem_comb)
                    if doc[rem_comb_index].pos_=="PROPN"  :
                        if rem_comb_index > token_index(doc,ent_text.split(' ')[0]):
                            entity_text=entity_text+" "+rem_comb
                        else:
                            entity_text=rem_comb+" "+entity_text
                    else:
                        break
                final_combinations.append(entity_text)
                if len(comb.replace(entity_text,'').strip())>0:
                    final_combinations.append(comb.replace(entity_text,'').strip())
                comb_processed=True
        if not comb_processed:
            final_combinations.append(comb)
    return final_combinations,combinations_relations
            
                
                
                
def merge_comb_det(combinations,text):
    doc = nlp(text)
    final_combinations=[]
    for comb in combinations:
        if comb.istitle():
            comb_index=token_index(doc,comb)
            if comb_index==-1:
                comb_index=token_index(doc,comb.lower())
            if doc[comb_index-1].tag_=="DT":
                final_combinations.append(doc[comb_index-1].text.capitalize()+" "+comb)
            else:
                final_combinations.append(comb)
        else:
            final_combinations.append(comb)
    return final_combinations
        




def get_relations_seachindex(combinations,combinations_relations):
    final_combinations=[]
    for comb in combinations:
        if wiki_search_elastic.propertySearchExactmatch(comb):
            combinations_relations.append(comb)
        else:
            final_combinations.append(comb)
    return final_combinations,combinations_relations


        

def evaluate(raw,rules,evaluation=True):
    try:
        #global rules
        #evaluation=True
        relations_flag=False
        global correctRelations
        #correctRelations=0
        global wrongRelations
        #wrongRelations=0
        global correctEntities
        #correctEntities=0
        global wrongEntities
        #wrongEntities=0
        global count
        print(count)
        p_entity=0
        r_entity=0
        p_relation=0
        r_relation=0
        k=1
        questionRelationsNumber=0
        entities=[]
        questionWord=raw[0].strip().split(' ')[0]
        
        mixedRelations=[]
        question=raw[0]
        if question.strip()[-1]!="?":
            question=question+"?"
        originalQuestion=question
        question=question[0].lower() + question[1:]
        question=question.replace("?","")
        question=question.replace(".","")
        question=question.replace("!","")
        question=question.replace("\\","")
        question=question.replace("#","")

        questionStopWords = []
        combinations = question.split(' ')
        combinations_relations=[]




        if any(x==1 for x in rules):
            questionStopWords=extract_stop_words_question(question)#rule1: Stopwords cannot be entities or relations
        if any(x==2 for x in rules):
            combinations=get_question_combinatios(question,questionStopWords) #rule 2: If two or more words do not have any stopword in between, consider them as a single compound word
        
        if any(x==4 for x in rules):
            combinations,combinations_relations=split_base_on_verb(combinations,combinations_relations,originalQuestion)  #rule 4: Verbs cannot be an entity, Verbs act as a division point of the sentence in case of two entities and we do not merge tokens from either side of the verb.
            combinations=split_base_on_s(combinations)  
            
        if any(x==3 for x in rules):        
            combinations,combinations_relations=merge_comb_stop_words(combinations,combinations_relations,question,questionStopWords) #rule 3: Entities with only stopwords between them are one entity
        
                  
        if any(x==5 for x in rules):
            for idx,term in enumerate(combinations): #rule 5: If a token does not have any relation candidate, identify it as an entity
                if len(term)==0:
                    continue 
                if term[0].istitle():
                    continue;
    
                propertyResults=wiki_search_elastic.propertySearch(term)
        
                if len(propertyResults) == 0:  
                    combinations[idx]=term.capitalize()
                    question=question.replace(term,term.capitalize())

            if any(x==3 for x in rules): 
                combinations=sort_combinations(combinations,question) 
        

         
        if any(x==8 for x in rules):
            combinations,compare_found=split_bas_on_comparison(combinations) #rule 8: Comparison words acts as a point of division in case of two tokens/entities
    
        if any(x==9 for x in rules):
            combinations=extract_abbreviation(combinations) #rule 9: Abbreviations are separate entities
        
        if any(x==10 for x in rules):
            combinations,combinations_relations=split_base_on_entities(combinations,combinations_relations,originalQuestion) #rule 10: Proper nouns and 

        
        if any(x==14 for x in rules):
            combinations,combinations_relations=get_relations_seachindex(combinations,combinations_relations) #rule 14:
        
        combinations=upper_all_entities(combinations,originalQuestion)

        if any(x==12 for x in rules):
            combinations=merge_comb_det(combinations,originalQuestion) #rule 12: Merge the determiner in the combination, if preceding an entity
            
        #Rules applied during/after elastic search
        i=0
        nationalityFlag=False
        for term in combinations:
            entities_term=[]
            if len(term)==0:
                continue
    
            if check_entities_in_text(originalQuestion,term):
                term=term.capitalize()
            
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
                entities.append(entities_term)
               
                
                
        for term in combinations_relations:
            properties=[]
            propertyResults=wiki_search_elastic.propertySearch(term)
            if len(propertyResults)!=0:
                    propertyResults=[result+[term] for result in propertyResults]
                    properties=properties+propertyResults
            mixedRelations.append("")
            mixedRelations[i]=properties
            i=i+1
            
        questionRelationsNumber=len(mixedRelations)

        if (len(mixedRelations)==0 and questionWord.lower()=="when"): 
            mixedRelations.append([["time","<http://www.wikidata.org/wiki/Property:P569>",0,20,"when"]]) 
    
        for i in range(len(mixedRelations)):
            #print(i)
            mixedRelations[i]=distinct_relations(mixedRelations[i])
            try:
                if any(x==13 for x in rules): #rule13: If the text is a question, use the question word to increase the weight of all the relations which range matches the question word expected answer.
                    head_rule = True
                else:
                    head_rule = False
                mixedRelations[i],entities=reRank_relations(entities,mixedRelations[i],questionWord,questionRelationsNumber,question,k,head_rule)
            except: 
                try:
                    mixedRelations[i],entities=reRank_relations(entities,mixedRelations[i],questionWord,questionRelationsNumber,question,k,head_rule)
                except:
                    continue
            
        mixedRelations=mix_list_items(mixedRelations,k)
        entities=mix_list_items_entities(entities,k)
        
        if nationalityFlag:
            mixedRelations.append(["country","<https://www.wikidata.org/wiki/Property:P17>",20,"country"])
            
        if evaluation:
            if relations_flag:
                numberSystemRelations=len(raw[2])
                intersection= set(raw[2]).intersection([tup[1][tup[1].rfind('/')+1:-1] for tup in mixedRelations])
                if numberSystemRelations!=0 and len(mixedRelations)!=0:
                    p_relation=len(intersection)/len(mixedRelations)
                    r_relation=len(intersection)/numberSystemRelations
    
    
            true_entity=[]
            for e in raw[1]:
                true_entity.append(e)
            numberSystemEntities=len(raw[1])
            intersection= set(true_entity).intersection([tup[1][tup[1].rfind('/')+1:-1] for tup in entities])
    
            if numberSystemEntities!=0 and len(entities)!=0 :
                p_entity=len(intersection)/len(entities)
                r_entity=len(intersection)/numberSystemEntities
            for e in true_entity:
                if e in [tup[1][tup[1].rfind('/')+1:-1] for tup in entities]:
                    correctEntities=correctEntities+1
                else:
                    wrongEntities=wrongEntities+1
    
        count=count+1
        ############        
        raw.append([[tup[1],tup[4]] for tup in mixedRelations])        
        raw.append([[tup[1],tup[4]] for tup in entities])
        raw.append(p_entity)
        raw.append(r_entity)
        raw.append(p_relation)
        raw.append(r_relation)
        global threading
        if threading==True:
            global results
            results.append(raw)
        
        return raw
    except:
        #raise
        print("error")


def datasets_evaluate():
    global threading
    threading=True
    
    global correctRelations
    correctRelations=0
    global wrongRelations
    wrongRelations=0
    global correctEntities
    correctEntities=0
    global wrongEntities
    wrongEntities=0
    errors=0
    global count
    count=1
    
    global results
    results=[]


    
    
    questions=wiki_evaluation.read_simplequestions_entities_upper()
    global rules
    rules = [1,2,3,4,5,8,9,10,12,13,14]
    
    if threading:
        pool = ThreadPool(12)
        pool.map(evaluate, questions)
        pool.close()
        pool.join()
    else:
        for question in questions[:]:
            try:
                single_result=evaluate(question)
                print(count)
                count=count+1
                print( "#####" + str((correctRelations * 100) / (correctRelations + wrongRelations)))
                print("#####" + str((correctEntities * 100) / (correctEntities + wrongEntities)))
                results.append(single_result)
            
            except:
                errors+=1
                print("error"+str(errors))
                continue
     
        
    with open('datasets/results/finaaaaal/FALCON_webqsp.csv', mode='w', newline='', encoding='utf-8') as results_file:
        writer = csv.writer(results_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerows(results)    
    print("Correct Relations:",correctRelations)
    print("Relations:")
    print((correctRelations*100)/(correctRelations+wrongRelations))
    print("Correct Entities:",correctEntities)
    print("Entities:")
    print((correctEntities*100)/(correctEntities+wrongEntities))
    print(correctEntities+wrongEntities)


if __name__ == '__main__':
    #datasets_evaluate()
    global count
    count=0
    global threading
    threading=False
    rules = [1,2,3,4,5,8,9,10,12,13,14]
    #rules = [1,2,3]
    process_text_E_R('who is the wife of barack obama?',rules)
    #datasets_evaluate()


