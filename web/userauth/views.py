from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse

def login_view(request: HttpRequest):
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect('/kb/')
        return render(request, 'userauth/login.html')

    username = request.POST["username"]
    password = request.POST["password"]

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return redirect('/kb/')

    return render(request, 'userauth/login.html', {"error": "Invalid login credentials"})

def logout_view(request: HttpRequest):
    logout(request)
    return redirect(reverse('userauth:login'))

# def set_cookie_view(request: HttpRequest) -> HttpResponse:
#     response = HttpResponse("Cookie set")
#     response.set_cookie("test", "1", max_age=3600)
#     return response

# def get_cookie_view(request: HttpRequest) -> HttpResponse:
#     value = request.COOKIES.get("test", "default")
#     return HttpResponse(f"Cookie value: {value}")
