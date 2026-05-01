import os
import google.generativeai as google_ai

# Initialize the Google Gemini client
client = google_ai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

# The KOLTSEG_TABLA with Google Gemini models and their pricing
gemini_models = {
    'gemini-3.0-flash': {'price': 0.10},
    'gemini-2.0-flash': {'price': 0.08},
    'gemini-2.5-pro': {'price': 0.09},
    'gemini-1.5-flash': {'price': 0.07}
}

# Function to fetch news
def fetch_news(query):
    response = client.generate_text(prompt=query,
                                     model='gemini-3.0-flash')
    return response.content

# Example of fetching news
if __name__ == '__main__':
    news_content = fetch_news('Latest in AI')
    print(news_content)