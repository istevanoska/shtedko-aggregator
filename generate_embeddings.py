import mysql.connector
from sentence_transformers import SentenceTransformer
import numpy as np
import pickle

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='marketi_database'
)
cursor = conn.cursor()

# Get products that don't have a valid embedding
cursor.execute("SELECT id, name FROM products2 WHERE name IS NOT NULL")
rows = cursor.fetchall()

for product_id, name in rows:
    try:
        embedding = model.encode(name)
        if np.any(np.isnan(embedding)):
            print(f"Embedding has NaN for product: {name} (ID: {product_id})")
            continue

        embedding_blob = pickle.dumps(embedding.astype(np.float32))
        cursor.execute("UPDATE products2 SET embedding = %s WHERE id = %s", (embedding_blob, product_id))
        print(f"✅ Embedded: {name} (ID: {product_id})")
    except Exception as e:
        print(f"❌ Failed embedding for {name} (ID: {product_id}): {e}")

conn.commit()
conn.close()
