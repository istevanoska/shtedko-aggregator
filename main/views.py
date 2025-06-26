import json
import requests
from django.core.paginator import Paginator
from django.db.models import Case, When, DecimalField
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegisterForm
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from .models import ShoppingList, ShoppingListItem, Products2
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
    return render(response, "main/base.html")


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

        print(f"Store: {cleaned}")
        print(f"Products after store filter: {store_filtered.count()}")
        print(f"Products after popust filter: {popust_filtered.count()}")

        products = popust_filtered.order_by('-price')[:3]

        if not products:
            print(f"No discounted products for {cleaned}")
        else:
            print(f"Found {len(products)} products for {cleaned}")

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

    return render(response, 'main/base.html', context)

# def base(response):
#     return render(response, "main/base.html")
def product_list(request):
    products = Products2.objects.all()
    query = request.GET.get("q")
    products = Products2.objects.all()

    if query:
        products = products.filter(name__icontains=query)

    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(name__icontains=search_query)

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

    # Store filter
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
        products = products.order_by('-popularity')  # Assuming you have a popularity field
    elif sort == 'newest':
        products = products.order_by('-created_at')  # Assuming you have a created_at field

    show_discounted = request.GET.get('discounted')
    if show_discounted:
        products = products.filter(popust=True)

    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categories': Products2.objects.values_list('category', flat=True).distinct(),
        'selected_categories': selected_categories,
        'selected_max_price': max_price,
        'selected_stores': selected_stores,
        'selected_sort': sort,
        'search_query': search_query,
    }
    return render(request, 'main/product_list.html', context)


def product_catalog(request):
    products = Products2.objects.all()

    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query)
        )

    context = {
        'products': products,
    }
    return render(request, 'main/product_list.html', context)


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')  # Redirect to your homepage
    else:
        form = RegisterForm()
    return render(request, 'main/register.html', {'form': form})


def custom_logout(request):
    logout(request)

    # Replicate the home view logic for stores_with_products
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
        if products.exists():  # Only add if there are products
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
    return render(request, 'main/base.html', context)


@login_required
def view_lists(request):
    user_lists = ShoppingList.objects.filter(user=request.user)
    return render(request, 'main/lists.html', {'user_lists': user_lists})


@login_required
def create_list(request):
    if request.method == 'POST':
        list_name = request.POST.get('list_name')
        if list_name:
            ShoppingList.objects.create(user=request.user, name=list_name)
            return redirect('view_lists')
    return redirect('view_lists')



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
        # Extract data from POST request
        data = json.loads(request.body)
        product_id = data.get('product_id')
        list_id = data.get('list_id')

        # Debugging: Log received values
        print(f"Product ID: {product_id}, List ID: {list_id}, User: {request.user}")

        # Validate inputs
        if not product_id or not list_id:
            return JsonResponse({'success': False, 'message': 'Missing product or list ID'}, status=400)

        # Fetch shopping list and product
        shopping_list = get_object_or_404(ShoppingList, id=list_id, user=request.user)
        product = get_object_or_404(Products2, id=product_id)

        # Debugging: Confirm the product and list are found
        print(f"Shopping List: {shopping_list}, Product: {product}")

        # Get or create the list item
        item, created = ShoppingListItem.objects.get_or_create(
            shopping_list=shopping_list,
            product=product,
            defaults={'quantity': 1}
        )

        # Check if item is created or updated
        if not created:
            item.quantity += 1
            item.save()

        # Debugging: Confirm the item was saved
        print(f"Item: {item}, Created: {created}")

        return JsonResponse({'success': True, 'message': 'Product added to list'})

    except Exception as e:
        print(f"Error: {e}")  # Log error details
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

    if store and query:
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
            else:
                cursor.execute("""
                    SELECT DISTINCT name FROM product_history2 
                    WHERE store LIKE %s
                """, ['%' + store + '%'])
                all_store_products = [row[0] for row in cursor.fetchall()]

                similar_products = []

                string_matches = get_close_matches(
                    query,
                    all_store_products,
                    n=10,
                    cutoff=0.3
                )

                query_lower = query.lower()
                contains_matches = [
                                       p for p in all_store_products
                                       if query_lower in p.lower()
                                   ][:10]

                all_matches = list(set(string_matches + contains_matches))

                if len(all_matches) < 5:
                    all_matches.extend([
                                           p for p in all_store_products
                                           if p not in all_matches
                                       ][:10 - len(all_matches)])

                similar_products = [(p, 1.0) for p in all_matches[:10]]

        if selected_product:
            matched_name = selected_product

        if matched_name:
            base_sql = """
                SELECT scraped_date, price 
                FROM product_history2 
                WHERE name = %s AND store LIKE %s
            """
            params = [matched_name, '%' + store + '%']

            # Add date range conditions if provided
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

    return render(request, 'main/stats.html', {
        'chart_data': chart_data,
        'matched_name': matched_name,
        'query': query,
        'store': store,
        'similar_products': similar_products,
        'exact_match': exact_match,
        'start_date': start_date,
        'end_date': end_date,
    })

def get_driving_distance(user_lat, user_lon, store_lat, store_lon, api_key):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": f"{user_lat},{user_lon}",
        "destinations": f"{store_lat},{store_lon}",
        "key": api_key,
        "units": "metric"
    }
    response = requests.get(url, params=params)
    data = response.json()

    if data['status'] == 'OK':
        element = data['rows'][0]['elements'][0]
        if element['status'] == 'OK':
            distance_km = element['distance']['value'] / 1000
            duration = element['duration']['text']
            return distance_km, duration
    return None, None

from django.conf import settings

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
        {"name": "Reptil Market Ruzveltova", "lat": 41.9980, "lon": 21.4250, "chain": "reptil"},
        {"name": "Reptil Market Crniche", "lat": 41.9840, "lon": 21.4400, "chain": "reptil"},
        {"name": "Reptil Market Kisela Voda", "lat": 41.9510, "lon": 21.4460, "chain": "reptil"},
        {"name": "Reptil Market Aerodrom", "lat": 41.9780, "lon": 21.4680, "chain": "reptil"},
        {"name": "Reptil Market Karposh", "lat": 41.9980, "lon": 21.3930, "chain": "reptil"},
        {"name": "Reptil Market Partizanska", "lat": 41.9980, "lon": 21.4090, "chain": "reptil"},
        {"name": "Reptil Market Porta Vlae", "lat": 41.9990, "lon": 21.3860, "chain": "reptil"},
        {"name": "Reptil Market Radishani", "lat": 42.0500, "lon": 21.4500, "chain": "reptil"},
        {"name": "Reptil Market Karposh 3", "lat": 41.9990, "lon": 21.4080, "chain": "reptil"},
        {"name": "Reptil Market Butel", "lat": 42.0400, "lon": 21.4500, "chain": "reptil"},
        {"name": "Reptil Market Center (50ta Divizija)", "lat": 41.9980, "lon": 21.4320, "chain": "reptil"},
        {"name": "Reptil Market Nerezi", "lat": 41.9960, "lon": 21.3900, "chain": "reptil"},
        {"name": "Reptil Market Madzari", "lat": 41.9900, "lon": 21.4700, "chain": "reptil"},
        {"name": "Reptil Market Lisiche", "lat": 41.9752, "lon": 21.4728, "chain": "reptil"},
        {"name": "Reptil Market Green Market", "lat": 41.9950, "lon": 21.4360, "chain": "reptil"},
        {"name": "Reptil Market Center (Aminta III)", "lat": 41.9980, "lon": 21.4300, "chain": "reptil"},
        {"name": "Reptil Market Kozle", "lat": 41.9960, "lon": 21.3900, "chain": "reptil"},
        {"name": "Reptil Market Vlae", "lat": 41.9990, "lon": 21.3860, "chain": "reptil"},
        {"name": "Reptil Market Avtokomanda", "lat": 42.0000, "lon": 21.4700, "chain": "reptil"},
        {"name": "Reptil Market Bardovci", "lat": 42.0200, "lon": 21.3900, "chain": "reptil"},
        {"name": "Reptil Market Novo Lisiche", "lat": 41.9801, "lon": 21.4752, "chain": "reptil"},
        {"name": "Reptil Market Taftalidze", "lat": 41.9972, "lon": 21.4085, "chain": "reptil"},
        {"name": "Ramstore Vardar", "lat": 41.9981, "lon": 21.4325, "chain": "ramstore"},
        {"name": "Ramstore City Mall", "lat": 42.0045, "lon": 21.3919, "chain": "ramstore"},
        {"name": "Ramstore Taftalidze", "lat": 42.0030, "lon": 21.3925, "chain": "ramstore"},
        {"name": "Ramstore Karposh", "lat": 42.0040, "lon": 21.3940, "chain": "ramstore"},
        {"name": "Ramstore Cevahir", "lat": 41.9880, "lon": 21.4700, "chain": "ramstore"},
        {"name": "Ramstore Park", "lat": 41.9975, "lon": 21.4260, "chain": "ramstore"},
        {"name": "Ramstore Gorno Lisiche", "lat": 41.9600, "lon": 21.4700, "chain": "ramstore"},
        {"name": "Ramstore Kapitol", "lat": 41.9830, "lon": 21.4690, "chain": "ramstore"},
        {"name": "Ramstore Kapishtec", "lat": 41.9900, "lon": 21.4300, "chain": "ramstore"},
        {"name": "Ramstore Debar Maalo", "lat": 41.9970, "lon": 21.4300, "chain": "ramstore"},
        {"name": "Ramstore Vodno", "lat": 41.9900, "lon": 21.4300, "chain": "ramstore"},
        {"name": "Ramstore Aerodrom", "lat": 41.9800, "lon": 21.4700, "chain": "ramstore"},
        {"name": "Ramstore Star Aerodrom", "lat": 41.9800, "lon": 21.4700, "chain": "ramstore"},
        {"name": "Ramstore Michurin", "lat": 41.9800, "lon": 21.4700, "chain": "ramstore"},
        {"name": "Ramstore Sever", "lat": 42.0100, "lon": 21.4400, "chain": "ramstore"},
        {"name": "Ramstore Cair", "lat": 42.0100, "lon": 21.4400, "chain": "ramstore"},
        {"name": "Vero Aerodrom", "lat": 41.9980, "lon": 21.4680, "chain": "vero"},
        {"name": "Vero Taftalidze", "lat": 41.9972, "lon": 21.4085, "chain": "vero"},
        {"name": "Vero GTC", "lat": 41.9981, "lon": 21.4325, "chain": "vero"},
        {"name": "Vero Čair", "lat": 42.0000, "lon": 21.4330, "chain": "vero"},
        {"name": "Vero Vero Centar", "lat": 41.9980, "lon": 21.4250, "chain": "vero"},
        {"name": "Vero Kisela Voda", "lat": 41.9510, "lon": 21.4460, "chain": "vero"},
        {"name": "Vero Karposh", "lat": 41.9980, "lon": 21.3930, "chain": "vero"},
        {"name": "Vero Diamond Mall", "lat": 41.9985, "lon": 21.4230, "chain": "vero"},
    ]

    filtered_stores = [s for s in stores if s["chain"] == store_chain]

    print("Filtered stores:", filtered_stores)

    results = []
    for store in filtered_stores:
        distance_km, duration = get_driving_distance(user_lat, user_lon, store["lat"], store["lon"], settings.GOOGLE_MAPS_API_KEY)
        if distance_km is not None:
            gas_used = (distance_km * 2 * fuel_consumption) / 100
            results.append({
                "store": store["name"],
                "distance_km": distance_km,
                "duration": duration,
                "gas_used": round(gas_used, 2),
                "lat": store["lat"],
                "lon": store["lon"],
            })

    nearest_stores = sorted(results, key=lambda x: x['distance_km'])
    nearest_stores_top5 = nearest_stores[:5]

    least_gas_stores = sorted(results, key=lambda x: x['gas_used'])
    least_gas_stores_top5 = least_gas_stores[:5]

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

