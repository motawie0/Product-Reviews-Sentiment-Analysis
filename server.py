import csv
import pip
import requests
import time

try:
    from groq import Groq
    import json
    from bs4 import BeautifulSoup
    import pandas as pd
    import gradio as gr
    from collections import Counter
    import urllib.parse
except:
    pip.main(['install', 'groq'])
    pip.main(['install', 'gradio'])
    pip.main(['install', 'bs4'])
    pip.main(['install', 'requests'])
    pip.main(['install', 'Counter'])
    pip.main(['install', 'urllib3'])
    from groq import Groq
    import json
    from bs4 import BeautifulSoup
    import pandas as pd
    import gradio as gr
    from collections import Counter
    import urllib.parse

class AmazonReviewsScrapper:
    def __init__(self):
        self.user_agents : list[str] = [
            # Google Chrome
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",

            # Mozilla Firefox
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:88.0) Gecko/20100101 Firefox/88.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0",

            # Microsoft Edge
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 Edg/90.0.818.51",

            # Apple Safari
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",

            # Opera
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 OPR/76.0.4017.123",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 OPR/76.0.4017.123",

            # Android Webview
            "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Mobile Safari/537.36",

            # Common Bot User-Agents
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
        ]
    
        self.headers : dict[str] = {
            "Accept-Language": "en-GB,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive"
        }

        self.domain = "https://amazon.eg/"

    def _extract_page_content(self, url: str) -> BeautifulSoup:
        """Fetches the HTML content of a page given its URL, handling HTTP errors and exceptions."""
        for user_agent in self.user_agents:
            headers = {
                "Accept-Language": "en-GB,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Cache-Control": "max-age=0",
                "Connection": "keep-alive",
                "User-Agent": user_agent,
            }
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()  # Raises HTTPError for bad responses
                return BeautifulSoup(response.text, "lxml")
            except requests.RequestException as e:
                print(f"Failed to retrieve data from {url} with User-Agent '{user_agent}': {e}")
        return None
    
    def _extract_page_reviews(self, soup) -> list[dict]:
        """ Extracts a list of review data from the parsed HTML soup of a product review page. """
        if soup is None:
            return []
        
        try:
            review_elements = soup.select("div.review")
            reviews = []

            for review in review_elements:
                details = {
                    "author": review.select_one("span.a-profile-name").text if review.select_one("span.a-profile-name") else None,
                    "rating": review.select_one("i.review-rating").text.replace("out of 5 stars", "").strip() if review.select_one("i.review-rating") else None,
                    "title": review.select_one("a.review-title > span").text if review.select_one("a.review-title > span") else None,
                    "content": review.select_one("span.review-text").text if review.select_one("span.review-text") else None,
                    "date": review.select_one("span.review-date").text if review.select_one("span.review-date") else None,
                    "verified": review.select_one("span.a-size-mini").text if review.select_one("span.a-size-mini") else None,
                    "image_url": review.select_one("img.review-image-tile")['src'] if review.select_one("img.review-image-tile") else None
                }
                reviews.append(details)

            return reviews
        except Exception as error:
            print(f"Failed to retrieve data: {error}")
        return None
    
    def _extract_product_info(self, url) -> (str, str) :
        """Feteches product name and ASIN from a given url"""
        try:
            path_parts : str = url.replace("https://", "").split("/")
            return path_parts[3], path_parts[5]
        except Exception as error:
            print(f"Failed to extract product information: {error}")
            return None, None
    
    def _get_reviews_url(self, product_name: str, asin: str, domain: str = "https://www.amazon.eg") -> str:
        """Constructs the review URL for a given product."""
        return f"{domain}/-/en/{product_name}/product-reviews/{asin}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews"
    
    def extract_product_reviews(self, url) -> (str, list[dict]):
        """Orchestrates the fetching of all reviews from multiple pages for a given Amazon product URL."""
        try:
            product_name, asin = self._extract_product_info(url)

            if (product_name == None or asin == None):
                gr.Warning("Enter a valid URL")
                raise Exception("URL invalid")
        
            review_url = self._get_reviews_url(product_name, asin)
            all_reviews = []
            while review_url:
                soup = self._extract_page_content(review_url)
                all_reviews.extend(self._extract_page_reviews(soup))
                next_page_link = None
                if soup:
                    if soup.find('li', class_='a-last'):
                        next_page_link = soup.find('li', class_='a-last').find('a', href=True)
                review_url = f"{self.domain}{next_page_link['href']}" if next_page_link else None

            # print((product_name, all_reviews))
            return product_name, all_reviews
        except Exception as error:
            print(f"Failed to extract product reviews: {error}")
            return []
        
class ReviewsProcessor:
    def __init__(self, api_key: str, model_name: str):
        self.client = Groq(api_key=api_key)
        self.model_name = model_name
    
    def get_all_reviews(self, reviews: list[dict]) -> list[str]:
        try:
            reviews_df = pd.DataFrame(reviews)
            return reviews_df["content"].to_list()
        except Exception as error:
            print(f"Failed to extract product reviews: {error}")
    
    def get_egypt_reviews(self, reviews: list[dict]) -> list[str] :
        try:
            reviews_df = pd.DataFrame(reviews)
            return reviews_df[reviews_df["date"].str.contains("Egypt")]["content"].to_list()
        except Exception as error:
            print(f"Failed to extract product reviews: {error}")
    
            
    def get_LLM_reponses(self, reviews_df: list[str]) -> dict[str]:
        try:
            # raise Exception("Internet")
            responses = {"reviews": [], "sentiment": [], "pros": [], "cons": []}
            system_instruction = """
                You are tasked to function as an assistant specifically designed to evaluate product reviews in XML format. The assistant will analyze individual reviews and provide detailed insights including sentiment analysis for each review. Additionally, the assistant will summarize the pros and cons of the product based on the collective content of the reviews.

                Key functionalities include:
                1. Sentiment Analysis: Determine the sentiment ("positive", "neutral", "negative") of each review and quantify this sentiment to provide a comprehensive view, do not return their values as numbers.
                2. Pros and Cons Summary: Extract and summarize the advantages and disadvantages of the product as mentioned across different reviews.
                3. Insightful Summaries: Generate brief summaries for reviews that highlight critical information and overall opinion.
                4. Categorization of Feedback: Organize feedback into categories such as quality, usability, value for money, etc., based on the content of the reviews.

                The assistant should handle reviews across a variety of products and ensure accuracy and neutrality in the analysis and summaries provided.

                Inputs will be in the format:
                <review>
                    review1
                </review>

                Your output **must** always be in the format:
                {"sentiment": [...], "pros": [...], "cons": [...]}

                Do not provide any extra information. **Make sure that the number of sentiments you provided match the number of reviews provided to you**
            """
            for review in reviews_df:
                chat_history = [{"role": "system", "content":system_instruction }, {"role": "user", "content": "<review>\n" + review + "\n</review>"}]
                chat_completion = self.client.chat.completions.create(messages=chat_history, model=self.model_name, temperature=0.01)

                assistant_response = chat_completion.choices[0].message.content
                assistant_response = assistant_response[assistant_response.find("{"):assistant_response.find("}")+1].replace("\n", "").replace("\t", "")
                assistant_response = json.loads(assistant_response)
                if len(assistant_response["sentiment"]) == 1:
                    responses["sentiment"] += assistant_response["sentiment"]
                    responses["pros"] += assistant_response["pros"]
                    responses["cons"] += assistant_response["cons"]
                    responses["reviews"].append(review)
                    time.sleep(1.5)
            responses["pros"] = list(set(responses["pros"]))
            responses["cons"] = list(set(responses["cons"]))
            
            system_instruction = """
                You are tasked to summarize a list of pros and a list of cons of a product. Summarize each list in 5 main points maximum. Summaries should be written in Modern Standard Arabic.
                Your output **must** always be in the format:
                {"pros": [...], "cons": [...]}
                Do not provide any extra information.
            """
            user_message = "<pros>" + str(responses["pros"]) + "</pros>\n" + "<cons>" + str(responses["cons"]) + "</cons>"
            chat_history = [{"role": "system", "content":system_instruction }, {"role": "user", "content": user_message}]
            chat_completion = self.client.chat.completions.create(messages=chat_history, model=self.model_name, temperature=0.01)
            assistant_response = chat_completion.choices[0].message.content
            assistant_response = assistant_response[assistant_response.find("{"):assistant_response.find("}")+1].replace("\n", "").replace("\t", "")
            assistant_response = json.loads(assistant_response)
            responses["pros"] = assistant_response["pros"]
            responses["cons"] = assistant_response["cons"]
            return responses
        except Exception as error:
            print(f"Failed to process chunks {error}")
            gr.Warning("Processing Error")


class Pipeline:
    def __init__(self, api_key: str, model_name: str):
        self.scrapper = AmazonReviewsScrapper()
        self.processor = ReviewsProcessor(api_key, model_name)
    
    def get_statistics_all(self, url: str) -> dict:
        try:
            product_name, reviews = self.scrapper.extract_product_reviews(url)
            if reviews:
                reviews_df = self.processor.get_all_reviews(reviews)
                responses = self.processor.get_LLM_reponses(reviews_df)
                sentiments = responses["sentiment"]
                sentiments_dict = Counter(sentiments)
                sentiments_df = pd.DataFrame(list(sentiments_dict.items()), columns=['Sentiment', 'Percentage'])
                sentiments_df['Percentage'] = sentiments_df['Percentage']/sentiments_df['Percentage'].sum()
                return pd.DataFrame({"Reviews": [self._word_wrap(text) for text in responses["reviews"]], "Sentiment": responses["sentiment"]}), pd.DataFrame({"Pros": responses["pros"]}), pd.DataFrame({"Cons": responses["cons"]}), sentiments_df
            else:
                raise Exception("Something went wrong")
        except Exception as error:
            print(error)
            return None
    
    def get_statistics_egypt(self, url: str) -> dict:
        try:
            product_name, reviews = self.scrapper.extract_product_reviews(url)

            # if (product_name )
            if reviews:
                reviews_df = self.processor.get_egypt_reviews(reviews)
                responses = self.processor.get_LLM_reponses(reviews_df)
                sentiments = responses["sentiment"]
                sentiments_dict = Counter(sentiments)
                sentiments_df = pd.DataFrame(list(sentiments_dict.items()), columns=['Sentiment', 'Percentage'])
                sentiments_df['Percentage'] = sentiments_df['Percentage']/sentiments_df['Percentage'].sum()
                return pd.DataFrame({"Reviews": [self._word_wrap(text) for text in responses["reviews"]], "Sentiment": responses["sentiment"]}), pd.DataFrame({"Pros": responses["pros"]}), pd.DataFrame({"Cons": responses["cons"]}), sentiments_df
            else:
                raise Exception("Something went wrong")
        except Exception as error:
            print(error)
            return None
        
    def _word_wrap(self, text, width=10):
        """
            Wraps text to fit within the specified width. This function ensures that the text
            is broken into lines that do not exceed the specified width, and breaks are made
            at word boundaries where possible.

            Args:
            text (str): The text to be wrapped.
            width (int): The maximum width of each line in characters.

            Returns:
            str: The wrapped text with new lines inserted.
        """
        words = text.split()
        if not words:
            return ""

        # Initialize variables to build the wrapped lines
        current_line = words[0]
        wrapped_text = []

        for word in words[1:]:
            # Check if adding the next word would exceed the width
            if len(current_line) + len(word) + 1 > width:
                # If it does, add the current line to the wrapped text and start a new line
                wrapped_text.append(current_line)
                current_line = word
            else:
                # Otherwise, add the word to the current line
                current_line += " " + word

        # Add the last formed line to the wrapped text
        wrapped_text.append(current_line)

        # Join all lines into a single string separated by newline characters
        return "\n".join(wrapped_text)
        

pipeline = Pipeline("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", "llama3-70b-8192")


class GradioApp:
    def __init__(self):
        self.credentials = self._read_db("users.csv")

    def _read_db(self, filepath):
        user_password_dict = {}
        try:
            with open(filepath, mode='r') as file:
                csv_reader = csv.reader(file)
                next(csv_reader)  # Skip the header row
                for row in csv_reader:
                    if len(row) == 2:  # Ensure the row has exactly 2 elements
                        user, password = row
                        user_password_dict[user] = password
        except FileNotFoundError:
            print(f"Error: The file {filepath} does not exist.")
        except Exception as e:
            print(f"An error occurred: {e}")
    
        return user_password_dict

    def _login(self, username, password):
        if username in self.credentials and self.credentials[username] == password:
            return True
        else:
            return False
        
    def run(self):
        with gr.Blocks() as app:
            try:
                # Title of the app
                gr.Markdown("# Product Reviews Analysis Tool")

                # Textbox for URL input
                text_input = gr.Textbox(label="Enter your URL here")

                # Submit button
                button = gr.Button("Submit")

                # Section for displaying sentiment analytics
                gr.Markdown("## Reviews Sentiment Analytics")
                plot = gr.BarPlot(x='Sentiment', y='Percentage', width=600, height=300)

                # Section for displaying individual reviews
                gr.Markdown("## Reviews")
                reviews_output = gr.Dataframe()

                # Section for displaying pros and cons
                gr.Markdown("## Pros and Cons")
                with gr.Row():
                    pros_output = gr.Dataframe()
                    cons_output = gr.Dataframe()

                # Define the function to be called on button click
                button.click(fn=pipeline.get_statistics_egypt, inputs=text_input, outputs=[reviews_output, pros_output, cons_output, plot])

                app.launch(
                    auth = self._login,
                    share=True,
                    server_port=7860)

            except Exception as error:
                gr.Markdown(f"## An error occurred: {error}")

app = GradioApp()

app.run()