import gzip
import json
import pandas
import pandas as pd

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

titles = pd.DataFrame.from_dict(books_titles) # Turn each dictionary in books_title into a row in the dataframe
titles["ratings"] = pd.to_numeric(titles["ratings"])
titles["mod_title"] = titles["title"].str.replace("[^a-zA-Z0-9]", "", regex=True)
print(titles)

