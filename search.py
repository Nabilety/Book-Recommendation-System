import gzip
import json
import pandas
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

#pd.set_option('display.max_columns', None)

# Explore data
with gzip.open("goodreads_books.json.gz", 'r') as f:
    line = f.readline()
    print(line)

line_dict = json.loads(line)
print(line_dict)

# Pick lines of interest
def parse_fields(line):
    data = json.loads(line)
    return {
        "book_id": data["book_id"],
        "title": data["title_without_series"],
        "ratings": data["ratings_count"],
        "url": data["url"],
        "cover_image": data["image_url"]
    }

# Parse book metadata for each line
books_titles = []
with gzip.open("goodreads_books.json.gz", "r") as f:
    while True:
        line = f.readline()
        if not line:
            break
        fields = parse_fields(line)

        try:
            ratings = int(fields["ratings"])
        except ValueError:
            continue
        if ratings > 15:
            books_titles.append(fields)

# Processing book metadata with pandas
titles = pd.DataFrame.from_dict(books_titles) # Turn each dictionary in books_title into a row in the dataframe
titles["ratings"] = pd.to_numeric(titles["ratings"])
titles["mod_title"] = titles["title"].str.replace("[^a-zA-Z0-9 ]", "", regex=True)
titles["mod_title"] = titles["mod_title"].str.lower()
titles["mod_title"] = titles["mod_title"].str.replace("\s+", " ", regex=True)
titles = titles[titles["mod_title"].str.len() > 0] # Only take rows where len of mod_title greater than 0
titles.to_json("books_titles.json")

#with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    #print(titles.head(3))

# minimize the impact of common words using inverse document frequency matrix
# (equation is log(number of different titles / divided by the number of titles that particular word appear in.
# Lastly multiplying term frequencies with inverse document frequencies)
# This technique is called tf idf.

# Vectorizer takes list of strings and turns it into tf idf matrix
vectorizer = TfidfVectorizer()

tfidf = vectorizer.fit_transform(titles["mod_title"])

# Style column to build hyperlink html element for each of the column entries
def make_clickable(val):
    return '<a target="_blank" href="{}">Goodreads</a>'.format(val)

# Style to show the cover image
def show_image(val):
    return '<img src={}" width=50></img>'.format(val)

# Build code to turn search query into vector and match against our matrix
def search(query, vectorizer):
    #query = "fire upon the deep" # query
    processed = re.sub("[^a-zA-Z0-9 ]", "", query.lower()) # 2. process query
    query_vec = vectorizer.transform([processed]) # turn query into vector
    similarity = cosine_similarity(query_vec, tfidf).flatten() # search the tfidf matrix for our search query and tell us how much each row in the matrix is similar
    indices = np.argpartition(similarity, -10)[-10:] # from the above matrix, find the indices of the 10 largest similarities values
    results = titles.iloc[indices]
    results = results.sort_values("ratings", ascending=False) # incase of duplicate titles, take the rows with highest ratings
    return  results.head(5)
    #return results.head(5).style.format({'url': make_clickable, 'cover_image': show_image})
    #return results.head(5).style.format({'url': make_clickable})

print(search("Homegoing", vectorizer))

#Create a list of liked books
#liked_books = ["8132407", "31147619", "29983711"]
#liked_books = ["4408", "31147619", "29983711", "94013317", "9317691", "8153988", "20494944"]