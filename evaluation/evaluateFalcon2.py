
import json
import io
import re
import csv

def isLineEmpty(line):
	return len(line) == 0

def read_dataset(filename):
	f = open(filename, 'r',encoding='utf-8')
	rows=f.readlines()
	ans = []
	for q in rows:
		q = q.rstrip('\n')
		line = q.split("\t")
		if 'R' in line[1]:
			line[1].replace('R','P')
		if not isLineEmpty(line):
			ans.append([line[3],[line[0]],[line[1]]])
		# if(len(line)!=4):
		# 	print(q," has more elements")
	f.close()
	return ans

def read_test_set():
    data = json.load(io.open('../datasets/webqsp.test.entities.with_classes.json', encoding='utf-8')) 
    questions=[[question['utterance'],question['entities']] for question in data]
    return questions


if __name__== '__main__':
	read_dataset('simplequestions.txt')
