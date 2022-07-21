# data-science

### Install the virtual environment
https://docs.python.org/3/library/venv.html
```
python3 -m venv ./path
```

### Activate the venv
```
source /venv/bin/activate
```

### Install spaCy with english model
```
pip install -U pip setuptools wheel
pip install -U spacy
python -m spacy download en_core_web_sm
```

### Run the Flask app
```
pip install Flask
export FLASK_APP=<filename>
flask run
```