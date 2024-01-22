import pytesseract
import shutil
import os
import random
from pdf2image import convert_from_path
from PIL import Image
#import cv2 as cv
import matplotlib.pyplot as plt
import spacy
import json
import pandas as pd
import pathlib

path=pathlib.Path(__file__).parents[0].joinpath('pdfFiles')
pathTxt=pathlib.Path(__file__).parents[0].joinpath('outFiles')

print(path)
fileNames=os.listdir(path)
print(fileNames)

eventData=pd.DataFrame(columns=["pdfFile", "txtFile", "eventDate","eventPlace","locList","geoEvents"])
nlp = spacy.load('ro_core_news_lg')
numFiles=0
numProcFiles=1
for fileName in fileNames:

  textFileName=fileName[:-3]+'txt'
  if os.path.exists(pathTxt.joinpath(textFileName)):
    continue

  print("Number of processed files: %d" % numProcFiles)
  numProcFiles=numProcFiles+1
  try:
    images = convert_from_path(path.joinpath(fileName))
  except Exception:
    continue


  f = open(pathTxt.joinpath(textFileName), 'w')


  jsonData = {}
  locList=[]
  eventsList=[]
  k=0
  okPV=0
  semDate=0
  semGPE=0
  for img in images:
    #img.show()
    #display(img)
    #print(k)
    #img.save(fileName[:-4]+'_'+str(k)+'.bmp')
    extractedInformation = pytesseract.image_to_string(img)
    f.write(extractedInformation)

    if (k==0):
      splitFirstLines=extractedInformation.splitlines()[1:15]

      for line in splitFirstLines:
        #print(type(line))
        #print(line.upper())
        if 'VERBAL' in line.upper():
          okPV=1
          break
      if okPV:
        jsonData['pdfFile']=fileName
        jsonData['txtFile']=textFileName
        jsonData['eventDate']=''
        jsonData['eventPlace']=''

        lengths = list(map(len, splitFirstLines))
        res = sum(lengths)
        firstLines=extractedInformation[:res+10]
        semDate=0
        semGPE=0
        doc = nlp(firstLines)
        for word in doc.ents:
          if (word.label_=="DATETIME") and (semDate==0):
            #print(word.text)
            jsonData['eventDate']=word.text
            semDate=1
          if ((word.label_=="GPE")or(word.label_=="LOC")) \
          and (word.text!="ROMANIA") and (semGPE==0):
            #print(word.text)
            place=word.text
            jsonData['eventPlace']=place.split('\n', 1)[0]
            semGPE=1
          if (semDate==1) and  (semGPE==1):
            break
        if (semGPE==0):
          #print("HERE")
          jsonData['eventPlace']=splitFirstLines[2]
      k=k+1

    docAll = nlp(extractedInformation)
    for word in docAll.ents:
      if ((word.label_=="GPE")or(word.label_=="LOC")) \
          and (word.text!="ROMANIA") and (word.text!="PRAHOVA") \
          and (semGPE==0):
          place=word.text
          jsonData['eventPlace']=place.split('\n', 1)[0]
          semGPE=1
      if (word.label_=="LOC") or (word.label_=="GPE"):
        locList.append(word.text)
      if (word.label_=="EVENT"):
        eventsList.append(word.text)
      if (semDate==0):
        if (word.label_=="DATETIME"):
          jsonData['eventDate']=word.text
          semDate=1

  f.close()
  if bool(jsonData) and (okPV==1):
    numFiles=numFiles+1
    jsonData['locations']=locList
    jsonData['events']=eventsList
    #with open(fileName[:-3]+"json", "w") as outfile:
    # json.dump(jsonData, outfile)
    eventData.loc[len(eventData)]=[jsonData['pdfFile'],\
                                  jsonData['txtFile'],\
                                  jsonData['eventDate'],\
                                  jsonData['eventPlace'],\
                                  jsonData['locations'],\
                                  jsonData['events']]
  if (numFiles%50==0):
    #print(eventData)
    eventData.to_csv('eventsDB_'+str(numFiles)+'.csv')

