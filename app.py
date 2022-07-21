import json
import os
import spacy
from flask import Flask, render_template, request, flash

app = Flask(__name__)
app.secret_key = "key"
app.templates_auto_reload = True


@app.route("/")
def index():
    createArticles()
    createIndexes()
    return loadTemplate()


def loadTemplate():
    searchTerm = request.args.get("search")
    if searchTerm:
        data = search(searchTerm)
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
        'freqency_lookup': {},
    }
    count = 0

    for filename in os.listdir(f'{os.getcwd()}/articles'):
        # add doc indexes
        indexes['doc_lookup'][count] = filename
        # open in readonly mode
        with open(os.path.join(f'{os.getcwd()}/articles', filename), 'r') as f:
            doc = nlp(f.read())
            for ent in doc.ents:
                # add entity and frequency indexes
                if ent.text in indexes['entity_lookup']:
                    if count not in indexes['entity_lookup'][ent.text]:
                        indexes['entity_lookup'][ent.text].append(
                            count)
                        indexes['freqency_lookup'][ent.text] += 1
                else:
                    indexes['entity_lookup'][ent.text] = [count]
                    indexes['freqency_lookup'][ent.text] = 1
        count += 1
    export = json.dumps(indexes)
    index.write(export)
    index.close()


def search(term):
    """Given a search term, lookup the entity in the index and get the article files that contain the search."""
    f = open('index.json', 'r')
    j = json.loads(f.read())
    docs = []
    for entity in j['entity_lookup']:
        if entity == term:
            for doc in j['entity_lookup'][entity]:
                path = (j['doc_lookup'][f'{doc}'])[:-4].replace('_', '/')
                docs.append(
                    f'https://www.theguardian.com/{path}')
    return docs
