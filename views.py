from django.shortcuts import render

def home(request):
    # Render role-specific home page based on profile attributes.
    if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
        if request.user.userprofile.is_seller:
            return render(request, "seller/seller_home.html")
        elif request.user.userprofile.is_consumer:
            return render(request, "consumer/consumer_home.html")
    # Fallback common home page.
    return render(request, "home.html")
