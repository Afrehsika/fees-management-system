from django.shortcuts import render
from django.views import View
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


# Create your views here.



class LoginView(View):
    def get(self, request):
        return render(request, "authentication/login.html")
    
    def post(self, request):
        if request.method == "POST":
            username = request.POST.get("Username")
            password = request.POST.get("Password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("finance:student") 
            else:
                messages.error(request, "Either Username or Password is not correct")
                return render(request, "authentication/login.html")
        return redirect("login")  


def View_logout(request):
    logout(request)
    messages.success(request,"You Successfully Logout")
    return redirect("login") 