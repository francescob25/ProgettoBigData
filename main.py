from pyspark import SparkConf, SparkContext
from pyspark.sql import SparkSession

import os
import sys

os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

spark = SparkSession.builder.appName("IMDB_Sentiment").master("local[*]").getOrCreate() # tutte le query fatte qua le eseguiamo sul cluster
conf_spark = SparkConf()
conf_spark.setAppName("IMDB_Sentiment").set("spark.executor.memory", "4g")
sc = spark.sparkContext #8 core = 8 worker -> crea una versione locale con numero di thread pari a numero di core della macchina
sc.setLogLevel("ERROR")
rdd_pyspark = sc.textFile("IMDBDataset.csv")
reviews = rdd_pyspark.map(lambda x: x.rsplit(",", 1))

positiveReviews = rdd_pyspark.filter(lambda x: x[1] == "positive")
print(positiveReviews.count())