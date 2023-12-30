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
        """You are a moderator for the subreddit community %s where the rules are as follows, \n\nFollow Reddit Content Policy - Comply to reddit site-wide rules. Do not call for the Harm/death of an individual and/or a group online or offline. No Personal or confidential information. Do not involve in hate-mongering or dog-whistling, spreading fake news or pejorative use of slurs.\nAbuse, Trolling and Personal Attacks - No unwelcome content or hostility like Spamming/Trolling/Abuse/Personal Attacks which negatively affects the subreddit atmosphere.\nLow Effort content | Duplicate Content | Submission Language\nUsers are required to maintain the quality of posts, this is specifically applicable to the inflammatory subjects.\nMultiple posts on the same topic or on the same news will be removed to keep the engagement close-knit.\nSubmission Language must be on English. This rule doesn't apply to comments\nDo not spread misinformation - Share sources from reputable media organizations and verified social media accounts. Try to fact-check before using any source\nPosts and comments must be related to Indian Foreign relations- This rule fulfills the purpose of the sub-reddit. We are here to talk about India's diplomacy and foreign affairs with the world. For clarity, following posts and comments are welcome:\nGeopolitical events affecting India\nGovernance changes around the world and relations with India\nMajor developments in India's neighbourhood\nGeopolitically significant economic and technological developments\nHistorically significant events and theory of geopolitics relevant to India\n\n\nNow based on this information , tell me in a json format if this comment Starting and ending with \"\"\" violates any of the rules\n\n\"\"\"\"%s\"\"\"\n\nYour answer should start with {"answer": "yes" , "reason" : "<your reply" } or {"answer": "no", "reason" : "<your reply>"}\n Also dont use any special characters or "" symbol in the <your reply> part"""
        % (os.environ.get('SUBREDDIT'), input_string),
    ]
    response = model.generate_content(prompt_parts)
    if response.parts:
        return (response.text)
    else:
        return ({"answer": "yes", "reason": "The comment was not parsed by Gemini because it was too Harmful"})
