# utils/db.py
from main.models import Products2  # Make sure to import your model

def get_all_products():
    products = Products2.objects.values('id', 'name', 'category', 'embedding', 'price', 'store', 'image_url')
    return list(products)
