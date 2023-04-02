import os

import requests
from bs4 import BeautifulSoup
from langchain import LLMChain, OpenAI, PromptTemplate
from langchain.chains.mapreduce import MapReduceChain
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter


class News:
    excerpt = ""

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
