from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from .models import Task, UserProfile
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
    user = request.user
    #
    active_tasks = Task.objects.filter(user=user, status='pending').order_by('create_at')
    complete_tasks = Task.objects.filter(user=user, status='completed').order_by('-create_at')[:5] # get the least of 5 task

    profile = user.profile
    next_level_exp = profile.get_next_level_exp()
    xp_percentage = (profile.exp / next_level_exp) * 100 ## i don't want it baby

    context = {
        'active_tasks': active_tasks,
        'complete_tasks': complete_tasks,
        'xp_percentage': xp_percentage,
        'next_level_exp': next_level_exp,
    }
    return render(request, 'core/dashboard.html',context)
@login_required
def add_task(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        difficulty = request.POST.get('difficulty')

        if title:
            Task.objects.create(
                user = request.user,
                title = title,
                difficulty = difficulty
            )
            messages.success(request, 'New Quest Added!')
    return redirect('dashboard')

@login_required
def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user = request.user)
    
    if task.status == 'pending':
        task.status = 'complete'
        task.save()

        profile = request.user.profile
        profile.exp += task.difficulty

        if profile.check_level_up():
            messages.success(request, f'LEVEL UP! You reached level {profile.level}!')
        else :
            messages.success(request, f'Quest Complete! +{task.difficulty} EXP')
        
        profile.save()
    return redirect('dashboard')

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    messages.info(request 'Quest deleted.')
    return redirect('dashboard')