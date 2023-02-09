#import pandas as pd
from pyspark import SparkConf
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
from pyspark.sql import SparkSession
import re
import os
import sys


############################### CONFIGURAZIONE ########################################

os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable
#recensioni=pd.read_csv("IMDBDataset.csv")
spark = SparkSession.builder.master("local[*]").appName("IMDB_Sentiment").getOrCreate() # tutte le query fatte qua le eseguiamo sul cluster
conf_spark = SparkConf()
conf_spark.setAppName("IMDB_Sentiment").set("spark.executor.memory", "4g")
sc = spark.sparkContext #8 core = 8 worker -> crea una versione locale con numero di thread pari a numero di core della macchina
sc.setLogLevel("ERROR")
rdd_pyspark = sc.textFile("IMDBDataset.csv") #lista di stringhe
stopwords = sc.textFile("stopwords.txt").collect() #lista di stringhe
reviews = rdd_pyspark.map(lambda x: x.rsplit(',', 1)).cache() ## lista di liste


# ########################### PREPROCESSING DEI DATI ################################

def processWord(word: str):
    return re.sub("[^A-Za-z0-9]+", "", word.lower())

def splitAndProcess(words: str):
    return [processWord(word) for word in words.split()]


reviews = reviews.map(lambda x: [x[0].replace("<br /><br />", " "), x[1]]) #da un'analisi fatta le recensioni possono avere solo doppi break
namesOfColumns = reviews.first()
reviews = reviews.filter(lambda x: x != namesOfColumns)

####################### RECENSIONI POSITIVE E NEGATIVE ############################

def filterByPositive(reviews):
    return reviews.filter(lambda x: x[1] == 'positive')

def filterByNegative(reviews):
    return reviews.filter(lambda x: x[1] == 'negative')

####################### RECENSIONI PIU LUNGHE/CORTE ############################

def orderByLongReviews(reviews):
    return reviews.sortBy(lambda x: len(x[0]), False)

def orderByShortReviews(reviews):
    return reviews.sortBy(lambda x: len(x[0]), True)

############################ PAROLE CHE SI RIPETONO PIU VOLTE ############################

def wordsMostFrequently(reviews):
    countsRDD = reviews.flatMap(lambda x: splitAndProcess(x[0])).map(lambda word:(word, 1)).reduceByKey(lambda a,b: a+b)
    orderedRDD = countsRDD.sortBy(lambda x: x[1], False).map(lambda x: x[0])
    return orderedRDD.filter(lambda x: x not in stopwords)

################################# RECENSIONI CON SPOILER ##################################

def filterBySpoilers(reviews):
    return reviews.filter(lambda x: (x[0].upper().count("SPOILER") - x[0].upper().count("NO SPOILER")) > 0)

def filterByNoSpoilers(reviews):
    return reviews.filter(lambda x: (x[0].upper().count("SPOILER") - x[0].upper().count("NO SPOILER")) <= 0)

###################################### CERCA PER PAROLA ###################################

def filterByWord(reviews,word):
    return reviews.filter(lambda x: re.search(r"\b"+word+r"\b", str(x[0]), re.IGNORECASE))

####################### PAROLE CHE SI RIPETONO PIU VOLTE IN POS./NEG. ######################

def mostFrequentlyPositiveWords(reviews):
    positiveReviews = filterByPositive(reviews)
    return wordsMostFrequently(positiveReviews)

def mostFrequentlyNegativeWords(reviews):
    negativeReviews = filterByNegative(reviews)
    return wordsMostFrequently(negativeReviews)

############################ PREDICI SENTIMENT CON MLIB ######################################

from pyspark.ml.feature import CountVectorizer, RegexTokenizer, StopWordsRemover
from pyspark.sql.functions import col, when, isnull
from pyspark.ml.classification import NaiveBayes

def predict_sentiment(review):
    global reviews

    regex_tokenizer = RegexTokenizer(inputCol="review", outputCol="words", pattern="\\W")
    reviews_df = reviews.toDF(namesOfColumns).cache()

    # print(sum([reviews_df.filter(isnull(c)).count() for c in reviews_df.columns]))
    # print(reviews_df.filter(reviews_df[1] == 'positive').count())
    # print(reviews_df.filter(reviews_df[1] == 'negative').count())

    raw_words = regex_tokenizer.transform(reviews_df)

    #print("Output regextokenizer:")
    #print(raw_words.select("words").show(truncate=False))

    remover = StopWordsRemover(inputCol="words", outputCol="filtered")
    words_df = remover.transform(raw_words)

    #print("Output stopwordsremover:")
    #print(words_df.select("filtered").show(truncate=False))

    cv = CountVectorizer(inputCol="filtered", outputCol="features")
    model = cv.fit(words_df)
    countVectorizer_train = model.transform(words_df)
    countVectorizer_train = countVectorizer_train.withColumn("label", when(col('sentiment') == "positive", 1).otherwise(0))

    #print("Output countvectorizer:")
    #print(countVectorizer_train.select("features").show(truncate=False))

    (reviews_train, reviews_test) = countVectorizer_train.randomSplit([0.7, 0.3], seed=0)

    nb = NaiveBayes(modelType="multinomial", labelCol="label", featuresCol="features")
    nbModel = nb.fit(reviews_train)
    nb_predictions = nbModel.transform(reviews_test)

    #evaluator = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="accuracy")
    #nb_accuracy = evaluator.evaluate(nb_predictions)
    #print("Accuratezza NaiveBayes = %g"% (nb_accuracy))

    # tokenizzazione della recensione
    tokenized_review = regex_tokenizer.transform(spark.createDataFrame([(review,)], ["review"]))
    # rimozione stopwords
    filtered_review = remover.transform(tokenized_review)
    # creazione features usando il modello allenato a partire dal CountVectorizer
    features = model.transform(filtered_review)
    # predizione sentiment usando il modello NaiveBayes
    prediction = nbModel.transform(features).select("prediction").collect()[0]["prediction"]
    return prediction




