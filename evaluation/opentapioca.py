# -*- coding: utf-8 -*-

import requests
import csv
import evaluation


def open_tapioca_call(text):
    print(text)
    text = text.replace('?','')

    headers = {
        'Accept': 'application/json',
    }
    url = "https://opentapioca.org/api/annotate"
    payload = 'query='

    data = text.split(" ");
    for s in data:
        payload=payload+s
        payload+='+'
    payload+='%3F'

    response = requests.request("POST", url, data=payload, headers=headers)
    if response.status_code == 200:
        result=response.json()
        print(result)
        if ans in result[annotations]:
            return ans
        else:
            return ""
    else:
        temp=open_tapioca_call(text)
        return temp


if __name__ == "__main__":
    print(open_tapioca_call("Where did roger marquis die"))
 
