from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileEditForm, CreateSellerForm
from .models import UserProfile
from .communication_services import communication_service
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.urls import reverse
from django.contrib.auth import update_session_auth_hash
from .forms import CustomPasswordChangeForm, ForgotPasswordForm, ResetPasswordForm
from .email_service import azure_communication_service
import secrets
import string
import datetime
from django.utils import timezone
from pymongo import MongoClient
from django.conf import settings

def home(request):
    if request.user.is_authenticated:
        try:
            if request.user.userprofile.is_seller:
                return render(request, 'seller_home.html')
            elif request.user.userprofile.is_consumer:
                return render(request, 'consumer_home.html')
        except:
            # If user profile doesn't exist, show general home
            pass
    return render(request, 'home.html')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                username = form.cleaned_data.get('username')
                messages.success(request, f'Account created for {username}!')
                login(request, user)
                return redirect('home')
            except Exception as e:
                messages.error(request, f"Registration failed: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()
    return render(request, 'auth/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                
                # Redirect to the intended page or default
                next_page = request.GET.get('next')
                if next_page:
                    return redirect(next_page)
                else:
                    return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'auth/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def profile_view(request):
    return render(request, 'auth/profile.html')

@login_required
def edit_profile_view(request):
    """Allow users to edit their profile information (non-sensitive fields only)"""
    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, user=request.user)
        if form.is_valid():
            form.save(request.user)
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileEditForm(user=request.user)
    
    return render(request, 'auth/edit_profile.html', {'form': form})

@login_required
def create_seller_view(request):
    """Allow existing sellers to create new seller accounts"""
    # Check if user is a seller
    if not request.user.userprofile.is_seller:
        messages.error(request, 'Only sellers can create new seller accounts.')
        return redirect('home')
    
    if request.method == 'POST':
        form = CreateSellerForm(request.POST)
        if form.is_valid():
            try:
                # Generate a secure password
                if communication_service:
                    password = communication_service.generate_password()
                else:
                    # Fallback password generation if service is not available
                    import secrets
                    import string
                    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
                    password = ''.join(secrets.choice(alphabet) for _ in range(12))
                
                # Create the new user
                new_user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=password,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name']
                )
                
                # Set user type as seller
                profile, created = UserProfile.objects.get_or_create(user=new_user)
                profile.user_type = 'seller'
                profile.save()
                
                # Send welcome email with credentials
                if communication_service:
                    success, message_info = communication_service.send_welcome_email(
                        recipient_email=new_user.email,
                        username=new_user.username,
                        password=password,
                        created_by=request.user.username
                    )
                    
                    if success:
                        messages.success(request, 
                            f'Seller account created successfully for {new_user.username}. '
                            f'Login credentials have been sent to {new_user.email}.')
                    else:
                        messages.warning(request, 
                            f'Seller account created successfully for {new_user.username}, '
                            f'but email could not be sent. Password: {password}')
                else:
                    messages.warning(request, 
                        f'Seller account created successfully for {new_user.username}. '
                        f'Email service unavailable. Password: {password}')
                
                return redirect('create_seller')
                
            except Exception as e:
                messages.error(request, f'Error creating seller account: {str(e)}')
    else:
        form = CreateSellerForm()
    
    return render(request, 'auth/create_seller.html', {'form': form})

@login_required
def search_history_view(request):
    """Display user's search history from MongoDB"""
    if not request.user.userprofile.is_consumer:
        messages.error(request, 'Only consumers can view search history.')
        return redirect('home')

    # Connect to MongoDB
    client = MongoClient(settings.MONGODB_URI)
    db = client.get_default_database()
    history_collection = db['history']

    # Query for documents with username == request.user.username
    search_history = list(
        history_collection.find({'username': request.user.username}).sort('scanned_at', -1)
    )

    return render(request, 'auth/search_history.html', {'search_history': search_history})

@login_required
def change_password_view(request):
    """View for changing user password"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in after password change
            messages.success(request, 'Your password has been successfully changed.')
            return redirect('profile')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'auth/change_password.html', {'form': form})

def forgot_password_view(request):
    """View for requesting password reset"""
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            if user:
                # Generate password reset token
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Create reset link
                reset_link = request.build_absolute_uri(
                    reverse('reset_password', kwargs={'uidb64': uid, 'token': token})
                )
                
                # Send email using Azure Communication Services
                success = azure_communication_service.send_password_reset_email(
                    user_email=user.email,
                    reset_link=reset_link,
                    user_name=user.get_full_name() or user.username
                )
                
                if success:
                    messages.success(
                        request, 
                        'Password reset instructions have been sent to your email address.'
                    )
                else:
                    messages.error(
                        request, 
                        'There was an error sending the password reset email. Please try again later.'
                    )
                    
                return redirect('login')
    else:
        form = ForgotPasswordForm()
    
    return render(request, 'auth/forgot_password.html', {'form': form})

def reset_password_view(request, uidb64, token):
    """View for resetting password with token"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = ResetPasswordForm(request.POST)
            if form.is_valid():
                form.save(user)
                messages.success(request, 'Your password has been successfully reset. You can now log in.')
                return redirect('login')
        else:
            form = ResetPasswordForm()
        
        return render(request, 'auth/reset_password.html', {'form': form, 'valid_link': True})
    else:
        messages.error(request, 'The password reset link is invalid or has expired.')
        return render(request, 'auth/reset_password.html', {'valid_link': False})

