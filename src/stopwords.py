# -*- coding: utf-8 -*-



def getStopWords():
    stopWords=[]
    with open('./data/stopwords-en.txt',encoding="utf8") as f:
        lines = f.readlines()
        for line in lines:
            stopWords.append(line.strip())
    return stopWords

def extract_stop_words_question(question,stopWordsList):
    stopWords=[]
    words=question.split(' ')
    words[0]=words[0].lower()
    for word in words:
        if word.strip() in stopWordsList:
            stopWords.append(word)
    return stopWords

def getComparisonWords():
    stopWords=[]
    with open('./data/comparsion_words.txt',encoding="utf8") as f:
        lines = f.readlines()
        for line in lines:
            stopWords.append(line.strip())
    return stopWords