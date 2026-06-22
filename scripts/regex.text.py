import re

text = """
URL 1 :

https://www.theguardian.com/global-development/2024/jan/10/every-days-a-school-day-the-great-grandmother-who-goes-to-primary-school

URL 2 :

https://www.nytimes.com/2024/01/09/world/americas/ecuador-gang-prison-emergency.html

URL 3 :

https://www.foreignaffairs.com/china/how-thwart-chinas-bid-lead-global-south

URL 4 :

https://foreignpolicy.com/2024/01/05/ones-and-tooze-trump-2024-elections-ukraine-taiwan-india/
"""

# Define a regular expression pattern to match URLs
domain_pattern = re.compile(r'https?://([a-zA-Z0-9.-]+)')
url_pattern = re.compile(r'(https?://[^\s]+)')


# Find all matches in the text
domains = domain_pattern.findall(text)

if (domains == []):
    print('empty')
else:
    print("domains = ", domains)


urls = url_pattern.findall(text)

if (urls == []):
    print('empty')
else:
    print("urls : ", urls)
