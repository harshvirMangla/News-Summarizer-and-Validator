api_key = ""
api_key2 = ""
gemini_api = ""

from newsapi import NewsApiClient
from finlight_client import FinlightApi, ApiConfig
from finlight_client.models import GetArticlesParams
import google.generativeai as genai

newsapi = NewsApiClient(api_key = 'c477e5c2b52b4e618da89c116dc9bc2a')

client = FinlightApi(
    config = ApiConfig(
        api_key = api_key2
    )
)

genai.configure(api_key = gemini_api)
model = genai.GenerativeModel(model_name = "gemini-2.0-flash")

class Model:
    def __init__(self):
        self.model_name = "gemini-2.0-flash"
        self.model = genai.GenerativeModel(model_name = self.model_name)

    def h1(self):
        return "The following is the User Query: \n"

    def h2(self):
        return "The following are the relevant headlines found from news API:\n"

    def h3(self):
        from datetime import date
        today = date.today()
        t1 = "\nCheck if any matches user question and tell the user."
        t2 = "Else handle the situation appropriately."
        t3 = "\nAct professionally and try to explain the matching results a bit.\nDon't mention provided headlines. Act like you are the agent."
        t4 = "\nMention sources if any and also try possible expansions of abbreviations."
        t0 = "Dont ever mention about 'the articles'. Reply as if it were your knowledge in the first place. As if you were a super intelligent person."
        t5 = f"Today's date is {today} for your additional knowledge."

        prompt = f"""
        You are a news assistant bot. When the user asks a question, match it with current headlines and generate a well-formatted answer.
        **Instructions**:
        - Use **bold** for important entities or keywords or maybe location names.
        - Use *italics* for quotes or indirect information.
        - Use __underline__ for dates or time references.
        """
        # t5 = "\nAs the first words of response, give the abbreviations you would want me to expand for you if any in the matching headline text. Start as [ab1, ab2, ...] and then text in next line"
        return t1 + t2 + t3 + t4 + t5 + t0 + prompt

    def get_data(self, user_input):
        # context = "Fetch me the most important keyword(s) from the given user query so that I can get relevant data from news API\n"
        # form = "Return it as just one string and nothing else and also also fetch me the two code ISO word for the country related to it."
        # delimiter = "Delimit the two results using an &."
        additional_rules = '''The API actually specifies format for the query for searching news as q Keywords or phrases to search for in the article title and body. 
        Advanced search is supported here:
        Surround phrases with quotes (") for exact match
        Prepend words or phrases that must appear with a + symbol. Eg: +bitcoin
        Prepend words that must not appear with a - symbol. Eg: -bitcoin
        Alternatively you can use the AND / OR / NOT keywords, and optionally group these with parenthesis. Eg: crypto AND (ethereum OR litecoin) NOT bitcoin.
        Based on these rules, give me a string showing a good query for the user input. Just give me the query with no additional text.
        Don't be so specific in terms of must required words that it results in no query results.
        Be generalized in terms of query and yield the best results.
        '''

        # prompt = context + user_input + form + delimiter
        prompt = additional_rules + user_input

        q = model.generate_content(prompt).text
        print("Q:", q)
        return q
        
        # topic, country = model.generate_content(prompt).text.split('&')
        # return topic, country[:-1].lower()

    def get_more_data(self, user_input):
        context = "Fetch me the most important keyword(s) from the given user query so that I can get relevant data from news API\n"
        rules = "It must be in and/or format. e.g Canada and Modi, Bitcoin or Ethereum."
        constraint = "Just output what I asked and not a single extra word."
        prompt = context + rules + constraint + user_input

        q2 = model.generate_content(prompt).text
        print("Q2:", q2)
        return q2
        
    def fetch_news(self, user_input, more = False):
        # topic, country_code = self.get_data(user_input)
        # top_headlines = newsapi.get_everything(q = topic, language = 'en', country = country_code)

        topic = self.get_data(user_input)
        top_headlines = newsapi.get_everything(q = topic, language = 'en')
        
        data = ""
        for article in top_headlines['articles']:
            data += f"Source: {article['source']}\n"
            data += f"Title: {article['title']}\n"
            data += f"Description: {article['description']}\n"
            data += f"Publish Date: {article['publishedAt']}\n\n"

        if more:
            myQuery = self.get_more_data(user_input)
            params = GetArticlesParams(query = myQuery)
            r = client.articles.get_basic_articles(params = params)
            r_data = ""
            for article in r['articles']:
                r_data += f"Source: {article['source']}\n"
                r_data += f"Title: {article['title']}\n"
                if article['summary']:
                    r_data += f"Summary: {article['summary']}\n"
                r_data += f"Publish Date: {article['publishDate']}\n\n"
            # print(data + r_data)
            return data + r_data
        # print(data)
        return data

    def answer(self, upToDate = False, ret = False, question = ""):
        from rich.console import Console
        from rich.markdown import Markdown

        if not ret:
            print("What is your question?")
            user_input = input()
            headlines = self.fetch_news(user_input, more = upToDate)
            p = self.h1() + user_input + self.h2() + headlines + self.h3()
            # print(headlines)
        else:
            headlines = self.fetch_news(question, more = upToDate)
            p = self.h1() + question + self.h2() + headlines + self.h3()
        
        response = model.generate_content(p)

        if ret:
            return response.text

        console = Console()
        md = Markdown(response.text)
        console.print(md)
        # print(response.text)
        
