import spotlight
import evaluation


def get_annotations(text):
    try:
        annotations = spotlight.annotate('http://api.dbpedia-spotlight.org/en/annotate',
                                  text,
                                  confidence=0.4, support=20)
        return annotations
    except  Exception as ex:
        if  type(ex) is spotlight.SpotlightException:
            return []
        else:
            raise
        


def evaluate(questions):
    global p
    count=0
    correctEntities=0
    wrongEntities=0
    for question in questions:
        count=count+1
        print (count)
        entities=get_annotations(question[0])
        if len(entities)==0:
            wrongEntities=wrongEntities+1
            continue
       # print(entities)
        #print(question[3])
        if len(question[3]) == 0:
            p=p+1
            continue
        for entity in question[3]:
            numberSystemEntities=len(entities)
            if entity in [tup['URI'] for tup in entities]:
                p=p+(1/numberSystemEntities)
                print("hi")
                correctEntities=correctEntities+1
            else:
                print("bye")
                wrongEntities=wrongEntities+1
    
    print("Correct Entities:",correctEntities)
    print("Entities:")
    print((correctEntities*100)/(correctEntities+wrongEntities))
    print(correctEntities+wrongEntities)
    print("p:")
    print(p)
    
    
    
if __name__ == "__main__":
    global p
    p=0
    questions=evaluation.read_QALD5()
    evaluate(questions[:50])