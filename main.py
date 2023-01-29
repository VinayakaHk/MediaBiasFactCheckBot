import praw
import re
import json
import time


def print_text(obj):
    if obj['credibility'] == 'no credibility rating available':
        text = f"""|Metric|Rating|
    |:-|:-|
    |Bias Rating|{obj['bias']}|
    |Factual Rating| {obj['factual']}|\n\nThis rating has been given by Media Bias Fact Check. Check out {obj['name']}`s rating [here]({obj['profile']}) for more information.  \n\n*I am a bot, and this action was performed automatically. Please [contact the moderators of this subreddit](https://www.reddit.com/message/compose/?to=/r/GeopoliticsIndia) if you have any questions or concerns.*
                                        """
    else:
        text = f"""|Metric|Rating|
        |:-|:-|
        |Bias Rating|{obj['bias']}|
        |Factual Rating| {obj['factual']}|
        |Credibility Rating|{obj['credibility']}|\n\nThis rating has been given by Media Bias Fact Check. Check out {obj['name']}`s rating [here]({obj['profile']}) for more information.
                                            \n\n*I am a bot, and this action was performed automatically. 
                                            Please [contact the moderators of this subreddit](https://www.reddit.com/message/compose/?to=/r/GeopoliticsIndia)
                                            if you have any questions or concerns.*
                                            """
    return text


def political_bias(domain_url):
    try:
        with open('MBFC.json', 'r') as mbfc_file:
            data = json.load(mbfc_file)
            for i in data:

                if not i['url'] == "no url available":
                    url = i['url']
                    m = re.search('https?://([A-Za-z_0-9.-]+).*', url)
                    if m:
                        domain = m.group(1)
                        # f2.write(str(domain) + '==' + str(domain_url) + '\n')
                        if str(domain) == str(domain_url):
                            text = print_text(i)
                            return text
        return None
    except Exception as e:
        print(e)


def main():
    iteration = 0
    reddit = praw.Reddit(
        client_id="",
        client_secret="",
        password="",
        user_agent="",
        username="GeoIndModBot",
    )

    subreddit = reddit.subreddit("GeopoliticsIndia")
    while True:
        try:
            for submission in subreddit.new(limit=20):

                f = open('IDs-responded-to.txt', 'r+')

                IDs = f.readlines()
                if str(submission.id) + '\n' not in IDs:

                    if not submission.locked:
                        if not submission.is_self:

                            url = submission.url
                            url = str(url)
                            # m = re.search('https?://?([A-Za-z_0-9-]*).([A-Za-z_0-9-]*).([A-Za-z_0-9-]*)', url)
                            m = re.search('https?://([A-Za-z_0-9.-]+).*', url)
                            if m:
                                domain = m.group(1)
                                if not m.group(1) == 'v.redd.it':
                                    if not m.group(1) == 'i.redd.it':
                                        print("Domain =", domain)
                                        text = political_bias(domain)
                                        if text is None:
                                            f.write(str(submission.id) + '\n')
                                            continue
                                        submission.reply(text)
                                        print(text)
                                        f.write(str(submission.id) + '\n')
        except Exception as e:
            print(e)
        iteration = iteration + 1
        print("Loop Number", iteration)
        time.sleep(600)


if __name__ == '__main__':
    main()
