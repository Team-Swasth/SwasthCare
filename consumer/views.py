from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
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
    Render the consumer app home page
    """
    return render(request, 'consumer/home.html')

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
            
            return JsonResponse({'product': product})
        else:
            return JsonResponse({'error': 'Product not found'}, status=404)
            
    except Exception as e:
        return JsonResponse({'error': f'Database error: {str(e)}'}, status=500)
