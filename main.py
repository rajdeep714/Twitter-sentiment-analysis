from flask import Flask, render_template, request
import tweepy
import pandas as pd
from textblob import TextBlob
import re

app = Flask(__name__)


@app.route('/sentiment', methods=['GET', 'POST'])
def sentiment():
    userid = request.form.get('userid')
    hashtag = request.form.get('hashtag')

    if userid == "" and hashtag == "":
        error = "Please enter any one value"
        return render_template('index.html', error=error)

    if not userid == "" and not hashtag == "":
        error = "Both entry not allowed"
        return render_template('index.html', error=error)

    # ======================Insert Twitter API Here==========================
    consumerKey = ""
    consumerSecret = ""
    accessToken = ""
    accessTokenSecret = ""
    # =====================Insert Twitter API Here===========================

    authenticate = tweepy.OAuthHandler(consumerKey, consumerSecret)
    authenticate.set_access_token(accessToken, accessTokenSecret)
    api = tweepy.API(authenticate, wait_on_rate_limit=True)

    def cleanTxt(text):
        text = re.sub(r'@[A-Za-z0–9]+', '', text)  # Removing @mentions
        text = re.sub(r'#', '', text)  # Removing '#' hashtag
        text = re.sub(r'RT\s+', '', text)  # Removing RT
        text = re.sub(r'https?://\S+', '', text)  # Removing hyperlink
        text = re.sub('&amp;', '&', text)  # Replacing special characters with symbols
        text = re.sub('&lt;', '<', text)
        text = re.sub('&gt;', '>', text)
        text = re.sub('&quot;', '"', text)
        text = re.sub('&apos;', '`', text)
        return text

    def getSubjectivity(text):
        return TextBlob(text).sentiment.subjectivity

    def getPolarity(text):
        return TextBlob(text).sentiment.polarity

    def getAnalysis(score):
        if score < 0:
            return 'Negative'
        elif score == 0:
            return 'Neutral'
        else:
            return 'Positive'

    if userid == "":
        # hashtag coding
        posts = tweepy.Cursor(api.search_tweets, lang='en', q=hashtag).items(100)
        twitter = pd.DataFrame([tweet.text for tweet in posts], columns=['Tweets'])
        if twitter.empty:
            error = "No tweets found with given HashTag"
            return render_template('index.html', error=error)
    else:
        # user coding
        try:
            posts = api.user_timeline(screen_name=userid, count=100, tweet_mode="extended")
        except tweepy.errors.NotFound:
            error = "No user found with given UserID"
            return render_template('index.html', error=error)
        twitter = pd.DataFrame([tweet.full_text for tweet in posts], columns=['Tweets'])

    twitter['Tweets'] = twitter['Tweets'].apply(cleanTxt)
    twitter['Subjectivity'] = twitter['Tweets'].apply(getSubjectivity)
    twitter['Polarity'] = twitter['Tweets'].apply(getPolarity)
    twitter['Analysis'] = twitter['Polarity'].apply(getAnalysis)

    positive = twitter.loc[twitter['Analysis'].str.contains('Positive')]
    negative = twitter.loc[twitter['Analysis'].str.contains('Negative')]
    neutral = twitter.loc[twitter['Analysis'].str.contains('Neutral')]

    positive_per = round((positive.shape[0] / twitter.shape[0]) * 100, 1)
    negative_per = round((negative.shape[0] / twitter.shape[0]) * 100, 1)
    neutral_per = round((neutral.shape[0] / twitter.shape[0]) * 100, 1)

    return render_template('sentiment.html', name=("@" + userid, hashtag)[userid == ""], positive=positive_per,
                           negative=negative_per,
                           neutral=neutral_per)


@app.route('/')
def home():
    return render_template('index.html')


app.run(debug=True)
