from elasticsearch import Elasticsearch


es = Elasticsearch(['https://5e9acbee.ngrok.io/'])
docType = "doc"



def entitySearch(query):
    indexName = "wikidataentityindex"
    results=[]
    ###################################################
    elasticResults=es.search(index=indexName, doc_type=docType, body={
              "query": {
                "match" : { "label" : query } 
              }
               ,"size":10
    }
           )
    for result in elasticResults['hits']['hits']:
        if result["_source"]["label"].lower()==query.replace(" ", "_").lower():
            results.append([result["_source"]["label"],result["_source"]["uri"],result["_score"]*50,40])
        else:
            results.append([result["_source"]["label"],result["_source"]["uri"],result["_score"]*40,0])

    ###################################################
    elasticResults=es.search(index=indexName, doc_type=docType, body={
              "query": {
                "fuzzy" : { "label" : query  } 
              }
               ,"size":5
    }
           )
    for result in elasticResults['hits']['hits']:
        if result["_source"]["label"].lower()==query.replace(" ", "_").lower():
            results.append([result["_source"]["label"],result["_source"]["uri"],result["_score"]*50,40])
        else:
            results.append([result["_source"]["label"],result["_source"]["uri"],result["_score"]*25,0])
    return results
    #for result in results['hits']['hits']:
        #print (result["_score"])
        #print (result["_source"])
        #print("-----------")
        
def propertySearch(query):
    indexName = "wikidatapropertyindex"
    results=[]
    elasticResults=es.search(index=indexName, doc_type=docType, body={
            "query": {
        "bool": {
            "must": {
                "bool" : { "should": [
                      { "multi_match": { "query": query , "fields": ["label"]  }},
                      { "multi_match": { "query": query.replace(" ", "") , "fields": ["uri"] , "fuzziness": "AUTO"}} ] }
            }
        }
    }
            ,"size":10})
    for result in elasticResults['hits']['hits']:
        results.append([result["_source"]["label"],result["_source"]["uri"],result["_score"]*2,0])
    return results

if __name__ == '__main__':
  ans = entitySearch('India')
  props = propertySearch('daughter')
  print("Entity Search: ")
  for x in ans:
    print(x)
  print("Property Search: ")
  for y in props:
    print(y)
    #for result in results['hits']['hits']:
        #print (result["_score"])
        #print (result["_source"])
        #print("-----------")

