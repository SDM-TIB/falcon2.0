
import json
import io
import re
import csv

def isLineEmpty(line):
    return len(line) == 0

def read_dataset(filename):
    f = open(filename, 'r')
    rows=f.readlines()
    ans = []
    for q in rows:
    	q = q.rstrip('\n')
    	line = q.split("\t")
    	if not isLineEmpty(line):
    		ans.append(line)
    	# if(len(line)!=4):
    	# 	print(q," has more elements")
    f.close()
    return ans
    
if __name__== '__main__':
	read_dataset('simplequestions.txt')
