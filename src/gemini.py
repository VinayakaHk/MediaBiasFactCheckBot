import os
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


def gemini_detection(input_string):
    prompt_parts = [
        """You are a moderator for the subreddit community %s where the rules are as follows, \n\nFollow Reddit Content Policy - Comply to reddit site-wide rules. Do not call for the Harm/death of an individual and/or a group online or offline. Do not involve in hate-mongering or dog-whistling, spreading fake news or pejorative use of slurs.\nAbuse, Trolling and Personal Attacks - No unwelcome content or hostility like Spamming/Trolling/Abuse/Personal Attacks which negatively affects the subreddit atmosphere.\n\nNow based on this information , tell me in a json format if this comment Starting and ending with \"\"\" violates any of the rules\n\n\"\"\"\"%s\"\"\"\n\nYour answer should range from  {"answer": "99" , "reason" : "<your reply>" } or {"answer": "1", "reason" : "<your reply>"}\n where 1-99 is the probability where 99 percent the answer violates the rules or 1 percent , doesn't violate the rules.   Also dont use any special characters or "" symbol in the <your reply> part. make sure <your reply> is detailed and sophisticated."""
        % (os.environ.get('SUBREDDIT'), input_string),
    ]
    try:
        response = model.generate_content(prompt_parts)
    except Exception as e:
        print(f"""\033An exception occurred: {
              e}. Retrying in 2 seconds...\033""", e)
        time.sleep(2)
        response = model.generate_content(prompt_parts)
    if (response.prompt_feedback.block_reason):
        return ('{"answer": "100", "reason": "Rule 1 : Breaks Reddit content policy"}')
    if (response.text):
        return (response.text)
    else:
        return ('{"answer": "0", "reason": "API ERROR"}')
