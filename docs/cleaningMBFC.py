import json

# Load the JSON data from the file
with open('MBFC.json', 'r') as json_file:
    data = json.load(json_file)

# Remove trailing slashes from the URLs
for entry in data:
    if 'url' in entry and entry['url']:
        entry['url'] = entry['url'].rstrip('/')

# Save the modified data back to the file
with open('MBFC_modified.json', 'w') as json_file:
    json.dump(data, json_file, indent=2)

print("URLs without trailing slashes have been saved to MBFC_modified.json")
