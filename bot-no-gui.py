import tweepy
import os
import sys
import time
from datetime import datetime
import random
import json
from credentials import *
from colorama import Fore, Style
from config import INCLUDE_RETWEETS, SLEEP_TIME_PER_TWEET, SLEEP_TIME_PER_USER, TWEETS_PER_USER, PALS_TO_TAG, DEFAULT_AMOUNT_TO_TAG, ACCOUNT_NAME, SOL_WALLET, ETH_WALLET, APPEND_RANDOM_EMOTE, EMOTES, IGNORE_AFTER, ENABLE_DEBUG

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())

prefix = Fore.WHITE + '[' + Fore.CYAN + 'GiveawayBot' + Fore.WHITE + '] ' + Style.RESET_ALL
prefix_info = Fore.WHITE + '[' + Fore.CYAN + 'GiveawayBot' + Fore.WHITE + '] ' + Fore.YELLOW
prefix_error = Fore.WHITE + '[' + Fore.CYAN + 'GiveawayBot' + Fore.WHITE + '] ' + Fore.LIGHTRED_EX
seperator = Style.RESET_ALL + '\n====================================================================================================================\n'

# Function to clear terminal
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def setupFolder():
    if not os.path.exists('tweets'):
        os.makedirs('tweets')


def save_tweet(name, content):
    filename = 'tweets/' + str(name) + '.json'
    with open(filename, 'w') as file_object:
        json.dump(content, file_object)

def followUser(username):
    user = api.get_user(screen_name=username)
    if user.get('following'):
        print(prefix + 'Already following @' + username)
    else:
        try:
            api.create_friendship(user_id=user.get('id'))
            print(prefix + 'Following @' + username)
        except:
            print(prefix_error + 'Could not follow user ' + username)

def joinGiveaway(tweet):
    already_joined = False
    needs_rt = False
    needs_like = False
    needs_tag = False
    needs_follow = False
    needs_wlt = False
    comment = ''
    separator = ', '
    tagSeparator = ' '
    tweet_content = tweet.get('full_text')
    tweet_content_low = tweet_content.lower()

    #Skip tweet if it needs a proof (screenshot)
    if 'proof' in tweet_content_low:
        print(seperator + prefix_info + 'Skipping tweet because its need a proof for notifications')
        print(prefix_info  + 'This function is comming in a later version of the bot' + separator)
        return

    #Skip tweet if its older than X hours
    creationDateUnix = time.mktime(datetime.strptime(tweet.get('created_at'),'%a %b %d %H:%M:%S +0000 %Y').timetuple())
    todayUnix = datetime.utcnow().timestamp()
    targetTime = todayUnix - (IGNORE_AFTER * 60 * 60)
    if(targetTime > creationDateUnix):
        print(prefix_info  + 'Skipping tweet because its older than ' + str(IGNORE_AFTER) + ' hours\n')
        return

    print(seperator)
    print(Fore.BLUE + 'Tweet-URL: ' + Style.RESET_ALL + 'https://twitter.com/' + tweet.get('user')['screen_name'] + '/status/' + tweet.get('id_str'))
    print(Fore.BLUE + 'Tweet-Content: \n' + Style.RESET_ALL + tweet_content)

    if 'follow' in tweet_content_low and '@' in tweet_content_low:
        if 'winner ' not in tweet_content_low:
            needs_follow = True
            parts = tweet_content.split('@')

            for key in parts:
                if key != parts[0]:
                    temp = key.split()
                    name = temp[0]
                    followUser(name)
                

    if 'like' in tweet_content_low or '♥️' in tweet_content_low:
        if tweet.get('favorited'):
            already_joined = True
            print(prefix + 'Already liked the tweet' + Style.RESET_ALL)
        else:
            needs_like = True
            api.create_favorite(tweet.get('id'))
            print(prefix + 'Liked the tweet' + Style.RESET_ALL)
        
    if 'rt ' in tweet_content_low or 'retweet' in tweet_content_low or '+rt' in tweet_content_low or 'rt+' in tweet_content_low or 'rt,' in tweet_content_low or 'rt&' in tweet_content_low or ' rt' in tweet_content_low:
        if tweet.get('retweeted'):
            already_joined = True
            print(prefix + 'Already retweeted the tweet...' + Style.RESET_ALL)
        else:
            needs_rt = True
            api.retweet(tweet.get('id'))
            print(prefix + 'Retweeted the tweet' + Style.RESET_ALL)

    if 'tag ' in tweet_content_low or 'mention' in tweet_content_low or 'friends' in tweet_content_low:
        needs_tag = True
        if 'tag 3' in tweet_content_low:
            random_friends = random.sample(PALS_TO_TAG, 3)
        elif 'tag 2' in tweet_content_low:
            random_friends = random.sample(PALS_TO_TAG, 2)
        elif 'tag a' in tweet_content_low:
            random_friends = random.sample(PALS_TO_TAG, 1)
        else:
            random_friends = random.sample(PALS_TO_TAG, DEFAULT_AMOUNT_TO_TAG)
        
        comment = comment + str(tagSeparator.join(random_friends)) + '\n\n'

        print(prefix +  'Selected ' + separator.join(random_friends) + ' to tag' + Style.RESET_ALL)
    
    if 'drop ' in tweet_content_low and ('wallet' in tweet_content_low or 'address' in tweet_content_low):
        #Wallet
        wlt_type = 'no'
        if 'sol' in tweet_content_low or '$sol' in tweet_content_low or 'solana':
            needs_wlt = True
            comment = comment + SOL_WALLET
            wlt_type = 'SOL'
        elif 'eth' in tweet_content_low or '$eth' in tweet_content_low or 'ethereum':
            needs_wlt = True
            comment = comment + ETH_WALLET
            wlt_type = 'ETH'
        else:
            needs_wlt = False
            wlt_type = 'no'
        
        print(prefix + 'Selected ' + wlt_type + ' wallet')


    if needs_like == False and needs_rt == False and needs_tag == False and needs_follow == False and needs_wlt == False and already_joined == False:
        print('\n\n' + prefix_info + 'Skipping tweet because its not a giveaway' + Style.RESET_ALL)
    else:
        if already_joined:
            print('\n' + prefix_info + 'Already joined this giveaway')
        else:
            if APPEND_RANDOM_EMOTE:
                if needs_follow and needs_like and needs_rt:
                    comment = comment + ' ' + random.choice(EMOTES)

            print(prefix + 'Posting comment: ' + comment)
            api.update_status(status=comment, in_reply_to_status_id=tweet.get('id') , auto_populate_reply_metadata=True)
            print(prefix + Fore.LIGHTGREEN_EX + 'Successfull joined the giveaway' + Style.RESET_ALL)
            if(ENABLE_DEBUG):
                dataToSave = {
                    'url': 'https://twitter.com/' + tweet.get('user')['screen_name'] + '/status/' + tweet.get('id_str'),
                    'content': tweet_content,
                    'needsLike': needs_like,
                    'needsRetweet': needs_rt,
                    'needsFollow': needs_follow,
                    'needsTag': needs_tag,
                    'needsWallet': needs_wlt,
                    'comment': comment
                }
                save_tweet(tweet.get('id_str'), dataToSave)

    print(seperator + '\n')
    time.sleep(SLEEP_TIME_PER_TWEET)


def checkTweets():
    for data in tweepy.Cursor(api.get_friends, screen_name=ACCOUNT_NAME).pages():
        followers = data.get('users')
        for follower in followers:
            id = follower.get('id')
            tweets = api.user_timeline(user_id=id, count=TWEETS_PER_USER, tweet_mode="extended")

            for tweet in tweets:
                if INCLUDE_RETWEETS:
                    joinGiveaway(tweet)
                else:
                    if tweet.get('full_text').startswith('RT @'):
                        print(prefix + Fore.YELLOW + 'Skipping retweeted tweet...\n' + Style.RESET_ALL)
                    else:
                        joinGiveaway(tweet)
            print(prefix + 'Checked last ' + str(TWEETS_PER_USER) + ' tweets from ' + follower.get('screen_name'))
            print(prefix + 'Waiting ' + str(SLEEP_TIME_PER_USER) + ' seconds before checking next user.\n' + Style.RESET_ALL)
            time.sleep(SLEEP_TIME_PER_USER)


if __name__ == '__main__':
    clear()

    if(ENABLE_DEBUG):
        setupFolder()
    
    try:
        checkTweets()
    except KeyboardInterrupt:
        print(prefix_error + 'Bot exited by user...' + Style.RESET_ALL)
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)