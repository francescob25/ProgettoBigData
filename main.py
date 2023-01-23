#import pandas as pd
from pyspark import SparkConf, SparkContext
from pyspark.sql import SparkSession
import re
import os
import sys


############################### CONFIGURAZIONE ########################################

os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable
#recensioni=pd.read_csv("IMDBDataset.csv")
spark = SparkSession.builder.appName("IMDB_Sentiment").master("local[*]").getOrCreate() # tutte le query fatte qua le eseguiamo sul cluster
conf_spark= SparkConf()
conf_spark.setAppName("IMDB_Sentiment").set("spark.executor.memory", "4g")
sc = spark.sparkContext #8 core = 8 worker -> crea una versione locale con numero di thread pari a numero di core della macchina
sc.setLogLevel("ERROR")
rdd_pyspark = sc.textFile("IMDBDataset.csv") #lista di stringhe
stopwords = sc.textFile("stopwords.txt").collect() #lista di stringhe
reviews = rdd_pyspark.map(lambda x: x.rsplit(',',1)) ## lista di liste

########################### PREPROCESSING DEI DATI ################################

def processWord(word: str):
    return re.sub("[^A-Za-z0-9]+", "", word.lower())

def splitAndProcess(words: str):
    return [processWord(word) for word in words.split()]

reviews = reviews.filter(lambda x: str(x[0]).__contains__("<br />")).map(lambda x: [x[0].replace("<br /><br />", " "),x[1]]) #da un'analisi fatta le recensioni possono avere solo doppi break

####################### RECENSIONI POSITIVE E NEGATIVE ############################

def filterByPositive(reviews):
    return reviews.filter(lambda x: x[1] == 'positive')

def filterByNegative(reviews):
    return reviews.filter(lambda x: x[1] == 'negative')

####################### RECENSIONI PIU LUNGHE/CORTE ############################

def orderByLongReviews(reviews):
    return reviews.sortBy(lambda x: len(x[0]), False).map(lambda x: x[0])

def orderByShortReviews(reviews):
    return reviews.sortBy(lambda x: len(x[0]), True).map(lambda x: x[0])

############################ PAROLE CHE SI RIPETONO PIU VOLTE ############################

def wordsMostFrequently(reviews):
    countsRDD = reviews.flatMap(lambda x: splitAndProcess(x[0])).map(lambda word:(word, 1)).reduceByKey(lambda a,b: a+b)
    orderedRDD = countsRDD.sortBy(lambda x: x[1], False).map(lambda x: x[0])
    return orderedRDD.filter(lambda x: x not in stopwords)

################################# RECENSIONI CON SPOILER ##################################

def filterBySpoilers(reviews):
    return reviews.filter(lambda x: str(x[0]).upper().__contains__("*SPOILER")).map(lambda x: x[0])

def filterByNoSpoilers(reviews):
    return reviews.filter(lambda x: not(str(x[0]).upper().__contains__("*SPOILER"))).map(lambda x: x[0])

###################################### CERCA PER PAROLA ###################################

def filterByWord(reviews,word):
    return reviews.filter(lambda x: re.search(r"\b"+word+r"\b", str(x[0]), re.IGNORECASE)).map(lambda x: x[0])

####################### PAROLE CHE SI RIPETONO PIU VOLTE IN POS./NEG. ######################

def mostFrequentlyPositiveWords(reviews):
    positiveReviews = filterByPositive(reviews)
    return wordsMostFrequently(positiveReviews)

def mostFrequentlyNegativeWords(reviews):
    negativeReviews = filterByNegative(reviews)
    return wordsMostFrequently(negativeReviews)

############################ PREDICI SENTIMENT CON MLIB ######################################

