from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import LoginForm
from django.urls import reverse


def login_view(request):
    """Handle user login"""
    # Redirect authenticated users to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Validate credentials
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("dashboard")
        else:
            # Generic error message for security
            request.session['login_errors'] = {'general': ['Invalid credentials. Please try again.']}
            # Save username to repopulate the form
            request.session['login_username'] = username
            return redirect(f"{reverse('landing')}?modal=login")
    else:
        # Redirect GET requests to landing page
        return redirect("landing")


def logout_view(request):
    """Handle user logout"""
    logout(request)
    # Removed notification - landing page already shows logout message
    return redirect("landing")
