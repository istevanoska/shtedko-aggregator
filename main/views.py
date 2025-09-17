import json
import requests
from django.core.paginator import Paginator
from django.db.models import Case, When, DecimalField
from django.shortcuts import render, redirect
from django.contrib.auth import login
import transliterate  # pip install transliterate


from .forms import RegisterForm
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from .models import ShoppingList, ShoppingListItem, Products2, Favorite
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .utils.similarity import get_similar_products
from django.shortcuts import render, get_object_or_404
from datetime import datetime




# Create your views here.

# sega kreirame funkcija koja ke pretstavuva nas prv view
# def index(response):
#     return HttpResponse("<h1>Tech with Tim!</h1>")
# def v1(response):
#     return HttpResponse("<h1>View 1!</h1>")
# #testiranje na connekcija do db
# def test_db_connection(request):
#     try:
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT VERSION();")
#             db_version = cursor.fetchone()
#         return HttpResponse(f"Connected to MySQL, version: {db_version[0]}")
#     except Exception as e:
#         return HttpResponse(f"Database connection failed: {str(e)}")

def index(response):
    return render(response, "main/index.html")


from django.db.models import Q, F, Count
from django.db.models.functions import Lower

from django.utils import timezone
from django.db.models import Q


def home(response):
    categories = Products2.objects.exclude(
        Q(category__isnull=True) | Q(category__exact='')
    ).values_list('category', flat=True).distinct()

    discounted_products = Products2.objects.filter(
        popust=True
    ).filter(
        Q(popust_date__gte=timezone.now().date()) | Q(popust_date__isnull=True)
    ).order_by('-price')[:12]

    CATEGORY_EMOJIS = {
        "Млеко": "🥛",
        "Хлеб": "🍞",
        "Овошје": "🍎",
        "Зеленчук": "🥦",
        "Месо": "🍖",
        "Козметика": "🧴",
        "Слатки": "🍫",
        "Јајца": "🥚",
        "Масло": "🛢️",
        "Брашно": "🌾",
    }

    discounted_products = Products2.objects.filter(
        popust=True
    ).order_by('-price')[:12]

    stores = Products2.objects.filter(popust=True).values_list('store', flat=True).distinct()

    stores_with_products = []
    for store in stores:
        cleaned = store.strip()

        store_filtered = Products2.objects.filter(store__iexact=cleaned)
        popust_filtered = store_filtered.filter(popust=True)

        # print(f"Store: {cleaned}")
        # print(f"Products after store filter: {store_filtered.count()}")
        # print(f"Products after popust filter: {popust_filtered.count()}")

        products = popust_filtered.order_by('-price')[:3]

        # if not products:
        #     print(f"No discounted products for {cleaned}")
        # else:
        #     print(f"Found {len(products)} products for {cleaned}")

        stores_with_products.append({
            'name': cleaned,
            'products': list(products),  # <--- Important!
            'count': products.count()
        })

    context = {
        'categories': categories,
        'discounted_products': discounted_products,
        'category_emojis': CATEGORY_EMOJIS,
        'stores_with_products': stores_with_products
    }

    return render(response, 'main/index.html', context)

# def base(response):
#     return render(response, "main/index.html")
from django.db.models import Q
from django.utils import timezone
from django.db.models import Case, When, DecimalField
from django.core.paginator import Paginator


def product_list(request):
    products = Products2.objects.all()
    search_query = request.GET.get('search', '').strip()
    original_query = request.GET.get('original_search', '').strip()
    cyrillic_query = request.GET.get('cyrillic_search', '').strip()

    # For backward compatibility with old search URLs
    if not original_query and search_query:
        original_query = search_query
        cyrillic_query = transliterate_latin_to_cyrillic(search_query)

    # If there's a search query, find matching products in both Latin and Cyrillic
    if original_query:
        products = products.filter(
            Q(name__icontains=original_query) |
            Q(name__icontains=cyrillic_query)
        )

    # Rest of your existing filters remain unchanged
    selected_categories = request.GET.getlist('category')
    if selected_categories:
        products = products.filter(category__in=selected_categories)

    show_active_discounts = request.GET.get('active_discounts')
    if show_active_discounts:
        products = products.filter(
            popust=True,
            popust_date__gte=timezone.now().date()
        )

    max_price = request.GET.get('max_price')
    if max_price and max_price.isdigit():
        products = products.filter(
            Q(popust=True, actual_price__lte=int(max_price)) |
            Q(popust=False, price__lte=int(max_price))
        )

    selected_stores = request.GET.getlist('store')
    if selected_stores:
        products = products.filter(store__in=selected_stores)

    sort = request.GET.get('sort', '')
    if sort == 'price_asc':
        products = products.annotate(
            effective_price=Case(
                When(popust=True, then='actual_price'),
                default='price',
                output_field=DecimalField()
            )
        ).order_by('effective_price')
    elif sort == 'price_desc':
        products = products.annotate(
            effective_price=Case(
                When(popust=True, then='actual_price'),
                default='price',
                output_field=DecimalField()
            )
        ).order_by('-effective_price')
    elif sort == 'name_asc':
        products = products.order_by('name')
    elif sort == 'name_desc':
        products = products.order_by('-name')
    elif sort == 'popular':
        products = products.order_by('-popularity')
    elif sort == 'newest':
        products = products.order_by('-created_at')

    show_discounted = request.GET.get('discounted')
    if show_discounted:
        products = products.filter(popust=True)

    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get similar products if there's a search query and results
    similar_products = None
    if original_query and page_obj:
        # Get the first product from search results as reference
        reference_product = page_obj[0]
        similar_products = get_similar_products(
            product_name=reference_product.name,
            product_category=reference_product.category,
            top_n=8
        )

        # Convert to Product objects
        similar_product_ids = [p['id'] for p in similar_products]
        similar_products = Products2.objects.filter(id__in=similar_product_ids)

        # Maintain order from similarity results
        id_to_product = {p.id: p for p in similar_products}
        similar_products = [id_to_product[pid] for pid in similar_product_ids if pid in id_to_product]

    # Favorite products logic
    fav_ids = []
    if request.user.is_authenticated:
        fav_ids = list(request.user.favorites.all().values_list('product_id', flat=True))

    context = {
        'page_obj': page_obj,
        'categories': Products2.objects.values_list('category', flat=True).distinct(),
        'selected_categories': selected_categories,
        'selected_max_price': max_price,
        'selected_stores': selected_stores,
        'selected_sort': sort,
        'search_query': original_query or search_query,  # Show the original query in the UI
        'fav_ids': fav_ids,
        'similar_products': similar_products,
    }
    return render(request, 'main/product_list.html', context)


# Helper function for transliteration
def transliterate_latin_to_cyrillic(text):
    mapping = {
        'dzh': 'џ', 'dzs': 'џ', 'dsh': 'џ',
        'zh': 'ж', 'ch': 'ч', 'sh': 'ш', 'lj': 'љ', 'nj': 'њ', 'kj': 'ќ', 'dj': 'ѓ',
        'zs': 'ж', 'hs': 'ш', 'cx': 'ч', 'sx': 'ш', 'jx': 'ж',
        'tz': 'ц', 'ts': 'ц', 'tc': 'ц', 'dz': 'џ',
        'a': 'а', 'b': 'б', 'v': 'в', 'g': 'г', 'd': 'д', 'e': 'е', 'z': 'з', 'i': 'и',
        'j': 'ј', 'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н', 'o': 'о', 'p': 'п', 'r': 'р',
        's': 'с', 't': 'т', 'u': 'у', 'f': 'ф', 'h': 'х', 'c': 'ц',
        'y': 'ј', 'w': 'в', 'x': 'кс', 'q': 'к',
        'ia': 'ја', 'ie': 'је', 'io': 'јо', 'iu': 'ју'
    }

    text = text.lower()
    for lat, cyr in mapping.items():
        text = text.replace(lat, cyr)
    return text

from django.contrib.auth import authenticate, login

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Save the form, but don't commit to DB yet
            user = form.save(commit=False)
            raw_password = form.cleaned_data.get('password1')
            user.save()

            # Authenticate with raw credentials
            authenticated_user = authenticate(username=user.username, password=raw_password)
            if authenticated_user is not None:
                login(request, authenticated_user)
                return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'main/register.html', {'form': form})



def custom_logout(request):
    logout(request)

    categories = Products2.objects.exclude(
        Q(category__isnull=True) | Q(category__exact='')
    ).values_list('category', flat=True).distinct()

    discounted_products = Products2.objects.filter(
        popust=True
    ).filter(
        Q(popust_date__gte=timezone.now().date()) | Q(popust_date__isnull=True)
    ).order_by('-price')[:12]

    stores = Products2.objects.filter(popust=True).values_list('store', flat=True).distinct()
    stores_with_products = []
    for store in stores:
        cleaned = store.strip()
        store_filtered = Products2.objects.filter(store__iexact=cleaned)
        popust_filtered = store_filtered.filter(popust=True)
        products = popust_filtered.order_by('-price')[:3]
        if products.exists():
            stores_with_products.append({
                'name': cleaned,
                'products': list(products),
                'count': products.count()
            })

    context = {
        'categories': categories,
        'discounted_products': discounted_products,
        'stores_with_products': stores_with_products
    }
    return render(request, 'main/index.html', context)


@login_required
def view_lists(request):
    user_lists = ShoppingList.objects.filter(user=request.user)
    return render(request, 'main/lists.html', {'user_lists': user_lists})


@login_required
def create_list(request):
    if request.method == 'POST':
        list_name = request.POST.get('list_name', '').strip()

        # Transliterate Cyrillic to Latin if needed
        try:
            if any(ord(char) > 127 for char in list_name):  # Check for non-ASCII
                list_name = transliterate.translit(list_name, reversed=True)
        except:
            pass  # Fall through to original name

        try:
            ShoppingList.objects.create(user=request.user, name=list_name)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })


@login_required
def view_list(request, list_id):
    shopping_list = get_object_or_404(ShoppingList, id=list_id, user=request.user)
    items = ShoppingListItem.objects.filter(shopping_list=shopping_list)

    # Debugging: Log the items being passed to the template
    print(f"Items in list {shopping_list.name}: {items}")

    return render(request, 'main/list_detail.html', {'shopping_list': shopping_list, 'items': items})

@login_required
def delete_list(request, list_id):
    shopping_list = get_object_or_404(ShoppingList, id=list_id, user=request.user)
    if request.method == 'POST':
        shopping_list.delete()
    return redirect('view_lists')


@login_required
@require_POST
def remove_from_list(request, item_id):
    list_item = get_object_or_404(ShoppingListItem, id=item_id, list__user=request.user)
    list_item.delete()
    return redirect('view_list', list_id=list_item.list.id)


@login_required
@csrf_exempt
def toggle_list_item(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        completed = request.POST.get('completed') == 'true'

        list_item = get_object_or_404(ShoppingListItem, id=item_id, list__user=request.user)
        list_item.completed = completed
        list_item.save()

        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@csrf_exempt
@require_POST
@login_required
def add_to_list(request):
    try:
        # Only allow POST
        if request.method != "POST":
            return JsonResponse({'success': False, 'message': 'Invalid request'}, status=405)

        # Extract data from POST request
        data = json.loads(request.body)
        product_id = data.get('product_id')
        list_id = data.get('list_id')

        if not product_id or not list_id:
            return JsonResponse({'success': False, 'message': 'Missing product or list ID'}, status=400)

        # Fetch shopping list and product
        shopping_list = get_object_or_404(ShoppingList, id=list_id, user=request.user)
        product = get_object_or_404(Products2, id=product_id)

        # Get or create the item
        item, created = ShoppingListItem.objects.get_or_create(
            shopping_list=shopping_list,
            product=product,
            defaults={'quantity': 1}
        )

        if not created:
            item.quantity += 1
            item.save()

        return JsonResponse({
            'success': True,
            'message': f'{product.name} added to list',
            'quantity': item.quantity
        })

    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
def get_user_lists(request):
    if not request.user.is_authenticated:
        return JsonResponse({'lists': []})

    lists = ShoppingList.objects.filter(user=request.user).values('id', 'name')
    return JsonResponse({'lists': list(lists)})


def product_detail(request, product_id):
    product = get_object_or_404(Products2, id=product_id)

    chart_data = []
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT scraped_date, price 
            FROM product_history2 
            WHERE name = %s AND store LIKE %s
            ORDER BY scraped_date ASC
        """, [product.name, '%' + product.store + '%'])

        result = cursor.fetchall()
        chart_data = [{
            'date': row[0].isoformat(),
            'price': float(row[1])
        } for row in result]

    similar_products = get_similar_products(product.name, product.category)

    return render(request, 'main/product_detail.html', {
        'product': product,
        'similar_products': similar_products,
        'chart_data': chart_data,
        'price_history': chart_data
    })
@login_required
@require_POST
@csrf_exempt
def remove_from_list(request, item_id):
    try:
        list_item = get_object_or_404(ShoppingListItem, id=item_id, shopping_list__user=request.user)
        list_item.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def get_store_products(request):
    store = request.GET.get('store')
    if not store:
        return JsonResponse({'error': 'Store parameter missing'}, status=400)

    products = Products2.objects.filter(
        store=store,
        popust=True
    )

    products_data = [
        {
            'name': p.name,
            'id': p.id,
            'price': str(p.price),
            'actual_price': str(p.actual_price),
            'image_url': p.image_url
        }
        for p in products
    ]

    return JsonResponse({'products': products_data})


from difflib import get_close_matches
from django.db import connection


def stats_view(request):
    store = request.GET.get('store', '').strip()
    query = request.GET.get('query', '').strip()
    selected_product = request.GET.get('selected_product', '').strip()

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
    except (ValueError, TypeError):
        start_date_obj = None
        end_date_obj = None

    chart_data = []
    matched_name = None
    similar_products = []
    exact_match = False
    current_price = None
    min_price = None
    max_price = None
    avg_price = None

    if store and (query or selected_product):
        # First check for exact match if we have a query (not selected product)
        if query and not selected_product:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT name 
                    FROM product_history2 
                    WHERE store LIKE %s AND name = %s
                    LIMIT 1
                """, ['%' + store + '%', query])
                exact_match_result = cursor.fetchone()

                if exact_match_result:
                    matched_name = exact_match_result[0]
                    exact_match = True

        # If no exact match or we have selected_product, find similar products
        if not exact_match:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT name FROM product_history2 
                    WHERE store LIKE %s
                """, ['%' + store + '%'])
                all_store_products = [row[0] for row in cursor.fetchall()]

                search_term = selected_product if selected_product else query
                similar_products = []

                if search_term:
                    from difflib import get_close_matches
                    string_matches = get_close_matches(
                        search_term,
                        all_store_products,
                        n=10,
                        cutoff=0.3
                    )

                    query_lower = search_term.lower()
                    contains_matches = [
                                           p for p in all_store_products
                                           if query_lower in p.lower()
                                       ][:10]

                    all_matches = list(set(string_matches + contains_matches))
                    similar_products = [(p, 100) for p in all_matches[:10]]  # Using 100% for all for simplicity

        # If we have a selected product or exact match, get price history
        product_to_search = selected_product if selected_product else matched_name
        if product_to_search:
            base_sql = """
                SELECT scraped_date, price 
                FROM product_history2 
                WHERE name = %s AND store LIKE %s
            """
            params = [product_to_search, '%' + store + '%']

            if start_date_obj and end_date_obj:
                base_sql += " AND scraped_date BETWEEN %s AND %s"
                params.extend([start_date_obj, end_date_obj])
            elif start_date_obj:
                base_sql += " AND scraped_date >= %s"
                params.append(start_date_obj)
            elif end_date_obj:
                base_sql += " AND scraped_date <= %s"
                params.append(end_date_obj)

            base_sql += " ORDER BY scraped_date ASC"

            with connection.cursor() as cursor:
                cursor.execute(base_sql, params)
                result = cursor.fetchall()
                chart_data = [{
                    'date': row[0].isoformat(),
                    'price': float(row[1])
                } for row in result]

                if result:
                    prices = [float(row[1]) for row in result]
                    current_price = prices[-1]
                    min_price = min(prices)
                    max_price = max(prices)
                    avg_price = sum(prices) / len(prices)

    context = {
        'chart_data': chart_data,
        'matched_name': matched_name or selected_product,
        'query': query,
        'store': store,
        'similar_products': similar_products,
        'exact_match': exact_match,
        'start_date': start_date,
        'end_date': end_date,
        'current_price': current_price,
        'min_price': min_price,
        'max_price': max_price,
        'avg_price': avg_price,
    }

    # Debug output - remove in production
    # print("Context being sent to template:")
    for key, value in context.items():
        print(f"{key}: {value}")

    return render(request, 'main/stats.html', context)

# def get_driving_distance(user_lat, user_lon, store_lat, store_lon, api_key):
#     url = "https://maps.googleapis.com/maps/api/distancematrix/json"
#     params = {
#         "origins": f"{user_lat},{user_lon}",
#         "destinations": f"{store_lat},{store_lon}",
#         "key": api_key,
#         "units": "metric"
#     }
#     response = requests.get(url, params=params)
#     data = response.json()
#     print("Distance Matrix API response:", data)  # <-- add this
#
#     if data['status'] == 'OK':
#         element = data['rows'][0]['elements'][0]
#         if element['status'] == 'OK':
#             distance_km = element['distance']['value'] / 1000
#             duration = element['duration']['text']
#             return distance_km, duration
#     return None, None

import openrouteservice

def get_driving_distance(user_lat, user_lon, store_lat, store_lon, api_key):
    client = openrouteservice.Client(key=api_key)
    coords = ((user_lon, user_lat), (store_lon, store_lat))  # ORS expects (lon, lat)

    try:
        route = client.directions(coords, profile='driving-car', format='geojson')
        distance_m = route['features'][0]['properties']['segments'][0]['distance']  # meters
        duration_s = route['features'][0]['properties']['segments'][0]['duration']  # seconds

        distance_km = distance_m / 1000
        duration_min = round(duration_s / 60)
        duration = f"{duration_min} min"

        return distance_km, duration
    except Exception as e:
        print("ORS error:", e)
        return None, None




from django.conf import settings

from django.shortcuts import render

def nearby_stores_view(request):
    user_lat = request.GET.get('latitude')
    user_lon = request.GET.get('longitude')
    fuel_consumption = request.GET.get('fuel_consumption')
    store_chain = request.GET.get('store_chain')

    print("Received params:", user_lat, user_lon, fuel_consumption, store_chain)

    if not all([user_lat, user_lon, fuel_consumption, store_chain]):
        return render(request, "main/nearby_stores.html", {
            "error": "Missing parameters.",
            "results": [],
        })

    user_lat = float(user_lat)
    user_lon = float(user_lon)
    fuel_consumption = float(fuel_consumption)
    store_chain = store_chain.lower()

    stores = [
        {"name": "Reptil Market Ruzveltova", "lat": 42.0040878561334, "lon": 21.41538436528707, "chain": "reptil"},
        {"name": "Reptil Market Crniche", "lat": 41.98424985514346, "lon": 21.42854499185496, "chain": "reptil"},
        {"name": "Reptil Market Butel", "lat": 42.03151299550568, "lon": 21.44460271127004, "chain": "reptil"},
        {"name": "Reptil Market Avtokomanda", "lat": 42.00314285371043, "lon": 21.464809841955148, "chain": "reptil"},
        {"name": "Reptil Market Radishani", "lat": 42.05659527027985, "lon": 21.451523714968985, "chain": "reptil"},
        {"name": "Reptil Market Madzari", "lat": 42.00080136926024, "lon": 21.488524284283873, "chain": "reptil"},
        {"name": "Reptil Market Lisice", "lat": 41.975386066287584, "lon": 21.472738657297704, "chain": "reptil"},
        {"name": "Reptil Market Ardorom bul.Jane Sandanski", "lat": 41.98410917961027, "lon": 21.46690158428389, "chain": "reptil"},
        {"name": "Reptil Market Bardovci", "lat": 42.025668068096394, "lon": 21.37584645411437, "chain": "reptil"},
        {"name": "Reptil Market Aerodrom", "lat": 41.985188473060354, "lon": 21.453380984283882, "chain": "reptil"},
        {"name": "Reptil Market Shop & Go", "lat": 41.99948987076041, "lon": 21.423976899626428, "chain": "reptil"},
        {"name": "Reptil Market Zelen Pazar", "lat": 41.991862538872645, "lon": 21.433574943394476, "chain": "reptil"},
        {"name": "Reptil Market Drzhavna Bolnica", "lat": 41.99082095885179, "lon": 21.424983018422854, "chain": "reptil"},
        {"name": "Reptil Market Kisela Voda", "lat": 41.98173349419106, "lon": 21.43810738428388, "chain": "reptil"},
        {"name": "Reptil Market Aerodrom", "lat": 41.9780, "lon": 21.4680, "chain": "reptil"},
        {"name": "Reptil Market Karposh 3 br.9", "lat": 42.007022300132036, "lon": 21.400571526550074, "chain": "reptil"},
        {"name": "Reptil Market Karposh br.6", "lat": 42.00112199222344, "lon": 21.41212279925285, "chain": "reptil"},
        {"name": "Reptil Market Karposh br.5", "lat": 42.007478018986724, "lon": 21.395736283910317, "chain": "reptil"},
        {"name": "Reptil Market Porta Vlae", "lat": 42.00816321194575, "lon": 21.370438003817473, "chain": "reptil"},
        {"name": "Reptil Market Nerezi", "lat": 41.995647756137735, "lon": 21.39414196856774, "chain": "reptil"},
        {"name": "Reptil Market Vlae", "lat": 42.011056469322966, "lon": 21.374480029937953, "chain": "reptil"},
        {"name": "Reptil Market Centar Pestaloci", "lat": 41.99836555442384, "lon": 21.421861676512417, "chain": "reptil"},
        {"name": "Ramstore Vardar", "lat": 41.9981, "lon": 21.4325, "chain": "ramstore"},
        {"name": "Ramstore City Mall", "lat": 42.0045, "lon": 21.3919, "chain": "ramstore"},
        {"name": "Vero Aerodrom", "lat": 41.9980, "lon": 21.4680, "chain": "vero"},
        {"name": "Vero Taftalidze", "lat": 41.9972, "lon": 21.4085, "chain": "vero"},
        {"name": "Vero GTC", "lat": 41.9981, "lon": 21.4325, "chain": "vero"},
        {"name": "Vero Čair", "lat": 42.0000, "lon": 21.4330, "chain": "vero"},
    ]

    filtered_stores = [s for s in stores if s["chain"] == store_chain]
    print("Filtered stores:", filtered_stores)

    results = []
    for store in filtered_stores:
        distance_km, duration = get_driving_distance(
            user_lat,
            user_lon,
            store["lat"],
            store["lon"],
            settings.ORS_API_KEY  # Pass your ORS key here
        )
        if distance_km is not None:
            gas_used = (distance_km * 2 * fuel_consumption) / 100  # round trip
            results.append({
                "store": store["name"],
                "distance_km": round(distance_km, 2),
                "duration": duration,
                "gas_used": round(gas_used, 2),
                "latitude": store["lat"],
                "longitude": store["lon"],
            })

    nearest_stores_top5 = sorted(results, key=lambda x: x['distance_km'])[:5]
    least_gas_stores_top5 = sorted(results, key=lambda x: x['gas_used'])[:5]

    context = {
        "results": results,
        "nearest_stores": nearest_stores_top5,
        "least_gas_stores": least_gas_stores_top5,
        "latitude": user_lat,
        "longitude": user_lon,
        "fuel_consumption": fuel_consumption,
        "store_chain": store_chain.title(),
    }

    return render(request, "main/nearby_stores.html", context)


from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def fridge_recipes(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    try:
        data = json.loads(request.body)
        ingredients = data.get('ingredients', '')

        payload = {
            "inputs": f"User has the following ingredients: {ingredients}. Suggest a Macedonian recipe using them. Return only one recipe with name and preparation steps."
        }
        headers = {
            "Authorization": f"Bearer {settings.HUGGINGFACE_TOKEN}"
        }
        response = requests.post(
            "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1",
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            print(f"Hugging Face API error {response.status_code}: {response.text}")
            return JsonResponse({"error": "Не може да се генерира рецепт. Обидете се повторно."}, status=500)

        result = response.json()
        if isinstance(result, dict) and result.get("error"):
            print(f"HF API returned error: {result['error']}")
            return JsonResponse({"error": "Не може да се генерира рецепт. Обидете се повторно."}, status=500)

        generated_text = result[0]['generated_text']

        return JsonResponse({
            "recipes": [{
                "title": "Предлог Рецепт",
                "description": generated_text
            }]
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": "Не може да се генерира рецепт. Обидете се повторно."}, status=500)


LATIN_TO_CYRILLIC = {
    'dzh': 'џ', 'ch': 'ч', 'sh': 'ш', 'zh': 'ж', 'lj': 'љ', 'nj': 'њ', 'kj': 'ќ', 'dj': 'ѓ',
    'a': 'а', 'b': 'б', 'v': 'в', 'g': 'г', 'd': 'д', 'e': 'е', 'z': 'з', 'i': 'и',
    'j': 'ј', 'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н', 'o': 'о', 'p': 'п', 'r': 'р',
    's': 'с', 't': 'т', 'u': 'у', 'f': 'ф', 'h': 'х', 'c': 'ц',
}

def transliterate_latin_to_cyrillic(text):
    result = ''
    i = 0
    while i < len(text):
        if text[i:i+3].lower() in LATIN_TO_CYRILLIC:
            result += LATIN_TO_CYRILLIC[text[i:i+3].lower()]
            i += 3
        elif text[i:i+2].lower() in LATIN_TO_CYRILLIC:
            result += LATIN_TO_CYRILLIC[text[i:i+2].lower()]
            i += 2
        elif text[i].lower() in LATIN_TO_CYRILLIC:
            result += LATIN_TO_CYRILLIC[text[i].lower()]
            i += 1
        else:
            result += text[i]
            i += 1
    return result

def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'suggestions': []})

    cyrillic_query = transliterate_latin_to_cyrillic(query)

    suggestions = Products2.objects.filter(
        name__icontains=cyrillic_query
    ).values_list('name', flat=True).distinct()[:10]

    if not suggestions:
        suggestions = Products2.objects.filter(
            name__icontains=query
        ).values_list('name', flat=True).distinct()[:10]

    return JsonResponse({'suggestions': list(suggestions)})


def header(request):
    return render(request, "main/header.html")


@require_POST
def toggle_favorite(request):
    # Handle unauthenticated users
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required',
            'login_required': True,
            'login_url': f'/login/?next={request.META.get("HTTP_REFERER", "/")}'
        }, status=401)

    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')

        if not product_id:
            return JsonResponse({'success': False, 'message': 'Product ID is required'}, status=400)

        product = Products2.objects.get(id=product_id)

        # Check if favorite exists
        favorite_exists = Favorite.objects.filter(
            user=request.user,
            product=product
        ).exists()

        if favorite_exists:
            # Delete if exists
            Favorite.objects.filter(
                user=request.user,
                product=product
            ).delete()
            return JsonResponse({
                'success': True,
                'action': 'removed',
                'is_favorite': False,
                'product_id': product_id
            })
        else:
            # Create if doesn't exist
            Favorite.objects.create(
                user=request.user,
                product=product
            )
            return JsonResponse({
                'success': True,
                'action': 'added',
                'is_favorite': True,
                'product_id': product_id
            })

    except Products2.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Product not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
@login_required
def favorites_list(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('product')
    return render(request, 'main/favorites.html', {'favorites': favorites})

@login_required
def get_favorites(request):
    if request.user.is_authenticated:
        favorites = Favorite.objects.filter(user=request.user).values_list('product_id', flat=True)
        return JsonResponse({
            'success': True,
            'favorites': list(favorites)
        })
    return JsonResponse({'success': False, 'message': 'User not authenticated'})

from django.http import JsonResponse
from django.db import connection
from datetime import datetime

def product_history_api(request):
    store = request.GET.get('store', '').strip()
    product = request.GET.get('product', '').strip()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not store or not product:
        return JsonResponse({'error': 'Missing store or product'}, status=400)

    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date and start_date != 'None' else None
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date and end_date != 'None' else None
    except (ValueError, TypeError):
        start_date_obj = None
        end_date_obj = None

    base_sql = """
        SELECT scraped_date, price 
        FROM product_history2 
        WHERE name = %s AND store LIKE %s
    """
    params = [product, f"%{store}%"]

    if start_date_obj and end_date_obj:
        base_sql += " AND scraped_date BETWEEN %s AND %s"
        params.extend([start_date_obj, end_date_obj])
    elif start_date_obj:
        base_sql += " AND scraped_date >= %s"
        params.append(start_date_obj)
    elif end_date_obj:
        base_sql += " AND scraped_date <= %s"
        params.append(end_date_obj)

    base_sql += " ORDER BY scraped_date ASC"

    with connection.cursor() as cursor:
        cursor.execute(base_sql, params)
        rows = cursor.fetchall()
        data = [{'date': row[0].isoformat(), 'price': float(row[1])} for row in rows]

    return JsonResponse({'data': data})
