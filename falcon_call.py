import csv
import requests


headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}


def falcon2_call(text,mode='short'):
    try:
        text=text.replace('"','')
        text=text.replace("'","")
        if mode=='short':
            url = 'https://labs.tib.eu/falcon/falcon2/api?mode=short&db=1'
            entities_wikidata=[]
            entities_db=[]
            payload = '{"text":"'+text+'"}'
            r = requests.post(url, data=payload.encode('utf-8'), headers=headers)
            if r.status_code == 200:
                response=r.json()
                #print(response)
                for result in response['entities_wikidata']:
                    entities_wikidata.append(result[0])
                for result in response['entities_dbpedia']:
                    entities_db.append(result[0])
            else:
                r = requests.post(url, data=payload.encode('utf-8'), headers=headers)
                if r.status_code == 200:
                    response=r.json()
                    for result in response['entities_wikidata']:
                      entities_wikidata.append(result[0])
                    for result in response['entities_dbpedia']:
                      entities_db.append(result[0])
            if len(entities_wikidata)>0:
              entities_wikidata=entities_wikidata[0].replace('<','').replace('>','')
            if len(entities_db)>0:
              entities_db=entities_db[0]
            
            return entities_wikidata,entities_db
        else:
            url = 'https://labs.tib.eu/falcon/falcon2/api?mode=long&db=1'
            entities_wikidata=[]
            entities_db=[]
            payload = '{"text":"'+text+'"}'
            r = requests.post(url, data=payload.encode('utf-8'), headers=headers)
            if r.status_code == 200:
                response=r.json()
                #print(response)
                return response
                for result in response['entities_wikidata']:
                    entities_wikidata.append(result)
                for result in response['entities_dbpedia']:
                    entities_db.append(result)
            else:
                r = requests.post(url, data=payload.encode('utf-8'), headers=headers)
                if r.status_code == 200:
                    response=r.json()
                    return response
                    for result in response['entities_wikidata']:
                      entities_wikidata.append(result)
                    for result in response['entities_dbpedia']:
                      entities_db.append(result)
            if len(entities_wikidata)>0:
              entities_wikidata[0][1]=entities_wikidata[0][1].replace('<','').replace('>','')
            if len(entities_db)>0:
              entities_db=entities_db
            
            return entities_wikidata,entities_db
           

    except:
        raise
        return -1  
        
def bioFalcon_call(text, mode='short'):
    text=text.replace('"','')
    text=text.replace("'","")
    if mode=='short':
        url = 'https://labs.tib.eu/sdm/biofalcon/api?mode='+mode
        payload = '{"text":"'+text+'"}'
        try:
            r = requests.post(url, data=payload.encode('utf-8'), headers=headers)
            if r.status_code == 200:
                response=r.json()
                if len(response['entities']) > 1:
                    return response['entities'][1][0]
                else:
                    return ""
            else:
                return ""
        except:
            raise
            return ""
    else:
        url = 'https://labs.tib.eu/sdm/biofalcon/api?mode='+mode
        payload = '{"text":"'+text+'"}'
        try:
            r = requests.post(url, data=payload.encode('utf-8'), headers=headers)
            if r.status_code == 200:
                response=r.json()
                return response
        except:
            raise
            return ""