# FALCON 2.0

Falcon 2.0 is a entity and relation linking tool over Wikidata. It leverages fundamental principles of the English morphology (e.g., N-Gram tiling and N-Gramsplitting) to accurately map entities and relations in short texts to resources in  Wikidata. Falcon is available as Web API and can be queried using CURL: 
```
curl --header "Content-Type: application/json" \
  --request POST \
  --data '{"text":"Who painted The Storm on the Sea of Galilee?"}' \
  https://labs.tib.eu/falcon/falcon2/api?mode=long
```
This is the first resource of this repository. The second resource is described in the ElasticSearch section. 


# Implementation
To begin with, install the libraries stated in the requirements.txt file as follows:
```
pip install -r requirements.txt
```
The code for FALCON tool has three main aspects: elastic search, the algorithm and evaluation. 
## Elastic Search and Background Knowledge
Before we begin working with the Wikidata Dump, we first need to connect to an elasticsearch endpoint, and a Wikidata endpoint. The elasticsearch endpoint is used to interact with our cluster through the Elasticsearch API. 
The ElasticSearch dump (Also knowns as R2: Background Knowledge) for Falcon 2.0 can be downloaded from this link:
https://doi.org/10.6084/m9.figshare.11362883

To import the Elasticsearch dump please use elasticdump and execute the following commands:
```
elasticdump  --output=http://localhost:9200/wikidataentityindex/  --input=wikidataentity.json  --type=data

elasticdump  --output=http://localhost:9200/wikidatapropertyindex/  --input=wikidatapropertyindex.json  --type=data
```

To change your elasticsearch endpoint, makes changes in Elastic/searchIndex.py and Elastic/addIndex.py:
```
es = Elasticsearch(['http://localhost:9200'])
```
Wikidata SPARQL endpoint helps us to quickly search and analyse big volumes of the data stored in the knowledge graph (here, Wikidata). To change Wikidata endpoint, make changes in main.py:
```
wikidataSPARQL = " "
```
We then create indices for property search and entity search over wikidata. Refer to the following two functions in Elastic/addIndex.py for the code:
```
def propertyIndexAdd(): ...
def entitiesIndexAdd(): ...
```
Furthermore, we need to execute a search query and get back search hits that match the query. The search query feature is used to find whether a mention is an entity or a property in Wikidata. Note that Elasticsearch uses JSON as the serialisation format for the documents. The elasticsearch query used to retrieve candidates from elasticsearch is as follows:
```
{
  "query": {
    "match" : { "label" : "operating income" }
  }
}
```
Search queries over Wikidata are implemented in Elastic/searchIndex.py. Refer to the following two functions in the same file for entity search and property search in Wikidata:
```
def entitySearch(query): ...
def propertySearch(query): ...
```

## Algorithm
main.py contains the code for automatic entity and relation linking to resources in Wikidata using rule-based learning. Falcon 2.0 uses the same approach for Wikidata knowledge graph as used in Falcon for DBpedia(https://labs.tib.eu/falcon/). The rules that represent the English morphology are maintained in a catalog; a forward chaining inference process is performed on top of the catalog during the tasks of extractionand linking. Falcon 2.0 also comprises several modules that identify and link entities and relations to Wikidata knowledge graph. These modules implement POS Tagging, Tokenization & Compounding, N-Gram Tiling, Candidate  ListGeneration, Matching & Ranking, Query Classifier, and N-Gram Splitting and are reused from the implementation of Falcon. 

## Evaluation

### Usage
To run Falcon 2.0 you have to call the function "process_text_E_R(question)" where question is the short text to be processed by Falcon 2.0 We

For evaluating Falcon 2.0 we relied on three different question answering datasets namely SimpleQuestion dataset for Wikidata, WebQSP-WD, and LC-QuAD 2.0.

## Experimental Results for Entity Linking

### SimpleQuestions dataset
[SimpleQuestion dataset ](https://github.com/askplatypus/wikidata-simplequestions) contains 5622 test questions which are answerable using Wikidata as underlying Knowledge Graph. Falcon 2.0 reports precision value 0.56, recall value 0.64 and F-score value 0.60 on this dataset. 

### LC-QuAD 2.0 dataset
[LC-Quad 2.0](http://lc-quad.sda.tech/) contains 6046 test questions that are mostly complex (more than one entity and relation). On this dataset, Falcon 2.0 reports a precision value 0.50, recall value 0.56 and F-score 0.53. 


### WebQSP-WD dataset
[WebQSP-WD](https://github.com/UKPLab/coling2018-graph-neural-networks-question-answering/blob/master/WEBQSP_WD_README.md) contains 1639 test questions with single entity and relation per question. Falcon 2.0 outperforms all other baselines with highest F-score value 0.82, precision value 0.80 and highest recall value 0.84 on WebQSP-WD dataset. 

## Experimental Results for Relation Linking

### SimpleQuestions dataset
Falcon 2.0 reports a precision value of 0.35, recall value 0.44 and F-score 0.39 on SimpleQuestions dataset for relation linking task.

### LC-QuAD 2.0
Falcon 2.0 reports a precision value of 0.44, recall value 0.37 and F-score 0.40 on LC-Quad 2.0 dataset. 

