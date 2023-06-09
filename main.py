from fastapi import FastAPI
from fastapi.params import Body
from fastapi.middleware.cors import CORSMiddleware
from newspaper import Article
import re
import nltk
from nltk.corpus import stopwords
from urllib.parse import urlparse
import snscrape.modules.twitter as twitterScraper


nltk.download('stopwords')
stop = set(stopwords.words('english'))
alphabets= "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov|edu|me)"
digits = "([0-9])"

def remove_html(text):
    html_pattern = re.compile('<.*?>')
    return html_pattern.sub(r'', text)

def clean_text(text):
    text = " ".join([word.lower() for word in text.split() if word.lower() not in stop])
    text = " ".join([i for i in text.split() if len(i) > 2])
    return text

def lower_case(text):
    text= str(text).lower()
    return text


def split_into_sentences(text):
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    text = re.sub(digits + "[.]" + digits,"\\1<prd>\\2",text)
    if "..." in text: text = text.replace("...","<prd><prd><prd>")
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences

def string_magic(text):
    text = text.replace("\n","")
    text = text.replace("\"","")
    text = text.replace("CNN —", "")
    text = text.split('.')
    return text
    
def is_open_quote(s):
    stack = []
    for c in s:
        if c in ["'", '"', "`"]:
            if stack and stack[-1] == c:
                # this single-quote is close character
                stack.pop()
            else:
                # a new quote started
                stack.append(c)
        else:
            # ignore it
            pass

    return len(stack)

app = FastAPI()
origins = [
    "https://www.brainwashd.me",
    "https://app.brainwashd.me",
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World !!"}

@app.post("/parse/url")
async def parse_article(url: str):
    data = Article(url)
    data.download()
    data.parse()
    title = data.title
    author = data.authors
    text = data.text
    text = remove_html(text)
    text = text.replace("\n","")
    text = text.replace("\"","")
    source = urlparse(url).netloc
    source = source.split('.')[1]
    return {"source": source, "title": title, "author": author, "text":text}

@app.post('/parse/extension')
async def parse_article(url: str):
    data = Article(url)
    data.download()
    data.parse()
    title = data.title
    author = data.authors
    text = data.text
    text = string_magic(text)
    return {"title": title, "author": author, "text":text}
 

@app.post('/parse/tweet')
async def parse_article(id: str):
    # data = twitterScraper.TwitterTweetScraper(id).get_items()
    for i, item in enumerate(twitterScraper.TwitterTweetScraper(id).get_items()):
        if i>1:
            break
        tweet = {"author": item.user.displayname, "content": item.renderedContent, "profile": item.user.profileImageUrl, "verified": item.user.verified, "username": item.user.username}
    return tweet

# @app.post('/parse/facebook')
# async def parse_article(id: str):
#     post = graph.get_object(id=id, fields='description, message, name, target, caption, admin_creator')
#     print(post['description'])
#     return post