import requests
from bs4 import BeautifulSoup
import PyPDF2
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from collections import Counter
import ssl
ssl._create_default_https_context = ssl._create_stdlib_context
from newspaper import Article
from bs4 import BeautifulSoup
from newspaper.article import ArticleException
import datetime
import traceback
import nltk
import yake
import googlesearch
import json
from os import path
from nltk.corpus import stopwords
from heapq import nlargest
from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation


def search_document(query):
    url = f"https://www.googleapis.com/customsearch/v1"
    params = {
        "key": "YOUR_API_KEY",
        "cx": "YOUR_SEARCH_ENGINE_ID",
        "q": query,
        "num": 3,
    }
    response = requests.get(url, params=params)
    data = response.json()
    urllist = []
    if "items" in data:
        urllist.append(data["items"][0]["link"])
        urllist.append(data["items"][1]["link"])
        urllist.append(data["items"][2]["link"])
        return urllist
    return None


user_input = input("Enter your query: ")
document_url = search_document(user_input)
if document_url:
    print("Found a relevant document:", document_url)
else:
    print("No relevant document found.")

def pdfs_and_text_extraction(topic):
    inp = ""
    version = 1
    while inp != "end":
        inp = input("What topic do you want to research about today")
        urllist = search_document(inp)
        for i in range(0, len(urllist)):
            response = requests.get(urllist[i])
            pdf_content = response.content
            pdf_file_path = "V" + str(version) + "_pdf" + str(i) + ".pdf"
            with open(pdf_file_path, "wb") as file:
                file.write(pdf_content)
            pdf_text = extract_text_from_pdf(pdf_file_path)
            common_proper_nouns = get_most_occurring_proper_nouns(pdf_text)
            print("Most occurring proper nouns in " + pdf_file_path + " are:")
            for noun, count in common_proper_nouns:
                print(noun, "-", count)
                print("The most prominent paragraphs maybe")
                print_paragraphs_with_proper_nouns(pdf_content, noun)
                print("-----------------(NEXT PROPER NOUN)---------------")
            print("====================================")

def extract_text_from_pdf(file_path):
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfFileReader(file)
        text = ""
        for page_num in range(reader.numPages):
            page = reader.getPage(page_num)
            text += page.extractText()
    return text


def get_most_occurring_proper_nouns(text, top_n=5):
    words = word_tokenize(text)
    tagged_words = pos_tag(words)
    proper_nouns = [word for word, pos in tagged_words if pos == "NNP"]
    most_common_proper_nouns = Counter(proper_nouns).most_common(top_n)
    return most_common_proper_nouns


def print_paragraphs_with_proper_nouns(text, proper_nouns):
    paragraphs = text.split("\n\n")

    for noun, _ in proper_nouns:
        print("Paragraphs with", noun + ":")
        for paragraph in paragraphs:
            if noun in paragraph:
                print(paragraph)
                print()



topics = ["US Politics news", "Premier League Football news", "Tech News"]
news_list = []


class News:
    def __init__(self, title, content, summary="", keywords=[], code=""):
        self.title = title
        self.content = content
        self.keywords = keywords
        self.summary = summary
        self.code = code

    def export(self):
        filename = "Daily_News/" + str(datetime.date.today()) + "_News.txt"
        listObj = []
        if not path.isfile(filename):
            listObj.append(
                {
                    "code": self.code,
                    "title": self.title,
                    "content": self.content,
                    "summary": self.summary,
                    "keywords": self.keywords,
                }
            )
            with open(filename, "w") as out_file:
                json.dump(listObj, out_file, indent=2)
        else:
            with open(filename) as out_file:
                listObj = json.load(out_file)
            with open(filename, "w") as out_file:
                listObj.append(
                    {
                        "code": self.code,
                        "title": self.title,
                        "content": self.content,
                        "summary": self.summary,
                        "keywords": self.keywords,
                    }
                )
                json.dump(listObj, out_file, indent=2)


def fetch_article(link):
    try:
        article = Article(link, language="en")
        article.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        article.download()
        article.parse()
        article.nlp()
        return News(
            title=article.title,
            content=article.text,
            summary=article.summary,
            keywords=article.keywords,
            code=make_unique_code(),
        )
    except ArticleException as e:
        print(f"newspaper3k failed, trying manual scraping for {link}")
        return fetch_article_manually(link)
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        return None


def fetch_article_manually(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            title = soup.find("title").text
            paragraphs = soup.find_all("p")
            content = "\n".join([p.get_text() for p in paragraphs])
            return News(
                title=title,
                content=content,
                summary=technical_summarize(content, 0.4),
                keywords=technical_keywords(content),
                code=make_unique_code(),
            )
        else:
            print(f"Failed to fetch article with status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Manual scraping failed for {url}: {e}")
        return None


def technical_summarize(content, per):
    tokens = nltk.word_tokenize(content)
    stopwords = set(STOP_WORDS)
    word_frequencies = {}
    for word in tokens:
        if word.lower() not in stopwords:
            if word.lower() not in punctuation:
                word_frequencies[word.lower()] = (
                    word_frequencies.get(word.lower(), 0) + 1
                )
    max_freq = max(word_frequencies.values())
    for word in word_frequencies.keys():
        word_frequencies[word] = word_frequencies[word] / max_freq
    sentence_tokens = nltk.sent_tokenize(content)
    sentence_scores = {}
    for sentence in sentence_tokens:
        for word in nltk.word_tokenize(sentence.lower()):
            if word in word_frequencies.keys():
                sentence_scores[sentence] = (
                    sentence_scores.get(sentence, 0) + word_frequencies[word]
                )
    summary_length = int(len(sentence_tokens) * per)
    summary = nlargest(summary_length, sentence_scores, key=sentence_scores.get)
    return " ".join(summary)


def technical_keywords(content):
    kw_extractor = yake.KeywordExtractor()
    keywords = kw_extractor.extract_keywords(content)
    return [kw[0] for kw in keywords]


def make_unique_code():
    return str(datetime.date.today()) + "-" + str(len(news_list))


def fetch_articles():
    global news_list
    news_list = []
    for topic in topics:
        for link in googlesearch.search(
            topic, lang="en", safe="off", num=3, stop=3, pause=2, verify_ssl=True
        ):
            news_item = fetch_article(link)
            if news_item:
                news_list.append(news_item)
                news_item.export()


if __name__ == "__main__":
    fetch_articles()

def getdocs(topics):
    linklist = []
    for topic in topics:
        for link in googlesearch.search(topic, lang="en", safe="off", num=3, stop=3, pause=2, verify_ssl=True):
            linklist.append(link)
