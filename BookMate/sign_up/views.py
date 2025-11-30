from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegisterForm
from django.urls import reverse
from django.db import IntegrityError


def register_view(request):
    """Handle user registration"""
    # Redirect authenticated users to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.set_password(form.cleaned_data["password1"])
                user.save()
                messages.success(request, "Registration successful! Please sign in to continue.")
                return redirect(f"{reverse('landing')}?modal=login")
            except IntegrityError:
                # Username or email already exists
                request.session['register_errors'] = {
                    'general': ['Invalid credentials. Please check your information and try again.']
                }
                return redirect(f"{reverse('landing')}?modal=register")
            
        else:
            # Generic error message for security and formality
            request.session['register_errors'] = {'general': ['Invalid credentials. Please check your information and try again.']}
            return redirect(f"{reverse('landing')}?modal=register")
    else:
        # Redirect GET requests to landing page
        return redirect("landing")
