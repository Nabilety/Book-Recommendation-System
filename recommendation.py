import pandas as pd

#Create a list of liked books
liked_books = ["4408", "31147619", "29983711", "94013317", "9317691", "8153988", "20494944"]

# use goodreads_interaction to find each user
# and how much they liked each book to create some recommendations for us in two steps:
# 1. find all users who liked same books as us
# 2. find all the books liked by those users (we probably like the same, assumption)

#!head book_id_map.csv

csv_book_mapping = {}
with open("book_id_map.csv", "r") as f:
    while True:
        line = f.readline()
        if not line:
            break
        # reading each line, removing newline characters, splitting line on comma and assigning first part to csv_id
        # and second part to book_id
        csv_id, book_id = line.strip().split(",")
        csv_book_mapping[csv_id] = book_id # dict will have csv_id as keys and values as will be the ids from search.py

# go through each line goodreads_interaction, for each user for each book.
# line by line, check if the book is in our liked books and if the rating is greater than 4.
# then we will add that user who read the same book and rated the book high in our overlap_user set
overlap_users = set()
with open("goodreads_interactions.csv", "r") as f:
    while True:
        line = f.readline()
        if not line:
            break
        user_id, csv_id, _, rating, _ = line.split(",")

        if user_id in overlap_users:
            continue
        try:
            rating = int(rating)
        except ValueError:
            continue
        book_id = csv_book_mapping[csv_id] # turn csv_id into a book_id

        if book_id in liked_books and rating >=4:
            overlap_users.add(user_id)

# next step is finding what books those users liked
rec_lines = []
with open("goodreads_interactions.csv", "r") as f:
    while True:
        line = f.readline()
        if not line:
            break
        user_id, csv_id, _, rating, _ = line.split(",")

        if user_id in overlap_users:
            book_id = csv_book_mapping[csv_id]
            rec_lines.append([user_id, book_id, rating]) # rec_lines will only consist of books liked by users who read same books as us

print(len(overlap_users)) # how many users liked book we also liked
print(len(rec_lines)) # how many total books those users read (which is quite a lot). So we will need filtering

# find a way to rank recommendations
recs = pd.DataFrame(rec_lines, columns=["user_id", "book_id", "rating"])
recs["book_id"] = recs["book_id"].astype(str) # make sure book_id is string

# take a look at top recommendations.
# Using value_count to look through our dataframe and find which book_id occurs the most
# Meaning, our top recommendations will be the book_ids that occured most frequently
top_recs = recs["book_id"].value_counts().head(10)
top_recs = top_recs.index.values # get values from the indexes

# now all left is to get from book_id to title
books_titles = pd.read_json("books_titles.json")
books_titles["book_id"] = books_titles["book_id"].astype(str)
print(books_titles.head())

# find all book titles where the book_id is in the top recommendations
print(books_titles[books_titles["book_id"].isin(top_recs)])

# the issues that arises now is that above recommendations are very very popular books
# meaning, not a lot of difference between most popular books in general and the ones we got recommended
# we need a way to select books that are more popular in our set, differentiating us from generic books.
# We will look at what books they liked and not necessarily popular among all users.

# Instead of top_recs we will look at all recommendations
all_recs = recs["book_id"].value_counts()
all_recs = all_recs.to_frame().reset_index() # here our columns are incorrect: book_id counts how many times each book appeared among the recommendations. Index is the actual book_id.
all_recs.columns = ["book_id", "book_count"]

# we're gonna merge with books titles with inner merge. Meaning if the data does not exist in both. We get rid of the row
all_recs = all_recs.merge(books_titles, how="inner", on="book_id")

# Now we create a score to sort the recommendations.
# So of all the users, who liked books we liked. How many of them also like this book.
# We then penalize this based on how popular the book was in the general set.

# If a book is very popular in our set, and less popular on goodreads. It's gonna have highly recommended.
# meaning we're looking for books that are popular among users like us but aren't popular in general
all_recs["score"] = all_recs["book_count"] * (all_recs["book_count"] / all_recs["ratings"])
all_recs.sort_values("score", ascending=False).head(10)

# Now we filter out books with few ratings, and accept only ratings above 75
popular_recs = all_recs[all_recs["book_count"] > 75].sort_values("score", ascending=False)

def make_clickable(val):
    return '<a target="_blank" href="{}">Goodreads</a>'.format(val)

# Style to show the cover image
def show_image(val):
    return '<img src={}" width=50></img>'.format(val)

popular_recs[~popular_recs["book_id"].isin(liked_books)].head(10).style.format({'url': make_clickable, 'cover_image': show_image})