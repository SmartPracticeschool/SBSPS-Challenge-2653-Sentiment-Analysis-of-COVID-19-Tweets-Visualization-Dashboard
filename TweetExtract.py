from tweepy import Stream
from tweepy import OAuthHandler
import json
import sqlite3
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from unidecode import unidecode
import time
from datetime import datetime
import re
import nltk
import string
from tweepy.streaming import StreamListener
import numpy as np
from nltk.stem.porter import *
from nltk.tokenize import word_tokenize
from string import punctuation 
from nltk.corpus import stopwords

analyzer = SentimentIntensityAnalyzer()

#consumer key, consumer secret, access token, access secret - Create twitter developer account, and add your key details here
ckey="smShEwIuc1sPSbdiGgJKMyF4c"
csecret="oUo8h7sM09smTL5RPv4c53iHVa2f0ZxMn63OvmDsfaD6chHw6Y"
atoken="1212233345955852289-xSdyVncAgRnQu4tZI0oHZQ2jpNXssO"
asecret="GDZHoFp8QbvMcv1cViTsJ9PhiNILP6K0upixom5cUHtXw"

stemmer = PorterStemmer()

class PreProcessTweets:
    def __init__(self):
        self._stopwords = set(stopwords.words('english') + list(punctuation) + ['AT_USER','URL', 'RT', "n't", "..."])
        
    def processTweets(self, tweet):
        tweet = tweet.lower() # convert text to lower-case
        tweet = re.sub('((www\.[^\s]+)|(https?://[^\s]+))', 'URL', tweet) # remove URLs
        tweet = re.sub('@[^\s]+', 'AT_USER', tweet) # remove usernames
        tweet = re.sub(r'#([^\s]+)', r'\1', tweet) # remove the # in #hashtag
        tweet = word_tokenize(tweet) # remove repeated characters (helloooooooo into hello)
        
        return [word for word in tweet if (word not in self._stopwords) & (len(word) > 2)]

conn = sqlite3.connect('twitter.db')
c = conn.cursor()

def create_table():
    try:
        c.execute("CREATE TABLE IF NOT EXISTS sentiment(unix REAL, rdtime DATETIME, tweet TEXT, cleanedtweet TEXT, \
                  sentiment REAL)")
        c.execute("CREATE INDEX fast_unix ON sentiment(unix)")
        c.execute("CREATE INDEX fast_rdtime ON sentiment(rdtime)")
        c.execute("CREATE INDEX fast_tweet ON sentiment(tweet)")
        c.execute("CREATE INDEX fast_sentiment ON sentiment(sentiment)")
        conn.commit()
    except Exception as e:
        print(str(e))
create_table()

class listener(StreamListener):

    def on_data(self, data):
        try:
            texttweet = ""
            data = json.loads(data)
            tweet = unidecode(data['text'])
            time_ms = data['timestamp_ms']
            rd_time_ms = datetime.utcfromtimestamp(int(time_ms)/1000).strftime('%Y-%m-%d %H:%M:%S')
            vs = analyzer.polarity_scores(tweet)
            tweetProcessor = PreProcessTweets()
            cleanedtweet = tweetProcessor.processTweets(tweet)
            texttweet = " ".join(cleanedtweet)
            expected_keys = ['user', 'location']
            sentiment = vs['compound']
            print(time_ms, rd_time_ms, tweet, texttweet, sentiment)
            #print(texttweet)
            c.execute("INSERT INTO sentiment (unix, rdtime, tweet, cleanedtweet, sentiment) VALUES (?, ?, ?, ?, ?)",
                  (time_ms, rd_time_ms, tweet, texttweet, sentiment))
            conn.commit()

        except KeyError as e:
            print("Error: ", str(e))
        return(True)

    def on_error(self, status):
        print(status)
while True:
    try:
        auth = OAuthHandler(ckey, csecret)
        auth.set_access_token(atoken, asecret)
        twitterStream = Stream(auth, listener())
        # Modify the word for which you are searching tweets, in this case used "covid19". As I am looking for tweets which contain covid19 word
        twitterStream.filter(track=["covid19"])
    except Exception as e:
        print(str(e))
        time.sleep(5)
