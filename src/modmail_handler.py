import re

def extract_moderator_links(reddit, conversation_id, subreddit):
    """
    Extract links from the last message in a modmail conversation.
    
    Args:
        conversation_id (str): The ID of the modmail conversation
        subreddit (str): The subreddit name
        
    Returns:
        str: The URL found in the last message, or None if no URL is found
    """
    # Get the conversation
    conversation = reddit.subreddit(subreddit).modmail(conversation_id)
    
    # Regex to extract URLs
    url_regex = r'https?://[^\s)]+'
    
    # Get the last message
    messages = list(conversation.messages)
    if not messages:
        return []
        
    last_message = messages[-1]
    if last_message.author == "GeoIndModBot":
        return []
        
    # Extract URLs from the last message
    urls = re.findall(url_regex, last_message.body_markdown)
    return urls[0] if urls else []

