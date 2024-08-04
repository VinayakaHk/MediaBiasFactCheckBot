import re
import json 
from  src.exceptions import print_exception
def add_prefix_to_paragraphs(input_string):
    try:
        formatted_string = re.sub(r'\n+', '\n>\n>', input_string)
        formatted_string = re.sub(r'(?<=\n\n)(?=[^\n])', "> ", formatted_string)
        return formatted_string
    except Exception as e:
        print_exception()
        
def print_mbfc_text(domain, obj):
    text = f"""\n\n**📰 Media Bias fact Check Rating :**  {obj['name']} \n\n\n\n
|Metric|Rating|
|:-|:-|
|Bias Rating|{obj['bias']}|
|Factual Rating| {obj['factual']}|
"""
    credibility = obj.get("credibility", "no credibility rating available")
    if credibility != "no credibility rating available":
        text += f"|Credibility Rating|{obj['credibility']}|\n"

    text += f"""\nThis rating was provided by Media Bias Fact Check. For more information, see {obj['name']}'s review 
[here]({obj['profile']}).
***"""
    return text


def mbfc_political_bias(domain_url):
    try:
        with open('./docs/MBFC_modified.json', 'r') as mbfc_file:
            mbfc_data = json.load(mbfc_file)
        url_index = {entry["url"]: entry for entry in mbfc_data}

        if domain_url in url_index:
            retrieved_data = url_index[domain_url]
            text = print_mbfc_text(retrieved_data['url'], retrieved_data)
            return text
        else:
            print("URL not found in the index")
            return None

    except Exception as e:
        print('Exception ', e)
        print_exception()
        time.sleep(60)

