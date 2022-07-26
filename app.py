import spacy, os, datetime, requests, pickle
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
        apiCall()
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


def apiCall():
    """Connects to The Guardian api and retrieves articles from the past week."""
    today = datetime.date.today()
    from_date = today - datetime.timedelta(days=7)
    toady_string = today.strftime('%Y-%m-%d')
    from_string = from_date.strftime('%Y-%m-%d')
    page = 1
    added = True
    artObj = {}
    articles = open("articles.p", "ab")
    while added:
        url = f'http://content.guardianapis.com/search?page={page}&page-size=100&from-date={from_string}&to-date={toady_string}&order-by=newest&show-fields=bodyText&api-key=test'
        jsonString = requests.get(url).json()
        if 'results' in jsonString['response']:
            articleArray = jsonString['response']['results']
            for article in articleArray:
                artObj[article['id']] = article['fields']['bodyText']
            page+=1
        else:
            added = False
    pickle.dump(artObj, articles)
    articles.close()


def createIndexes():
    """
    Reads each article file and generates indexes for each doc, entity, and frequency.
    """
    nlp = spacy.load("en_core_web_sm")  # will use english model
    index = open('index.p', "ab")
    indexes = {
        'doc_lookup': {},
        'entity_lookup': {},
        'frequency_lookup': {},
    }
    count = 0
    articles = open('articles.p', 'rb')
    full_file = pickle.load(articles)
    for file in full_file:
        # add doc indexes
        indexes['doc_lookup'][count] = file
        doc = nlp(full_file[file])
        # filtered_tokens = [preprocess_token(token) for token in doc if is_token_allowed(token)]
        for token in doc:# filtered_tokens:
            if is_token_allowed(token):
                token = preprocess_token(token)
                # add entity and frequency indexes
                if token in indexes['entity_lookup']:
                    if count not in indexes['entity_lookup'][token]:
                        indexes['entity_lookup'][token].append(count)
                        indexes['frequency_lookup'][token] += 1
                else:
                    indexes['entity_lookup'][token] = [count]
                    indexes['frequency_lookup'][token] = 1
        count += 1
    pickle.dump(indexes, index)
    index.close()


def is_token_allowed(token):
     """Only allow valid tokens which are not stop words and punctuation symbols."""
     if (token.is_stop or token.is_punct):
         return False
     return True


def preprocess_token(token):
    # Reduce token to its lowercase lemma form
    return token.lemma_.strip().lower()


def search(term):
    """Given a search term, lookup the entity in the index and get the article files that contain the search."""
    f = open('index.p', 'rb')
    j = pickle.load(f)
    docs = []
    main_term = getLowestFreq(term, j)
    if main_term in j['entity_lookup']:
        for doc in j['entity_lookup'][main_term]:
            path = (j['doc_lookup'][doc])
            docs.append(
                f'https://www.theguardian.com/{path}')
    return docs


def getLowestFreq(term, j):
    """Reduces the search term to the lowest frequency word. Helpful to improve exact-match searches."""
    nlp = spacy.load("en_core_web_sm")  # will use english model
    terms = nlp(term)
    lowest_count = 10000
    lowest_term = None
    for term in terms:
        if is_token_allowed(term):
            term = preprocess_token(term)
            if term in j['frequency_lookup'] and j['frequency_lookup'][term] < lowest_count:
                lowest_count = j['frequency_lookup'][term]
                lowest_term = term
    return lowest_term