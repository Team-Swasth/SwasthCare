from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse, HttpResponseForbidden, HttpResponse
import json
from datetime import datetime
from django.contrib import messages
import base64
import logging

# MongoDB import - conditional based on availability
try:
    import pymongo
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("Warning: pymongo not available. MongoDB features will be disabled.")

# AI Services imports
from .azure_services import chat_about_product
try:
    from .ai_services import (
        ai_service,
        analyze_product_healthiness,
        get_product_alternatives as get_ai_alternatives,
        generate_meal_suggestions,
        text_to_speech,
        speech_to_text
    )
    AI_SERVICES_AVAILABLE = True
except ImportError:
    AI_SERVICES_AVAILABLE = False
    print("Warning: Enhanced AI services not available. Using basic chatbot only.")

from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

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

# Create your views here.

@login_required
@consumer_required
def home(request):
    """
    Previously redirected to 'home'. Now render the consumer dashboard directly.
    """
    return render(request, "consumer/consumer_home.html")

@login_required
@consumer_required
def scan_barcode(request):
    """
    Render the barcode scanning page
    """
    return render(request, 'consumer/scan.html')

@login_required
@consumer_required
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
@consumer_required
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
@consumer_required
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
@consumer_required
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
@consumer_required
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
@consumer_required
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
@consumer_required
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

@login_required
@consumer_required
def analyze_healthiness(request):
    """
    Analyze the healthiness of a product using AI service.
    Expects POST with JSON body: {'barcode': '...', 'question': '...'}
    """
    if request.method != "POST":
        return JsonResponse({'error': 'POST request required'}, status=405)
    try:
        data = json.loads(request.body.decode("utf-8"))
        barcode = data.get("barcode")
        if not barcode:
            return JsonResponse({'error': 'barcode required'}, status=400)
        if not AI_SERVICES_AVAILABLE:
            return JsonResponse({'error': 'AI services not available'}, status=500)
        
        # Call the AI service for healthiness analysis
        result = analyze_product_healthiness(barcode)
        
        return JsonResponse({'result': result})
    except Exception as e:
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)

@login_required
@consumer_required
def product_alternatives(request):
    """
    Get product alternatives using AI service.
    Expects POST with JSON body: {'barcode': '...'}
    """
    if request.method != "POST":
        return JsonResponse({'error': 'POST request required'}, status=405)
    try:
        data = json.loads(request.body.decode("utf-8"))
        barcode = data.get("barcode")
        if not barcode:
            return JsonResponse({'error': 'barcode required'}, status=400)
        if not AI_SERVICES_AVAILABLE:
            return JsonResponse({'error': 'AI services not available'}, status=500)
        
        # Call the AI service for product alternatives
        alternatives = get_ai_alternatives(barcode)
        
        return JsonResponse({'alternatives': alternatives})
    except Exception as e:
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)

@login_required
@consumer_required
def meal_suggestions(request):
    """
    Generate meal suggestions using AI service.
    Expects POST with JSON body: {'ingredients': ['...', '...', ...]}
    """
    if request.method != "POST":
        return JsonResponse({'error': 'POST request required'}, status=405)
    try:
        data = json.loads(request.body.decode("utf-8"))
        ingredients = data.get("ingredients")
        if not ingredients or not isinstance(ingredients, list):
            return JsonResponse({'error': 'ingredients list required'}, status=400)
        if not AI_SERVICES_AVAILABLE:
            return JsonResponse({'error': 'AI services not available'}, status=500)
        
        # Call the AI service for meal suggestions
        suggestions = generate_meal_suggestions(ingredients) # type: ignore
        
        return JsonResponse({'suggestions': suggestions})
    except Exception as e:
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)

@login_required
@consumer_required
def text_to_speech_view(request):
    """
    Convert text to speech using AI service.
    Expects POST with JSON body: {'text': '...'}
    """
    if request.method != "POST":
        return JsonResponse({'error': 'POST request required'}, status=405)
    try:
        data = json.loads(request.body.decode("utf-8"))
        text = data.get("text")
        if not text:
            return JsonResponse({'error': 'text required'}, status=400)
        if not AI_SERVICES_AVAILABLE:
            return JsonResponse({'error': 'AI services not available'}, status=500)
        
        # Call the AI service for text to speech
        audio_content = text_to_speech(text)
        
        # Encode audio content to base64 for JSON response
        audio_base64 = base64.b64encode(audio_content).decode('utf-8')
        
        return JsonResponse({'audio': audio_base64})
    except Exception as e:
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)

@login_required
@consumer_required
def speech_to_text_view(request):
    """
    Convert speech to text using AI service.
    Expects POST with audio file
    """
    if request.method != "POST":
        return JsonResponse({'error': 'POST request required'}, status=405)
    try:
        audio_file = request.FILES.get("file")
        if not audio_file:
            return JsonResponse({'error': 'audio file required'}, status=400)
        if not AI_SERVICES_AVAILABLE:
            return JsonResponse({'error': 'AI services not available'}, status=500)
        
        # Call the AI service for speech to text
        text = speech_to_text(audio_file)
        
        return JsonResponse({'text': text})
    except Exception as e:
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)

@login_required
@consumer_required
@csrf_exempt
def enhanced_product_chatbot(request):
    """
    Enhanced product chatbot with speech capabilities and personalized responses
    """
    if request.method != "POST":
        return JsonResponse({'error': 'POST request required'}, status=405)
    
    try:
        data = json.loads(request.body.decode("utf-8"))
        barcode = data.get("barcode")
        question = data.get("question")
        include_speech = data.get("include_speech", False)
        
        if not barcode or not question:
            return JsonResponse({'error': 'barcode and question required'}, status=400)
        
        if not MONGODB_AVAILABLE:
            return JsonResponse({'error': 'Database connection not available'}, status=500)
        
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
        user_profile = None
        if hasattr(request.user, 'userprofile'):
            user_profile = {
                'dietary_preferences': getattr(request.user.userprofile, 'dietary_preferences', []),
                'health_goals': getattr(request.user.userprofile, 'health_goals', []),
                'allergies': getattr(request.user.userprofile, 'allergies', []),
                'age_group': getattr(request.user.userprofile, 'age_group', 'adult')
            }
        
        # Streaming support
        if request.GET.get("stream") == "1":
            def stream_response():
                if AI_SERVICES_AVAILABLE:
                    for token in ai_service.chat_about_product(product, question, stream=True, user_profile=user_profile):
                        yield token
                else:
                    for token in chat_about_product(product, question, stream=True):
                        yield token
            return StreamingHttpResponse(stream_response(), content_type="text/plain")
        
        # Get response
        if AI_SERVICES_AVAILABLE:
            answer = ai_service.chat_about_product(product, question, stream=False, user_profile=user_profile)
        else:
            answer = chat_about_product(product, question)
        
        response_data = {'answer': answer}
        
        # Add speech synthesis if requested
        if include_speech and AI_SERVICES_AVAILABLE:
            try:
                audio_data = text_to_speech(answer)
                if audio_data:
                    # Convert to base64 for JSON response
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    response_data['audio'] = audio_base64
            except Exception as e:
                logger.error(f"Error generating speech: {str(e)}")
                response_data['speech_error'] = "Speech generation failed"
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error in enhanced_product_chatbot: {str(e)}")
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)

@login_required
@consumer_required
@csrf_exempt
def speech_to_text_api(request):
    """
    Convert speech to text using Azure Speech Services
    """
    if request.method != "POST":
        return JsonResponse({'error': 'POST request required'}, status=405)
    
    if not AI_SERVICES_AVAILABLE:
        return JsonResponse({'error': 'Speech services not available'}, status=500)
    
    try:
        # Get audio data from request
        audio_data = request.body
        
        if not audio_data:
            return JsonResponse({'error': 'No audio data provided'}, status=400)
        
        # Convert speech to text
        transcribed_text = speech_to_text(audio_data)
        
        return JsonResponse({'text': transcribed_text})
        
    except Exception as e:
        logger.error(f"Error in speech_to_text_api: {str(e)}")
        return JsonResponse({'error': f'Speech recognition failed: {str(e)}'}, status=500)

@login_required
@consumer_required
def product_health_analysis(request, barcode):
    """
    Analyze product healthiness and provide recommendations
    """
    if not MONGODB_AVAILABLE:
        return JsonResponse({'error': 'Database connection not available'}, status=500)
    
    if not AI_SERVICES_AVAILABLE:
        return JsonResponse({'error': 'AI services not available'}, status=500)
    
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
        user_profile = None
        if hasattr(request.user, 'userprofile'):
            user_profile = {
                'dietary_preferences': getattr(request.user.userprofile, 'dietary_preferences', []),
                'health_goals': getattr(request.user.userprofile, 'health_goals', []),
                'allergies': getattr(request.user.userprofile, 'allergies', []),
                'age_group': getattr(request.user.userprofile, 'age_group', 'adult')
            }
        
        # Analyze product healthiness
        analysis = analyze_product_healthiness(product, user_profile)
        
        return JsonResponse({
            'product_name': product.get('prod_name', 'Unknown'),
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Error in product_health_analysis: {str(e)}")
        return JsonResponse({'error': f'Analysis failed: {str(e)}'}, status=500)

@login_required
@consumer_required
def get_product_alternatives(request, barcode):
    """
    Get healthier alternatives for a product
    """
    if not MONGODB_AVAILABLE:
        return JsonResponse({'error': 'Database connection not available'}, status=500)
    
    if not AI_SERVICES_AVAILABLE:
        return JsonResponse({'error': 'AI services not available'}, status=500)
    
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
        user_profile = None
        if hasattr(request.user, 'userprofile'):
            user_profile = {
                'dietary_preferences': getattr(request.user.userprofile, 'dietary_preferences', []),
                'health_goals': getattr(request.user.userprofile, 'health_goals', []),
                'allergies': getattr(request.user.userprofile, 'allergies', []),
                'age_group': getattr(request.user.userprofile, 'age_group', 'adult')
            }
        
        # Get alternatives
        alternatives = get_ai_alternatives(product, user_profile)
        
        return JsonResponse({
            'product_name': product.get('prod_name', 'Unknown'),
            'alternatives': alternatives
        })
        
    except Exception as e:
        logger.error(f"Error in product_alternatives: {str(e)}")
        return JsonResponse({'error': f'Failed to get alternatives: {str(e)}'}, status=500)

@login_required
@consumer_required
def get_meal_suggestions(request, barcode):
    """
    Get meal suggestions using the product
    """
    if not MONGODB_AVAILABLE:
        return JsonResponse({'error': 'Database connection not available'}, status=500)
    
    if not AI_SERVICES_AVAILABLE:
        return JsonResponse({'error': 'AI services not available'}, status=500)
    
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
        
        # Get meal type from query parameters
        meal_type = request.GET.get('meal_type', 'any')
        
        # Get meal suggestions
        suggestions = generate_meal_suggestions(product, meal_type)
        
        return JsonResponse({
            'product_name': product.get('prod_name', 'Unknown'),
            'meal_type': meal_type,
            'suggestions': suggestions
        })
        
    except Exception as e:
        logger.error(f"Error in meal_suggestions: {str(e)}")
        return JsonResponse({'error': f'Failed to get meal suggestions: {str(e)}'}, status=500)

@login_required
@consumer_required
def ai_nutrition_dashboard(request):
    """
    AI-powered nutrition dashboard showing personalized insights
    """
    if not MONGODB_AVAILABLE:
        return render(request, 'consumer/ai_nutrition_dashboard.html', {
            'error': 'Database connection not available'
        })
    
    try:
        # Get user's recent scans
        client = pymongo.MongoClient(settings.COSMOSDB_URI)
        db = client['swasth']
        
        # Get recent history
        recent_scans = list(db['history'].find({
            'username': request.user.username
        }).sort('scanned_at', -1).limit(10))
        
        # Get unique products from recent scans
        product_insights = []
        processed_barcodes = set()
        
        for scan in recent_scans:
            barcode = scan.get('barcode')
            if barcode and barcode not in processed_barcodes:
                product = db['food'].find_one({'barcode': barcode})
                if product:
                    product['_id'] = str(product['_id'])
                    
                    # Get health analysis if AI services available
                    if AI_SERVICES_AVAILABLE:
                        try:
                            analysis = analyze_product_healthiness(product)
                            product['health_analysis'] = analysis
                        except Exception as e:
                            logger.error(f"Error analyzing product {barcode}: {str(e)}")
                            product['health_analysis'] = None
                    
                    product_insights.append(product)
                    processed_barcodes.add(barcode)
        
        context = {
            'recent_products': product_insights,
            'ai_available': AI_SERVICES_AVAILABLE,
            'total_scans': len(recent_scans),
            'unique_products': len(product_insights)
        }
        
        return render(request, 'consumer/ai_nutrition_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in ai_nutrition_dashboard: {str(e)}")
        return render(request, 'consumer/ai_nutrition_dashboard.html', {
            'error': f'Dashboard error: {str(e)}'
        })
