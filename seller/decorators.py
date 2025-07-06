from django.contrib.auth.decorators import user_passes_test

def seller_required(view_func):
    # Adjust the lambda check if your seller flag is named differently.
    return user_passes_test(
        lambda u: u.is_authenticated and getattr(u, 'is_seller', False),
        login_url='consumer_home'  # or another URL for unauthorized users
    )(view_func)
