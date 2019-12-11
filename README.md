# FALCON 2.0

Falcon 2.0 is a rule-based entity and relation linking tool over Wikidata. It leverages fundamental principles of the English morphology (e.g., N-Gram tiling and N-Gramsplitting) to accurately map entities and relations in short texts to resources in  Wikidata. 

# Implementation
To begin with, install the libraries stated in the requiremnts.txt file as follows:
```
pip install -r requirements.txt
```
The code for FALCON tool has three main aspects: elastic search, the algorithm and evaluation. 
## Elastic Search
Before we begin working with the Wikidata Dump, we first need to connect to an elasticsearch endpoint, and a Wikidata endpoint. The elasticsearch endpoint is used to interact with our cluster through the Elasticsearch API. To change your elasticsearch endpoint, makes changes in Elastic/searchIndex.py and Elastic/addIndex.py:
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
## Algorithm
main.py contains the code for automatic entity and relation linking to resources in Wikidata using rule-based learning. Falcon 2.0 uses the same approach for Wikidata knowledge graph as used in Falcon for DBpedia Spotlight. The rules that represent the English morphology are maintained in a catalog; a forward chaining inference process is performed on top of the catalog during the tasks of extractionand linking. Falcon 2.0 also comprises several modules that identify and link entities and relations to Wikidata knowledge graph. These modules implement POS  Tagging,  Tokenization  &  Compounding,  N-Gram  Tiling,  Candidate  ListGeneration, Matching & Ranking, Query Classifier, and N-Gram Splitting and are reused from the implementation of Falcon. 

## Evaluation
We empirically evaluated Falcon 2.0 on a question answering dataset tailored for Wikidata and Falcon 2.0 significantly outperforms the baseline. We worked on two different question answering datasets namely Simple-Question Dataset for Wikidata and LC-QuAD 2.0. SimpleQuestion dataset contains 6505 test questions which are answerable using Wikidata as underlying Knowledge Graph. We randomly selected 1000 questions from LC-QuAD 2.0 to test the robustness of our tool on complex questions. We chose OpenTapioca as our baseline for entity and relation linking. OpenTapioca is available as web API and can provide Wikidata URIs for relations and entities. We are not aware of any other tool/approach that provides Wikidata entity linking.

You may choose to run the tool for a single query or evalauate it on a dataset.
To run the tool on a single query (short text):
```
python3 main.py --q <query>
```

When evaluating a dataset, the program compares the entitites and relations extracted by Falcon 2.0 to that of the entitites and relations in the dataset for each question. To evaluate the tool on a dataset:
```
python3 main.py --d <path_To_Dataset>
```

We also evaluated OpenTapioca a
