import json
import os

from src.get_latest_news import get_summary_from_url

urls = [
       "https://theprint.in/diplomacy/india-must-underwrite-infra-projects-in-neighbourhood-to-ensure-stable-ties-in-long-term-jaishankar/2758765/",
]

outputs = []
for url in urls:
    output = {
        "url": url,
        "summary": get_summary_from_url(url)
    }
    outputs.append(output)
    print(json.dumps(output, indent=4))

output_file = "summaries.json"
with open(output_file, "w") as f:
    json.dump(outputs, f, indent=4)
print(f"Summaries written to {output_file}")