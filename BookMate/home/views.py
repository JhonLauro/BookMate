from django.shortcuts import render, redirect


def landing_view(request):
    """Landing page for unauthenticated users"""
    # Redirect authenticated users to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Get form errors from session if they exist
    register_errors = request.session.pop('register_errors', {})
    login_errors = request.session.pop('login_errors', {})
    login_username = request.session.pop('login_username', '')
    open_modal = request.GET.get('modal', '')
    
    return render(request, 'landing.html', {
        'register_errors': register_errors,
        'login_errors': login_errors,
        'login_username': login_username,
        'open_modal': open_modal,
    })
