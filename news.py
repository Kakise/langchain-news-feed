import os

import requests
from bs4 import BeautifulSoup
from langchain import LLMChain, OpenAI, PromptTemplate
from langchain.chains.mapreduce import MapReduceChain
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from datetime import datetime

from pymongo import MongoClient


class News:
    def __init__(self, link: str, user: any = None):
        llm = OpenAI(temperature=0)
        text_splitter = CharacterTextSplitter()

        req = requests.get(link)
        text = req.content

        soup = BeautifulSoup(text, "html.parser")
        text_content = soup.get_text()

        texts = text_splitter.split_text(text_content)

        doc = [Document(page_content=t) for t in texts]

        prompt_template = """Write a concise summary of the following:


        {text}


        CONCISE SUMMARY IN ENGLISH:"""
        prompt_template_title = """Write a title for the following:


        {text}


        TITLE IN ENGLISH:"""
        PROMPT = PromptTemplate(template=prompt_template, input_variables=["text"])
        PROMPT_TITLE = PromptTemplate(template=prompt_template_title, input_variables=["text"])

        chain = load_summarize_chain(llm, chain_type="stuff", prompt=PROMPT)
        chain_title = load_summarize_chain(llm, chain_type="stuff", prompt=PROMPT_TITLE)
        self.title = chain_title.run(doc)
        self.excerpt = chain.run(doc)
        self.link = link
        self.user = user

    def save(self):
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client.get_database("news")
        news = db.news
        news.insert_one({"title": self.title, "excerpt": self.excerpt, "link": self.link, "author": self.user["name"], "date": datetime.now().strftime('%Y-%m-%d')})

class NewsFeed:
    def __init__(self):
        self.news = []
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client.get_database("news")
        news = db.news
        for n in news.find():
            self.news.append(n)
    
    def get_one(self):
        return self.news[-1]
    def get_all_news(self):
        return self.news