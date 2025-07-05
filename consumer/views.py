from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from SwasthCare_seller.models import SearchHistory
import json

# MongoDB import - conditional based on availability
try:
    import pymongo
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("Warning: pymongo not available. MongoDB features will be disabled.")

# Create your views here.

@login_required
def home(request):
    """
    Redirect consumer app home to main consumer dashboard
    """
    return redirect('home')  # Redirect to main app home which will show consumer_home.html

@login_required
def scan_barcode(request):
    """
    Render the barcode scanning page
    """
    return render(request, 'consumer/scan.html')

@login_required
def product_detail(request, barcode=None):
    """
    Display product details for a specific barcode
    """
    if request.method == 'GET' and barcode:
        if not MONGODB_AVAILABLE:
            # If MongoDB is not available, show error page
            return render(request, 'consumer/product_not_found.html', {
                'barcode': barcode,
                'error': 'Database connection not available'
            })
        
        try:
            # Connect to MongoDB
            client = pymongo.MongoClient(settings.COSMOSDB_URI)
            db = client['swasth']
            collection = db['food']
            
            # Find product by barcode
            product = collection.find_one({'barcode': barcode})
            
            if product:
                # Convert MongoDB ObjectID to string for JSON serialization
                if '_id' in product:
                    product['_id'] = str(product['_id'])
                
                # Log search history for consumer users
                if request.user.userprofile.is_consumer:
                    SearchHistory.log_search(
                        user=request.user,
                        product_id=product['_id'],
                        product_name=product.get('prod_name', ''),
                        barcode=barcode,
                        search_query=f"Barcode scan: {barcode}"
                    )
                
                # Render the product detail page with the product data
                return render(request, 'consumer/product_detail.html', {'product': product})
            else:
                # Product not found
                return render(request, 'consumer/product_not_found.html', {'barcode': barcode})
                
        except Exception as e:
            # Handle database connection errors
            return render(request, 'consumer/product_not_found.html', {
                'barcode': barcode,
                'error': f'Database error: {str(e)}'
            })
    
    # If no barcode specified, redirect to scan page
    return render(request, 'consumer/scan.html')

@login_required
def get_product_json(request):
    """
    API endpoint to get product data by barcode
    """
    barcode = request.GET.get('barcode')
    
    if not barcode:
        return JsonResponse({'error': 'No barcode provided'}, status=400)
    
    if not MONGODB_AVAILABLE:
        return JsonResponse({'error': 'Database connection not available'}, status=500)
    
    try:
        # Connect to MongoDB
        client = pymongo.MongoClient(settings.COSMOSDB_URI)
        db = client['swasth']
        collection = db['food']
        
        # Find product by barcode
        product = collection.find_one({'barcode': barcode})
        
        if product:
            # Convert MongoDB ObjectID to string for JSON serialization
            if '_id' in product:
                product['_id'] = str(product['_id'])
            
            # Log search history for consumer users
            if request.user.userprofile.is_consumer:
                SearchHistory.log_search(
                    user=request.user,
                    product_id=product['_id'],
                    product_name=product.get('prod_name', ''),
                    barcode=barcode,
                    search_query=f"API search: {barcode}"
                )
            
            return JsonResponse({'product': product})
        else:
            return JsonResponse({'error': 'Product not found'}, status=404)
            
    except Exception as e:
        return JsonResponse({'error': f'Database error: {str(e)}'}, status=500)

@login_required
def search_products(request):
    """
    Search products by name or ingredients
    """
    query = request.GET.get('q', '').strip()
    
    if not query:
        return render(request, 'consumer/search_results.html', {'products': [], 'query': ''})
    
    if not MONGODB_AVAILABLE:
        return render(request, 'consumer/search_results.html', {
            'products': [], 
            'query': query, 
            'error': 'Database connection not available'
        })
    
    try:
        # Connect to MongoDB
        client = pymongo.MongoClient(settings.COSMOSDB_URI)
        db = client['swasth']
        collection = db['food']
        
        # Search products by name or ingredients (case-insensitive)
        search_filter = {
            '$or': [
                {'prod_name': {'$regex': query, '$options': 'i'}},
                {'Ingredients': {'$regex': query, '$options': 'i'}},
                {'prod_type': {'$regex': query, '$options': 'i'}}
            ]
        }
        
        products = list(collection.find(search_filter).limit(20))
        
        # Convert MongoDB ObjectIDs to strings
        for product in products:
            if '_id' in product:
                product['_id'] = str(product['_id'])
        
        return render(request, 'consumer/search_results.html', {
            'products': products, 
            'query': query
        })
            
    except Exception as e:
        return render(request, 'consumer/search_results.html', {
            'products': [], 
            'query': query, 
            'error': f'Database error: {str(e)}'
        })

@login_required
def product_detail_by_id(request, product_id):
    """
    Display product details for a specific product ID
    """
    if not MONGODB_AVAILABLE:
        return render(request, 'consumer/product_not_found.html', {
            'error': 'Database connection not available'
        })
    
    try:
        from bson import ObjectId
        
        # Connect to MongoDB
        client = pymongo.MongoClient(settings.COSMOSDB_URI)
        db = client['swasth']
        collection = db['food']
        
        # Find product by ObjectId
        product = collection.find_one({'_id': ObjectId(product_id)})
        
        if product:
            # Convert MongoDB ObjectID to string for JSON serialization
            product['_id'] = str(product['_id'])
            
            # Log search history for consumer users
            if request.user.userprofile.is_consumer:
                SearchHistory.log_search(
                    user=request.user,
                    product_id=product['_id'],
                    product_name=product.get('prod_name', ''),
                    barcode=product.get('barcode', ''),
                    search_query=f"Product view: {product.get('prod_name', product_id)}"
                )
            
            return render(request, 'consumer/product_detail.html', {'product': product})
        else:
            return render(request, 'consumer/product_not_found.html', {'product_id': product_id})
            
    except Exception as e:
        return render(request, 'consumer/product_not_found.html', {
            'product_id': product_id,
            'error': f'Database error: {str(e)}'
        })
