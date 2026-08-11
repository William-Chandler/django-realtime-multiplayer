from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile


def signup_view(request):
    # If user is already logged in, show a message instead of the signup form
    if request.user.is_authenticated:
        return render(request, "accounts/already_logged_in.html")
    
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")

        if password != password2:
            messages.error(request, "Passwords do not match")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect("signup")

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return redirect("index")  # change to your homepage

    return render(request, "accounts/signup.html")
    
def login_view(request):
    # If user is already logged in, show a message instead of the login form
    if request.user.is_authenticated:
        return render(request, "accounts/already_logged_in.html")
    
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("index")
        else:
            messages.error(request, "Invalid credentials")
            return redirect("login")

    return render(request, "accounts/login.html")
    
def logout_view(request):
    logout(request)
    return redirect("index")
    
@login_required
def preferences_view(request):
    profile = request.user.userprofile

    if request.method == "POST":
        profile.colour_preference = request.POST.get("colour_preference")
        profile.save()

        next_url = request.POST.get("next")
        if not next_url:
            next_url = "/"  # fallback

        return redirect(next_url)

    return render(request, "accounts/preferences.html", {
        "profile": profile,
        "colour_choices": UserProfile.COLOUR_CHOICES,
    })
