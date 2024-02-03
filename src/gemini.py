import os
import re
import time
import json
import linecache
import sys

import google.generativeai as genai
from dotenv import load_dotenv


load_dotenv()
genai.configure(api_key=os.environ.get("GEMINI"))

# Set up the model
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_ONLY_HIGH"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_ONLY_HIGH"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_ONLY_HIGH"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_ONLY_HIGH"
    },
]

model = genai.GenerativeModel(model_name="gemini-pro",
                              generation_config=generation_config,
                              safety_settings=safety_settings)


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno,
                                                       line.strip(), exc_obj))


def convert_quotes(obj):
    if isinstance(obj, str):
        return obj.replace('"', "'")
    return obj


def gemini_detection(input_string, parent_comment, link_title):
    if (parent_comment == None):
        parent_comment = link_title
    try:
        retry = True
        while retry:
            prompt_parts = [
                """You are a moderator for the subreddit community %s where the rules are as follows, \n\n
Rule 2 : No Spamming, No Verbal Abuse and no Personal Attacks \n\n

For context, %s is the title of the article and %s is the parent comment that OP is replying to. Do not judge these comments as these are just for context. 

Now based on this information , tell me in a json format 
if this comment Starting and ending with \"\"\" violates any of the rules \n\n\"\"\"\"%s\"\"\"\n\n
Your answer should range from  {"answer": "0" , "reason" : "<your reply>" }  or {"answer": "91", "reason" : "<your reply>"}\n where 0-91 is the probability where  0 percent -  doesn't violate the rules.\n 91 percent - the answer violates the rules.
make sure <your reply> is detailed and sophisticated. do not write anything beyond answer and reason."""
                % (os.environ.get('SUBREDDIT'), link_title, parent_comment, input_string),
            ]
            try:
                response = model.generate_content(prompt_parts)
                retry = False
            except Exception as e:
                print(f"""\033An exception occurred: {
                    e}. Retrying in 2 seconds...\033""", e)
                time.sleep(2)
            if (response.prompt_feedback.block_reason):
                return {"answer": "100", "reason": "The comment is extremely toxic. It violates Rule 1 (Follow Reddit's content policy) and Rule 2 (Abuse, trolling, or personal attacks)."}

            if (response._result.candidates):
                if (str(response._result.candidates[0].safety_ratings).find('HIGH') != -1):
                    return {"answer": "100", "reason": "The comment is extremely toxic. It violates Rule 1 (Follow Reddit's content policy) and Rule 2 (Abuse, trolling, or personal attacks)."}

                text = str(response.candidates[0].content.parts[0])
                json_match = re.search(r'{.+}', text)

                # Check if a match is found
                if json_match:
                    # Extract the matched JSON string
                    json_str = json_match.group(0)
                    json_str = json_str.replace('\\"', '"')
                    json_str = json_str.replace("\\'", "'")
                    answer_pattern = re.compile(
                        r'"answer"\s*:\s*["\']?(\d+)["\']?')
                    answer_match = answer_pattern.search(json_str)
                    json_str2 = ""
                    if (answer_match):
                        answer = answer_match.group(1)
                        json_str2 = '{"answer":"' + answer + '"'
                    reason_pattern = re.compile(
                        r'"reason"\s*:\s*["\']?(.*?)"\}')
                    reason_match = reason_pattern.search(json_str)
                    if (reason_match):
                        reason = reason_match.group(1)
                        reason = re.sub(r'"|\\\\"', '\'', reason)
                        json_str2 = json_str2 + ', "reason":"' + reason + '"}'
                        json_obj = json.loads(json_str2)
                    return json_obj
                else:
                    return ({"answer": "0", "reason": "API ERROR"})
            if (response.text):
                try:
                    response = json.loads(response.text)
                    return response
                except:
                    print("gemini response : ", response.text)
                    return ({"answer": "0", "reason": "API ERROR"})
            else:
                return ({"answer": "0", "reason": "API ERROR"})
    except Exception as e:
        PrintException()
        time.sleep(60)
