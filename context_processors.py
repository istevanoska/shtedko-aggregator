# In your context_processors.py
def category_translations(request):
    return {
        'CATEGORY_TRANSLATIONS': {
            'Electronics': 'Електроника',
            'Clothing': 'Облека',
            'Home': 'Домаќинство',
            'Sports': 'Спорт',
            'Toys': 'Играчки',
            # Add all categories
        }
    }