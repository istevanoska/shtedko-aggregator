# Shtedko 🛒🇲🇰

**Shtedko** is a Django-based web application that aggregates and compares product prices from major supermarkets in North Macedonia (e.g., Vero, Ramstore, Reptil).  
It helps users find the best deals, build shopping lists, discover cheaper alternatives, and even locate the nearest stores.

The project uses **scraped supermarket data stored in a SQL database** and integrates **Hugging Face models** (Sentence Transformers + text-generation API) to deliver smarter search, product matching, and suggestions.

> **Default branch:** `master`

---

## Key Features

### Product Search & Filtering
- Search products by name with support for **Latin ↔ Cyrillic transliteration**
- Filter by:
  - category
  - store
  - maximum price
  - active discounts
  - discounted-only
- Sorting options:
  - price (asc/desc) using an “effective price” (discount-aware)
  - name (asc/desc)
  - newest
  - popularity

### Smart Matching & Alternatives (ML)
- **Semantic product similarity** (Hugging Face Sentence Transformer)
  - Finds similar products based on name + category
  - Used in product listing search and product detail pages
- **Cheaper alternatives generator**
  - For each item in a shopping list, suggests a cheaper similar product (if available)

### Discounts & Store Highlights
- Homepage shows:
  - discounted products (popust)
  - stores grouped with their top discounted items
  - category list with emoji labels

### Shopping Lists
- Create and manage shopping lists (authenticated users)
- Add products to lists (quantity increases automatically)
- Update list item quantity / checked status (AJAX/JSON)
- Remove items from list
- Delete whole list
- Generate list of cheaper alternatives for list items

### Favorites
- Toggle favorite products (AJAX/JSON)
- Favorites page listing all saved products
- API endpoint to retrieve favorite product IDs for UI highlighting

### Price History & Statistics
- Product detail includes **price history chart data** from `product_history2`
- Stats page supports:
  - store selection
  - product selection / fuzzy matches
  - date range filtering
  - min / max / average / current price

### Nearest Store Finder (Driving Distance)
- Finds the **top 5 nearest stores** and **top 5 lowest fuel-cost stores**
- Uses **OpenRouteService** driving directions API
- Calculates:
  - driving distance (km)
  - estimated duration
  - estimated fuel usage (round trip)

### “Fridge Recipes” (Text Generation)
- Enter ingredients → generates a suggested Macedonian recipe
- Uses Hugging Face Inference API (Mistral model)

### Autocomplete Search Suggestions
- API endpoint returns product name suggestions (supports Latin input → Cyrillic lookup)

---

## Tech Stack

- **Backend:** Django (Python)
- **Database:** SQL (Django ORM + raw queries for history/statistics)
- **Machine Learning:** Hugging Face Sentence Transformers (semantic similarity)
- **AI Text Generation:** Hugging Face Inference API
- **Routing/Maps:** OpenRouteService (driving distance)
- **Data Source:** Web-scraped supermarket data stored in SQL

---

## Project Structure 
shtedko-aggregator/
├── main/ 
├── templates/ 
├── static/ 
├── manage.py
├── requirements.txt
└── README.md

## How to Run the Project

### 1. Clone the repository
```
git clone https://github.com/your-username/shtedko-aggregator.git
cd shtedko-aggregator
git checkout master
```

### 2. Create and activate virtual environment
```
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a .env file (or set system environment variables) for:
HUGGINGFACE_TOKEN – Hugging Face Inference API token
ORS_API_KEY – OpenRouteService API key
Database credentials (depending on your setup)
```
HUGGINGFACE_TOKEN=your_hf_token_here
ORS_API_KEY=your_ors_key_here
```

### 5. Run database migrations
```
python manage.py migrate
```

### 6. Start the development server
```
python manage.py runserver
```

The application will be available at:
http://127.0.0.1:8000/
