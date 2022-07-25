import json
import os
import spacy
from flask import Flask, render_template, request, flash

app = Flask(__name__)
app.secret_key = "key"
app.templates_auto_reload = True 

global first
first = True

@app.route("/")
def index():
    global first
    if first:
        createArticles()
        createIndexes()
        first = False
    return loadTemplate()


def loadTemplate():
    searchTerm = request.args.get("search")
    if searchTerm:
        data = search(searchTerm.lower())
        if not data:
            flash(f'No matches for {searchTerm}')
    else:
        data = None
        searchTerm = ''
    return render_template("index.html", data=data, searchTerm=searchTerm)


def createArticles():
    """
    Reads in the database results and turns them into individual files
    """
    f = open('test.json', 'r')
    jsonString = json.loads(f.read())
    articleArray = jsonString['response']['results']
    for article in articleArray:
        id = article['id'].replace('/', '_')
        newF = open(f"./articles/{id}.txt", "w")
        newF.write(article['fields']['bodyText'])
        newF.close()
    f.close()


def createIndexes():
    """
    Reads each article file and generates indexes for each doc, entity, and frequency.
    """
    nlp = spacy.load("en_core_web_sm")  # will use english model
    index = open('index.json', "w")
    indexes = {
        'doc_lookup': {},
        'entity_lookup': {},
        'frequency_lookup': {},
    }
    count = 0

    for filename in os.listdir(f'{os.getcwd()}/articles'):
        # add doc indexes
        indexes['doc_lookup'][count] = filename
        # open in readonly mode
        with open(os.path.join(f'{os.getcwd()}/articles', filename), 'r') as f:
            doc = nlp(f.read())
            filtered_tokens = [preprocess_token(token) for token in doc if is_token_allowed(token)]
            for token in filtered_tokens:
                # add entity and frequency indexes
                if token in indexes['entity_lookup']:
                    if count not in indexes['entity_lookup'][token]:
                        indexes['entity_lookup'][token].append(
                            count)
                        indexes['frequency_lookup'][token] += 1
                else:
                    indexes['entity_lookup'][token] = [count]
                    indexes['frequency_lookup'][token] = 1
        count += 1
    export = json.dumps(indexes)
    index.write(export)
    index.close()


def is_token_allowed(token):
     """Only allow valid tokens which are not stop words and punctuation symbols."""
     if (not token or not token.text.strip() or token.is_stop or token.is_punct):
         return False
     return True


def preprocess_token(token):
    # Reduce token to its lowercase lemma form
    return token.lemma_.strip().lower()


def search(term):
    """Given a search term, lookup the entity in the index and get the article files that contain the search."""
    f = open('index.json', 'r')
    j = json.loads(f.read())
    docs = []
    main_term = getLowestFreq(term, j)
    print(main_term)
    if(main_term):
        for doc in j['entity_lookup'][main_term]:
            path = (j['doc_lookup'][f'{doc}'])[:-4].replace('_', '/')
            docs.append(
                f'https://www.theguardian.com/{path}')
    return docs


def getLowestFreq(term, j):
    terms = term.split(' ')
    lowest_count = 10000
    lowest_term = None
    for term in terms:
        if term in j['frequency_lookup'] and j['frequency_lookup'][term] < lowest_count:
            lowest_count = j['frequency_lookup'][term]
            lowest_term = term
    return lowest_term