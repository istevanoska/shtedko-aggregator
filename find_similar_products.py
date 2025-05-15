import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import mysql.connector
import re

# Load model
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Preprocess helper
def preprocess(text):
    return re.sub(r'[^а-шА-Шa-zA-Z0-9\s]', '', text.lower()).strip()

# DB connection
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='marketi_database'
)
cursor = conn.cursor(dictionary=True)

# Search term
query = "АРГЕТА ПАШТЕТА КОКОШКИНА 95Г"
query_processed = preprocess(query)
query_embedding = model.encode([query_processed])

# Get the category of the query product
cursor.execute("SELECT category FROM products2 WHERE name = %s LIMIT 1", (query,))
row = cursor.fetchone()

if row:
    category = row['category']
    print(f"\n🔍 Top similar products to '{query}' in category '{category}':\n")

    cursor.execute("SELECT name, embedding FROM products2 WHERE category = %s", (category,))
else:
    print(f"Category not found for '{query}', using all products instead.\n")
    cursor.execute("SELECT name, embedding FROM products2")

products = cursor.fetchall()

similarities = []

for product in products:
    try:
        product_embedding = pickle.loads(product['embedding'])
        product_embedding = np.array(product_embedding).reshape(1, -1)

        if product_embedding.shape[1] != 384:
            raise ValueError(f"Invalid shape {product_embedding.shape}")

        sim = cosine_similarity(query_embedding, product_embedding)[0][0]

        if sim >= 0.6:
            similarities.append((product['name'], sim))

    except Exception as e:
        print(f"Error with product {product['name']}: {e}")

similarities.sort(key=lambda x: x[1], reverse=True)
for name, sim in similarities[:10]:
    print(f"{name}: {sim:.2f}")
