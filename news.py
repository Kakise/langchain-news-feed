import os

import requests
from bs4 import BeautifulSoup
from langchain import LLMChain, OpenAI, PromptTemplate
from langchain.chains.mapreduce import MapReduceChain
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter

from pymongo import MongoClient


class News:
    def __init__(self, link: str):
        llm = OpenAI(temperature=0)
        text_splitter = CharacterTextSplitter()

        req = requests.get(link)
        text = req.content

        soup = BeautifulSoup(text, "html.parser")
        text_content = soup.get_text()

        texts = text_splitter.split_text(text_content)

        doc = [Document(page_content=t) for t in texts]

        chain = load_summarize_chain(llm, chain_type="map_reduce")
        self.excerpt = chain.run(doc)
        self.link = link

    def save(self):
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client.get_database("news")
        news = db.news
        news.insert_one({"excerpt": self.excerpt, "link": self.link})

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