from newsapi import NewsApiClient
from finlight_client import FinlightApi, ApiConfig
from finlight_client.models import GetArticlesParams
import google.generativeai as genai

newsapi = NewsApiClient(api_key = api_key)

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
        self.history = ""

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
        Use double line breaks in markdown (\n\n) between paragraphs for clearer separation in chat bubbles.
        """
        return t1 + t2 + t3 + t4 + t5 + t0 + prompt

    def contextProvider(self, retry = False):
        return ""

    def get_data(self, user_input):
        additional_rules = '''The API actually specifies format for the query for searching news as q Keywords or phrases to search for in the article title and body. 
        Advanced search is supported here:
        Surround phrases with quotes (") for exact match
        Prepend words or phrases that must appear with a + symbol. Eg: +bitcoin
        Prepend words that must not appear with a - symbol. Eg: -bitcoin
        Alternatively you can use the AND / OR / NOT keywords, and optionally group these with parenthesis. Eg: crypto AND (ethereum OR litecoin) NOT bitcoin.
        Based on these rules, give me a string showing a good query for the user input. Just give me the query with no additional text.
        Don't be so specific in terms of must required words that it results in no query results.
        Be generalized in terms of query and yield the best results.\n
        '''

        prompt = additional_rules
        if len(self.history) > 10:
            prompt += self.contextProvider()

        prompt += "The following is the current user question you must answer (don't insert User/Agent formatting. Just give the answer as text): \n"
        prompt += user_input

        q = model.generate_content(prompt).text
        print("Q:", q)
        return q
        

    def get_more_data(self, user_input):
        context = "Fetch me the most important keyword(s) from the given user query so that I can get relevant data from news API\n"
        rules = "It must be in and/or format. e.g Canada and Modi, Bitcoin or Ethereum.\n"
        constraint = "Just output what I asked and not a single extra word.\n\n"
        prompt = context + rules + constraint
        
        if len(self.history) > 10:
            prompt += self.contextProvider()

        prompt += "The following is the current user question you must answer (don't insert User/Agent formatting. Just give the answer as text): \n"
        prompt += user_input

        q2 = model.generate_content(prompt).text
        print("Q2:", q2)
        return q2
        
    def fetch_news(self, user_input, more = False):

        topic = self.get_data(user_input)
        top_headlines = newsapi.get_everything(q = topic, language = 'en')

        optionalError = 0
        keywords = "Keywords1: " + topic
        
        data = ""
        for article in top_headlines['articles']:
            data += f"Source: {article['source']}\n"
            data += f"Title: {article['title']}\n"
            data += f"Description: {article['description']}\n"
            data += f"Publish Date: {article['publishedAt']}\n\n"

        if len(data) == 0:
            optionalError = 100

        if more:
            myQuery = self.get_more_data(user_input)
            keywords += "\nKeywords2: " + myQuery
            params = GetArticlesParams(query = myQuery)
            r = client.articles.get_basic_articles(params = params)
            r_data = ""
            for article in r['articles']:
                r_data += f"Source: {article['source']}\n"
                r_data += f"Title: {article['title']}\n"
                if article['summary']:
                    r_data += f"Summary: {article['summary']}\n"
                r_data += f"Publish Date: {article['publishDate']}\n\n"
            if len(r_data) == 0:
                optionalError += 200
            return (data + r_data), optionalError, keywords
        return data, optionalError, keywords

    def clearHistory(self):
        self.history = ""
        
    def answer(self, upToDate = False, ret = False, question = "", retry = False):
        from rich.console import Console
        from rich.markdown import Markdown

        user_feed = ""
        keyw = ""

        if not ret:
            print("What is your question?")
            user_input = input()
            user_feed = user_input
            headlines, optionalError, keyw = self.fetch_news(user_input, more = upToDate)

            if optionalError == 300:
                raise ModelError(optionalError)
            
            if len(self.history) < 10:
                p = self.h1() + user_input + self.h2() + headlines + self.h3()
            else:
                p = self.h1() + user_input + self.h2() + headlines + self.h3() + self.contextProvider(retry)
        else:
            user_feed = question
            headlines, optionalError, keyw = self.fetch_news(question, more = upToDate)

            if optionalError == 300:
                raise ModelError(optionalError)
            
            if len(self.history) < 10:
                p = self.h1() + question + self.h2() + headlines + self.h3()
            else:
                p = self.h1() + question + self.h2() + headlines + self.h3() + self.contextProvider(retry)
                
        response = model.generate_content(p)
        
        header = ""
        if retry:
            header = "User retry: "
        else:
            header = "User: "
            
        self.history = header + user_feed + "\n\nAgent Generated Keywords: \n" + keyw +  "\n\nAgent: " + response.text + "\n\n\n"
        
        if ret:
            return response.text

        console = Console()
        md = Markdown(response.text)
        console.print(md)

    def retry(self, upToDate = False, ret = False, question = ""):
        trial = question
        return self.answer(upToDate, ret, trial, retry = True)
        

class ModelError(Exception):
    def __init__(self, code):
        self.code = code
        self.message = self._generate_message(code)
        super().__init__(self.message)

    def _generate_message(self, code):
        messages = {
            100: "News-API has exceeded its free trial limit. Please purchase the premium package.",
            200: "Finlight-API has exceeded its free trial limit. Please purchase the premium package.",
            300: "Daily free limit of both APIs has been exhausted. Please purchase the premium package.",
        }
        return messages.get(code, f"⚠️ Unknown error occurred. Code: {code}")


import gradio as gr
import time

myModel2 = Model()

def process_question(question, history, retry = False):
    if not question.strip():
        return history, "", "Please enter a question to get started."
    history = history + [{"role": "user", "content": question}]
    try:
        if retry:
            markdown_result = myModel2.retry(upToDate = True, ret = True, question = question)
        else:
            markdown_result = myModel2.answer(upToDate = True, ret = True, question = question)
        history = history + [{"role": "assistant", "content": markdown_result}]
        return history, "", ""
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        history = history + [{"role": "assistant", "content": error_msg}]
        return history, "", ""

def clear_chat():
    myModel2.clearHistory()
    return [], "", "Chat cleared. Ask me anything!"

def retry_last(history):
    if not history or len(history) < 2:
        return history, "", "No previous question to retry."
    last_question = next((m["content"] for m in reversed(history) if m["role"] == "user"), None)
    if not last_question:
        return history, "", "No previous question found."
    while history and history[-1]["role"] == "assistant":
        history.pop()
    if history and history[-1]["role"] == "user":
        history.pop()
    return process_question(last_question, history, retry = True)

theme = gr.themes.Soft(
    primary_hue = "sky", 
    secondary_hue = "slate",
    radius_size = "lg",
    text_size = "lg"
)

CUSTOM_CSS = """
/* page background */
html, body, .gradio-container, .main {
    background: #0f172a !important;
    color: #f8fafc !important;
}
/* chatbot bubbles */
.message.user   {background:#5b5b5b !important;color:#ffffff !important;}
.message.bot {
    background: #000000 !important;
    color: #ffffff !important;       /* dark gray text */
    border: 1px solid #e0e7ff !important;
}
.message {
    border-radius: 12px !important;
    padding: 10px !important;
}
/* buttons */
button {border-radius:12px !important;font-weight:600;}
/* hide gradio footer *
footer {display:none !important;}
"""

with gr.Blocks(title = "News Summarizer & Validator",
               css = CUSTOM_CSS,
               theme = theme) as demo:

    gr.HTML("""
        <div class="py-4 text-center">
            <h1 class="text-3xl font-bold text-indigo-600">
                News Summarizer&nbsp;&middot;&nbsp;Validator
            </h1>
            <p class="text-slate-600 text-base">
                Ask anything and get concise, verified answers.
            </p>
        </div>
    """)

    with gr.Row():
        chatbot = gr.Chatbot(label = None,
                             height = 620,
                             value = [],
                             show_copy_button = True,
                             render_markdown = True,
                             type = "messages",
                             avatar_images = (
                                 "user.png",
                                 "bot.png"
                             ))

    status_text = gr.Markdown("💡 Ready!", visible = True)

    with gr.Row():
        with gr.Column(scale = 7):
            question_input = gr.Textbox(
                placeholder="Ask me anything...",
                lines = 2,
                max_lines = 6,
                show_label = False,
                container = False
            )
        with gr.Column(scale = 1, min_width = 100):
            send_btn = gr.Button("Send", variant = "primary", size = "sm")
        with gr.Column(scale = 1, min_width = 100):
            retry_btn = gr.Button("🔄 Retry", variant = "secondary", size = "sm")
        with gr.Column(scale = 1, min_width = 100):
            clear_btn = gr.Button("🗑️ Clear", variant = "secondary", size = "sm")

    with gr.Accordion("Example questions", open = False):
        gr.Examples(
            examples = [
                "Explain the sequence of events that lead to the India-Pakistan escalation.",
                "How did other countries react to the India-Pakistan escalation?",
                "Did Bitcoin hit its all time high recently?",
                "What's the situation between Trump and Harvard University?",
                "Explain the bill that Republicans want to pass in USA.",
                "What is the latest news in the Automobile industry?",
                "Is there something worth knowing about the recent Geopolitics?",
                "What's new in NLP?",
                "How are markets doing today?"
            ],
            inputs = question_input
        )

    def _send(msg, hist): return process_question(msg, hist)
    send_btn.click(_send,  [question_input, chatbot], [chatbot, question_input, status_text], show_progress = True)
    question_input.submit(_send, [question_input, chatbot], [chatbot, question_input, status_text], show_progress = True)
    retry_btn.click(retry_last, chatbot, [chatbot, question_input, status_text])
    clear_btn.click(clear_chat, None, [chatbot, question_input, status_text])

if __name__ == "__main__":
    demo.launch(inbrowser = True)
