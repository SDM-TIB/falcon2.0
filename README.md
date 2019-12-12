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
To begin with, install the libraries stated in the requiremnts.txt file as follows:
```
pip install -r requirements.txt
```
The code for FALCON tool has three main aspects: elastic search, the algorithm and evaluation. 
## Elastic Search and Background Knowlege
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
You may choose to run the tool for a single query or evaluate it on a dataset.
To run the tool on a single query (short text):
```
python3 main.py --q <query>
```

When evaluating a dataset, the program compares the entitites and relations extracted by Falcon 2.0 to that of the entitites and relations in the dataset for each question. To evaluate the tool on a dataset:
```
python3 main.py --d <path_To_Dataset>
```

We empirically evaluated Falcon 2.0 on a question answering dataset tailored for Wikidata and Falcon 2.0 significantly outperforms the baseline. We worked on two different question answering datasets namely Simple-Question Dataset for Wikidata and LC-QuAD 2.0. 

### Baseline

We chose OpenTapioca as our baseline for entity and relation linking. OpenTapioca is available as web API and can provide Wikidata URIs for relations and entities. We are not aware of any other tool/approach that provides Wikidata entity linking.

### Results on SimpleQuestions dataset
[SimpleQuestion dataset ](https://github.com/askplatypus/wikidata-simplequestions)contains 6505 test questions which are answerable using Wikidata as underlying Knowledge Graph. We observe that for baseline, the values surprisingly are approximately zero for precision, recall, and F-score. We analysed the source of errors,  and  found  that  out  of  6505  questions,  only  246  have  entity  labels  in uppercase  letters.  Opentapioca  can  not  recognise  entities  and  link  any  entity written in lowercase letters. For remaining 246 questions, only 70 gives the correct answer for OpenTapioca (https://opentapioca.org/). On the other hand, Falcon 2.0 reports F-score 0.63 on the same dataset.
The code for opentapioca evaluation on Simplequestions can be found in evaluation/opentapioca.py. We implement a wrapper for Opentapioca API to send requests and retrive data quickly. The following function refers to the wrapper:
```
def open_tapioca_call(text): ...
```
Opentapioca returns a JSON object with annotations for mentions in the text. It outputs all the candidate entities for a mention along with the best ranked entity or property under the attribute 'best_qid'. We consider the best ranked entity as the output and compare it with the true entities in the dataset. You can evaluate using the following function (annotations refer to Opentapioca output and raw refers to the true entities as mentioned in the dataset):
```
def evaluate(annotations, raw): ...
```
### Results on LC-Quad 2.0
Given the limitations of OpenTapioca on Simplequestions dataset, we randomly selected 1000 questions from [LC-QuAD 2.0](https://figshare.com/articles/test_set_for_lcquad_2_0/8479052) to test the robustness of our tool on complex questions. OpenTapioca reports F-score 0.25 against Falcon 2.0 with F-score 0.68.
