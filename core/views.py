from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm
# --- Auth views ---
def register_view(request) : 
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, 'Account created successfully! Welcome to Life Quest!')
            login(request, user)
            return redirect('dashboard')
        else:
            # แสดง error ถ้ากรมไม่ valid
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else : 
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password')
    else :
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})
# --- Game Logic views ---
@login_required(login_url='login')
def dashboard_view(request):
    return render(request, 'core/dashboard.html')

