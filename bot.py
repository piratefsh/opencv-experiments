import tweepy, re, requests, random, traceback, time
from secrets import *
import tests as t
from bs4 import BeautifulSoup
from tweepy.streaming import StreamListener
from myAPI import *


class listener_tweeter(StreamListener):

    # override on_status to pass data from on_data method of tweepy's StreamListener
    def on_status(self, status):
        print '{} said: "{}"'.format(status.user.screen_name, status.text)

        # ignore retweets or tweets from self
        if status.retweeted or ( status.user.screen_name.lower() == 'professorset' ):
            return

        img_str = None

        # parse tweet for url
        # if tweeted phrase contains "sets or not", will color based on presence/absence of sets
        # without outlining specific sets
        try:
            tweet_url = re.search(r'https:.*\b', status.text).group(0)
            with_sets_outlined = (False if re.search(r'sets or not', status.text) else True)
            text, img_str = solve_tweeted_set(tweet_url, with_sets_outlined=with_sets_outlined)
            #print text

        #ignore tweets with no image
        except AttributeError:
            text = "You forgot a picture, {} #whoops #howembarrassing".format(status.user.name)
            n = random.randint(0, 140-len(text))
            text += '!'*n

        response_text = '.@{} {}'.format(status.user.screen_name, text)
        #print response_text

        try:
            response = api.retweet(id=status.id)

        except tweepy.error.TweepError:
            traceback.print_exc()

        # try to avoid posting tweets out of order (should be retweet, then response tweet)
        for i in xrange(10):
            if response:
                send_tweet( response_text, response_id=status.id, media_str=img_str )
                return
            else:
                time.sleep(10)

        # but ultimately just send it anyway
        send_tweet( response_text, response_id=status.id, media_str=img_str )


    def on_error(self, status_code):
        print 'Error: {}'.format(status_code)

    def on_exception(self, exception):
        print 'Exception: {}'.format(exception)
        return



#def find_mentions():
    #mentions = api.mentions_timeline(count=5)
#
    #for mention in mentions[::-1]:
        #print '{} said: "{}"'.format(mention.user.screen_name, mention.text)
#
        ## parse tweet for url
        #try:
            #tweet_url = re.search(r'https:.*\b', mention.text).group(0)
            #text = solve_tweeted_set(tweet_url)
        #except AttributeError:
            ## ignore tweets with no image
            #text = "You forgot a picture, {} #whoops #howembarrassing".format(mention.user.name)
            ##api.update_status( text, in_reply_to_status_id = mention.id )
            #n = random.randint(0, 140-len(text))
            #text += '!'*n
#
        #status_text = '.@{} {}'.format(mention.user.screen_name, text)
#
        #try:
            #api.retweet(id=mention.id)
        #except tweepy.error.TweepError:
            #traceback.print_exc()
            #continue
#
        #send_tweet( status_text, response_id=mention.id )



def solve_tweeted_set(tweet_url, with_sets_outlined=True):
    tweet_content = requests.get(tweet_url).content

    # scrape tweet HTML string for image url
    soup = BeautifulSoup(tweet_content, 'lxml')
    img_url = soup.find('meta', attrs={'property': 'og:image'})['content']
    #print img_url

    # find Sets
    kwargs = {'path_is_url': True, 'pop_open': False}
    kwargs['draw_contours'] = (True if with_sets_outlined else False)
    kwargs['sets_or_no'] = (False if with_sets_outlined else True)
    #print "about to play"
    num_sets, initial_img_str = t.play_game(img_url, **kwargs)
    #print num_sets

    # send string with media_data (rather than media) tag because it is base64 encoded
    img_str = 'media_data={}'.format(initial_img_str)

    text = ("Whoa! {} sets #craycray".format(num_sets) if num_sets \
           else "No sets #bummer #sadface")

    img_str = (img_str if num_sets else None)

    return (text, img_str)



def send_tweet(text, response_id=None, media_str=None):
    try:
        text = text[:140]
        d_arguments = {'status': text}

        if response_id: d_arguments['in_reply_to_status_id'] = response_id

        if media_str:
            upload = api.media_upload(file=media_str, filename='filenames_are_for_dweebs')
            #upload = api.media_upload(filename='tmp.jpeg')
            d_arguments['media_ids'] = [upload.media_id_string]

        api.update_status(**d_arguments)

    except:
        traceback.print_exc()
        pass



def listen():
    my_listener = listener_tweeter()
    stream = tweepy.Stream(auth, my_listener)
    stream.userstream(_with='user')



if __name__ == "__main__":
    auth = tweepy.OAuthHandler(C_KEY, C_SECRET)
    auth.set_access_token(A_TOKEN, A_TOKEN_SECRET)
    api = myAPI(auth, timeout=600)
    #api = tweepy.API(auth)

    listen()
