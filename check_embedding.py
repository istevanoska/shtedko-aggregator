from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

product_name = "КРОМИД МЛАД ПАРЧЕ"  # Replace with any product name from your list
embedding = model.encode([product_name])[0]

print(f"Embedding for '{product_name}': {embedding}")
print(f"Is NaN: {np.isnan(embedding).any()}")
