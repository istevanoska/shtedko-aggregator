# import pickle
# import numpy as np
# from sentence_transformers import SentenceTransformer
# from sklearn.metrics.pairwise import cosine_similarity
# from .db import get_all_products
#
#
# model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
#
# def get_similar_products(product_name, product_category, top_n=5):
#     query_embedding = model.encode([product_name])
#
#     products = get_all_products()
#
#     similarities = []
#
#     for p in products:
#         try:
#             if p['category'] != product_category or p['name'] == product_name:
#                 continue
#
#             embedding = pickle.loads(p['embedding'])
#             embedding = np.array(embedding).reshape(1, -1)
#             sim = cosine_similarity(query_embedding, embedding)[0][0]
#
#             similarities.append({
#                 'id': p['id'],
#                 'name': p['name'],
#                 'similarity': round(sim, 2),
#                 'price': p.get('price'),
#                 'store': p.get('store'),
#                 'image': p.get('image_url'),
#
#             })
#
#         except Exception as e:
#             continue
#
#     return sorted(similarities, key=lambda x: x['similarity'], reverse=True)[:top_n]
import pickle
import numpy as np
import re
from collections import Counter
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from .db import get_all_products


model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Define unimportant words to ignore in matching
STOPWORDS = {
    "парче", "свежо", "парчиња", "грам", "г.", "ком", "комад", "број", "бр", "парчиња"
}


def get_similar_products(product_name, product_category, top_n=5):
    query_embedding = model.encode([product_name])
    products = get_all_products()

    # Step 1: Filter products by category only
    filtered_products = [p for p in products if p['category'] == product_category and p['name'] != product_name]

    # Step 2: Build keyword frequency across products in this category
    all_keywords = []
    for p in filtered_products:
        all_keywords += tokenize(p['name'])

    keyword_freq = Counter(all_keywords)

    # Step 3: Tokenize the query
    query_keywords = set(tokenize(product_name))

    results = []

    for p in filtered_products:
        try:
            product_keywords = set(tokenize(p['name']))
            common_keywords = query_keywords & product_keywords

            if len(common_keywords) == 0:
                continue  # skip if no overlap

            # Base keyword score based on frequency in dataset
            keyword_score = sum(keyword_freq[k] for k in common_keywords)

            # Boost score if 2+ strong matches
            bonus = 0
            if len(common_keywords) >= 2:
                bonus += 5

            # Extra bonus for important matches
            for word in common_keywords:
                if word in ['пиво', 'вино', 'ракија', 'сок', 'млеко', 'кромид', 'јаболко']:
                    bonus += 10
                elif re.match(r'\d+(\.\d+)?л', word):  # match like 1л, 0.5л
                    bonus += 5

            # Embedding similarity
            embedding = pickle.loads(p['embedding'])
            embedding = np.array(embedding).reshape(1, -1)
            sim = cosine_similarity(query_embedding, embedding)[0][0]

            total_score = keyword_score + bonus + (sim * 5)

            results.append({
                'id': p['id'],
                'name': p['name'],
                'similarity': round(sim, 2),
                'keyword_score': keyword_score,
                'score': round(total_score, 2),
                'price': p.get('price'),
                'store': p.get('store'),
                'image': p.get('image_url'),
            })

        except Exception:
            continue

    return sorted(results, key=lambda x: x['score'], reverse=True)[:top_n]


def tokenize(name):
    """
    Tokenize product names, lowercase, clean, ignore short words and stopwords.
    Also captures numbers + volume (e.g., 1л, 0.5л).
    """
    name = name.lower()
    tokens = re.findall(r'\w+(?:\.\d+)?л|\d+|\w+', name)
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]