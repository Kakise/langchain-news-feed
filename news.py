import os
from datetime import datetime
from typing import Any, Dict, List, NewType

import requests
from bs4 import BeautifulSoup
from langchain import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.llms import AzureOpenAI
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from pymongo import MongoClient

NewsType = NewType("NewsType", Dict[str, str])


class News:
    def __init__(self, link: str, user: Any):
        if link is None:
            raise ValueError("Link cannot be None")

        llm = AzureOpenAI(
            deployment_name="text-davinci-003", model_name="text-davinci-003"
        )
        text_splitter = CharacterTextSplitter()

        req = requests.get(link)
        text = req.content

        soup = BeautifulSoup(text, "html.parser")
        text_content = soup.get_text()
        if len(text_content) > 3700:
            text_content = text_content[:3700]

        texts = text_splitter.split_text(text_content)

        doc = [Document(page_content=t) for t in texts]

        prompt_template = """Write a concise summary, in english, of the following:


        {text}


        CONCISE SUMMARY IN ENGLISH:"""
        prompt_template_title = """Write a title for the following:


        {text}


        TITLE IN ENGLISH:"""
        PROMPT = PromptTemplate(template=prompt_template, input_variables=["text"])
        PROMPT_TITLE = PromptTemplate(
            template=prompt_template_title, input_variables=["text"]
        )

        chain = load_summarize_chain(llm, chain_type="stuff", prompt=PROMPT)
        chain_title = load_summarize_chain(llm, chain_type="stuff", prompt=PROMPT_TITLE)
        self.title = chain_title.run(doc)
        self.excerpt = chain.run(doc)
        self.link = link
        if user is not None:
            self.user = user
        else:
            self.user = {"name": "Anonymous"}

    def save(self):
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client.get_database("news")
        news = db.news
        # Check if news already exists
        if news.find_one({"link": self.link}) is not None:
            print("This news is already in the database")
        else:
            news.insert_one(
                {
                    "title": self.title,
                    "excerpt": self.excerpt,
                    "link": self.link,
                    "author": self.user["name"],
                    "date": datetime.now().strftime("%Y-%m-%d"),
                }
            )


class NewsFeed:
    def __init__(self):
        self.news: List[NewsType] = []
        client = MongoClient(os.getenv("MONGO_URI"))
        self.db = client.get_database("news")
        news = self.db.news
        for n in news.find():
            self.news.append(n)

    def get_one(self):
        return self.news[-1]

    def get_all_news(self):
        return self.news[::-1]

    def search(self, text: str) -> List[NewsType]:
        result = self.db.news.aggregate(
            [
                {
                    "$search": {
                        "index": "default",
                        "text": {"query": text, "path": {"wildcard": "*"}},
                    }
                }
            ]
        )
        return list(result)

    def delete(self, link: str | None) -> int | None:
        try:
            result = self.db.news.delete_one({"link": link})
            return result.deleted_count
        except Exception as e:
            print(e)
