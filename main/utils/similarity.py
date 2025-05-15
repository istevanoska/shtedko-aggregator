import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from .db import get_all_products  # We'll make this next


model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def get_similar_products(product_name, product_category, top_n=5):
    query_embedding = model.encode([product_name])

    products = get_all_products()

    similarities = []

    for p in products:
        try:
            if p['category'] != product_category or p['name'] == product_name:
                continue

            embedding = pickle.loads(p['embedding'])
            embedding = np.array(embedding).reshape(1, -1)
            sim = cosine_similarity(query_embedding, embedding)[0][0]

            similarities.append({
                'id': p['id'],  # Ensure the 'id' is included
                'name': p['name'],
                'similarity': round(sim, 2),
                'price': p.get('price'),
                'store': p.get('store'),
                'image': p.get('image_url'),

            })

        except Exception as e:
            continue

    return sorted(similarities, key=lambda x: x['similarity'], reverse=True)[:top_n]
