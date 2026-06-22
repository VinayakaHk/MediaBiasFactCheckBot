from google import genai

client = genai.Client(api_key="AIzaSyC5UlrZmHBvkYvkDvxl7nkSy35TYHV1XC0")

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="What is the latest geopolitical news this week?",
)

print(response.text)