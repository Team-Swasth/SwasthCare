from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
import json
from datetime import datetime
from django.contrib import messages

# MongoDB import - conditional based on availability
try:
    import pymongo
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("Warning: pymongo not available. MongoDB features will be disabled.")

from .azure_services import chat_about_product
from django.views.decorators.csrf import csrf_exempt

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
                
                # Log search history in MongoDB 'history' collection
                if request.user.userprofile.is_consumer:
                    db['history'].insert_one({
                        'barcode': barcode,
                        'item_name': product.get('prod_name', ''),
                        'username': request.user.username,
                        'scanned_at': datetime.utcnow()
                    })
                
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
            
            # Log search history in MongoDB 'history' collection
            if request.user.userprofile.is_consumer:
                db['history'].insert_one({
                    'barcode': barcode,
                    'item_name': product.get('prod_name', ''),
                    'username': request.user.username,
                    'scanned_at': datetime.utcnow()
                })
            
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
            
            # Log search history in MongoDB 'history' collection
            if request.user.userprofile.is_consumer:
                db['history'].insert_one({
                    'barcode': product.get('barcode', ''),
                    'item_name': product.get('prod_name', ''),
                    'username': request.user.username,
                    'scanned_at': datetime.utcnow()
                })
            
            return render(request, 'consumer/product_detail.html', {'product': product})
        else:
            return render(request, 'consumer/product_not_found.html', {'product_id': product_id})
            
    except Exception as e:
        return render(request, 'consumer/product_not_found.html', {
            'product_id': product_id,
            'error': f'Database error: {str(e)}'
        })

@login_required
def search_history(request):
    """
    Display the search history for the logged-in user.
    """
    if not MONGODB_AVAILABLE:
        return render(request, 'consumer/history.html', {'history': [], 'error': 'Database connection not available'})
    try:
        client = pymongo.MongoClient(settings.COSMOSDB_URI)
        db = client['swasth']
        history_cursor = db['history'].find({'username': request.user.username}).sort('scanned_at', -1).limit(100)
        history = []
        for entry in history_cursor:
            entry['_id'] = str(entry.get('_id', ''))
            entry['scanned_at'] = entry.get('scanned_at')
            history.append(entry)
        return render(request, 'consumer/history.html', {'history': history})
    except Exception as e:
        return render(request, 'consumer/history.html', {'history': [], 'error': f'Database error: {str(e)}'})

@login_required
@csrf_exempt
def product_chatbot(request):
    """
    API endpoint for product chatbot: takes barcode and user question, returns answer from Phi-4.
    """
    if request.method != "POST":
        return JsonResponse({'error': 'POST request required'}, status=405)
    try:
        data = json.loads(request.body.decode("utf-8"))
        barcode = data.get("barcode")
        question = data.get("question")
        if not barcode or not question:
            return JsonResponse({'error': 'barcode and question required'}, status=400)
        if not MONGODB_AVAILABLE:
            return JsonResponse({'error': 'Database connection not available'}, status=500)
        client = pymongo.MongoClient(settings.COSMOSDB_URI)
        db = client['swasth']
        collection = db['food']
        product = collection.find_one({'barcode': barcode})
        if not product:
            return JsonResponse({'error': 'Product not found'}, status=404)
        # Convert ObjectId to string
        if '_id' in product:
            product['_id'] = str(product['_id'])
        # Streaming support
        if request.GET.get("stream") == "1":
            def stream_response():
                for token in chat_about_product(product, question, stream=True):
                    yield token
            return StreamingHttpResponse(stream_response(), content_type="text/plain")
        # Call Phi-4 chatbot (non-streaming)
        answer = chat_about_product(product, question)
        return JsonResponse({'answer': answer})
    except Exception as e:
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)

@login_required
def compare_products(request):
    """
    Compare selected products side by side.
    Expects GET param 'barcode' 2–4 times.
    """
    barcodes = request.GET.getlist('barcode')
    if len(barcodes) < 2 or len(barcodes) > 4:
        messages.error(request, 'Select between 2 and 4 products to compare.')
        return redirect('search_history')
    if not MONGODB_AVAILABLE:
        return render(request, 'consumer/compare.html', {
            'products': [], 
            'error': 'Database connection not available'
        })
    try:
        client = pymongo.MongoClient(settings.COSMOSDB_URI)
        db = client['swasth']
        collection = db['food']
        products = []
        for bc in barcodes:
            prod = collection.find_one({'barcode': bc})
            if prod:
                prod['_id'] = str(prod.get('_id'))
                products.append(prod)
        return render(request, 'consumer/compare.html', {'products': products})
    except Exception as e:
        return render(request, 'consumer/compare.html', {
            'products': [], 
            'error': f'Database error: {str(e)}'
        })
