from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm

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
            user = form.save()
            username = form.cleaned_data.get('username')
            user_type = form.cleaned_data.get('user_type')
            messages.success(request, f'Account created for {username} as {user_type}!')
            
            # Automatically log in the user after registration
            login(request, user)
            
            # Redirect based on user type
            if user_type == 'seller':
                return redirect('home')  # This will redirect to seller dashboard
            else:
                return redirect('home')  # This will redirect to consumer dashboard
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
