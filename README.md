# FALCON 2.0

Falcon 2.0 is a rule-based entity and relation linking tool over Wikidata. It leverages fundamental principles of the English morphology (e.g., N-Gram tiling and N-Gramsplitting) to accurately map entities and relations in short texts to resources in  Wikidata. 

# Usage

To run the tool, you need to connect to an elasticsearch endpoint, and a Wikidata endpoint.
To change Wikidata endpoint, make changes in main.py
```
wikidataSPARQL=""
```
To change elastic search endpoint, makes changes in Elastic/searchIndex.py:
```
es = Elasticsearch(['http://localhost:9200'])
```

To run the tool on a short text:
```
python3 main.py --q <query>
```

To evaluate the tool on a dataset:
```
python3 main.py --d <path_To_Dataset>
```

