"""
Simple and reliable AI views for SwasthCare
These work with your existing data and provide accurate insights
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import pymongo
from django.conf import settings
from .simple_ai_features import get_simple_product_insights
from .azure_services import chat_about_product


def consumer_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'userprofile') and request.user.userprofile.is_consumer:
            return view_func(request, *args, **kwargs)
        return render(request, 'access_denied.html', {
            'message': "Access denied: Consumer role required.",
            'redirect_buttons': [
                {'url': 'consumer_home', 'label': 'Go to Consumer Homepage'},
                {'url': 'seller_home', 'label': 'Go to Seller Homepage'}
            ]
        })
    return wrapper


@login_required
@consumer_required
def simple_product_analysis(request, barcode):
    """
    Get simple but reliable product analysis
    Uses actual product data for accurate insights
    """
    try:
        # Get product data
        client = pymongo.MongoClient(settings.COSMOSDB_URI)
        db = client['swasth']
        collection = db['food']
        product = collection.find_one({'barcode': barcode})
        
        if not product:
            return JsonResponse({'error': 'Product not found'}, status=404)
        
        # Convert ObjectId to string
        if '_id' in product:
            product['_id'] = str(product['_id'])
        
        # Get user profile (if available)
        user_profile = {}
        if hasattr(request.user, 'userprofile'):
            # You'll need to adjust these based on your actual UserProfile model
            user_profile = {
                'dietary_preferences': getattr(request.user.userprofile, 'dietary_preferences', []),
                'allergies': getattr(request.user.userprofile, 'allergies', []),
            }
        
        # Get comprehensive insights
        insights = get_simple_product_insights(product, user_profile)
        
        return JsonResponse({
            'success': True,
            'insights': insights
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Analysis failed: {str(e)}'}, status=500)


@login_required
@consumer_required
def enhanced_product_detail_view(request, barcode):
    """
    Enhanced product detail page with simple AI insights
    """
    try:
        # Get product data (your existing logic)
        client = pymongo.MongoClient(settings.COSMOSDB_URI)
        db = client['swasth']
        collection = db['food']
        product = collection.find_one({'barcode': barcode})
        
        if not product:
            return render(request, 'consumer/product_not_found.html', {'barcode': barcode})
        
        # Convert ObjectId to string
        if '_id' in product:
            product['_id'] = str(product['_id'])
        
        # Log search history (your existing logic)
        if request.user.userprofile.is_consumer:
            db['history'].insert_one({
                'barcode': barcode,
                'item_name': product.get('prod_name', ''),
                'username': request.user.username,
                'scanned_at': datetime.utcnow()
            })
        
        # Get user profile for AI insights
        user_profile = {}
        if hasattr(request.user, 'userprofile'):
            user_profile = {
                'dietary_preferences': getattr(request.user.userprofile, 'dietary_preferences', []),
                'allergies': getattr(request.user.userprofile, 'allergies', []),
            }
        
        # Get AI insights
        ai_insights = get_simple_product_insights(product, user_profile)
        
        context = {
            'product': product,
            'ai_insights': ai_insights,
            'has_ai_insights': True
        }
        
        return render(request, 'consumer/enhanced_product_detail.html', context)
        
    except Exception as e:
        return render(request, 'consumer/product_not_found.html', {
            'barcode': barcode,
            'error': f'Error loading product: {str(e)}'
        })
