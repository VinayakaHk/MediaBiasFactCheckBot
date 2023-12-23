import json

# def mbfc_political_bias(domain_url):

#     try:
#         if not hasattr(mbfc_political_bias, "data"):
#             with open('./docs/MBFC_modified.json', 'r') as mbfc_file:
#                 mbfc_political_bias.data = json.load(mbfc_file)
#         start_time = time.time()  # Record start time

#         for i in mbfc_political_bias.data:
#             if not i['url'] == "no url available":
#                 url = i['url']
#                 url_without_protocol = re.sub(r'https?://', '', url)

#                 # Remove trailing slash
#                 domain_match = re.search(
#                     r'([A-Za-z_0-9.-]+)', url_without_protocol)
#                 if domain_match.group(1) == domain_url:
#                     print(domain_match.group(1))
#                     end_time = time.time()  # Record end time
#                     elapsed_time1 = end_time - start_time
#                     print('elapsed_time1 : ', elapsed_time1 * 1000)

#                 # print(f"""Time taken to create the index: {
#                 #       elapsed_time} seconds""")

#         return None
#     except Exception as e:
#         print(e)


with open('./docs/MBFC_modified.json', 'r') as mbfc_file:
    mbfc_political_bias = json.load(mbfc_file)

url_index = {entry["url"]: entry for entry in mbfc_political_bias}

desired_url = "www.nytimes.com"
if desired_url in url_index:
    retrieved_data = url_index[desired_url]
    print(retrieved_data['url'])
else:
    print("URL not found in the index")
