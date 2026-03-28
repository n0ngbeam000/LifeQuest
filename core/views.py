from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.db.models import Sum
from django.db.models.functions import TruncDate
from allauth.account.models import EmailAddress
from .forms import RegisterForm, LoginForm
from .models import Task, UserProfile

User = get_user_model()


def social_login_cancelled(request):
    """Redirect allauth's 'Login Cancelled' page back to our login page."""
    return redirect('login')


# --- Leaderboard view ---
@login_required(login_url='login')
def leaderboard_view(request):
    top_players = UserProfile.objects.select_related('user').order_by(
        '-level', '-exp'
    )[:10]

    ranked = []
    for rank, profile in enumerate(top_players, start=1):
        ranked.append({
            'rank': rank,
            'username': profile.user.username,
            'level': profile.level,
            'exp': profile.exp,
            'next_level_exp': profile.get_next_level_exp(),
        })

    return render(request, 'core/leaderboard.html', {
        'ranked_players': ranked,
        'top3': ranked[:3],
        'rest': ranked[3:],
    })


# --- Auth views ---
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            # Mark email as verified immediately — no verification email sent
            EmailAddress.objects.update_or_create(
                user=user,
                defaults={'email': user.email, 'primary': True, 'verified': True},
            )
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f'Welcome to LifeQuest, {user.username}!')
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})

# --- Password Reset views ---
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        try:
            user = User.objects.filter(email=email).first()
            if user is None:
                raise User.DoesNotExist
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_path = reverse('reset_password', kwargs={'uidb64': uid, 'token': token})
            reset_url = request.build_absolute_uri(reset_path)
            email_body = render_to_string('emails/password_reset_email.txt', {
                'user': user,
                'reset_url': reset_url,
            })
            send_mail(
                subject='Reset your Life Quest password',
                message=email_body,
                from_email=None,  # uses DEFAULT_FROM_EMAIL from settings
                recipient_list=[user.email],
                fail_silently=False,
            )
        except User.DoesNotExist:
            pass  # Intentional: prevent email enumeration
        # Always show success to prevent email enumeration
        messages.success(
            request,
            'If that email is registered, you will receive a password reset link shortly.'
        )
        return redirect('forgot_password')
    return render(request, 'core/forgot_password.html')


def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        messages.error(request, 'This password reset link is invalid or has expired.')
        return redirect('forgot_password')

    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        else:
            user.set_password(password1)
            user.save()
            return redirect('reset_password_done')

    return render(request, 'core/reset_password.html', {
        'uidb64': uidb64,
        'token': token,
    })


def reset_password_done(request):
    return render(request, 'core/reset_password_done.html')


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
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})
# --- Game Logic views ---
@login_required(login_url='login')
def dashboard_view(request):
    user = request.user
    #
    active_tasks = Task.objects.filter(user=user, status='pending').order_by('created_at')
    complete_tasks = Task.objects.filter(user=user, status='completed').order_by('-created_at')[:3] # get the least of 3 task
    completed_count = Task.objects.filter(user=user ,status='completed').count()

    profile = user.profile
    next_level_exp = profile.get_next_level_exp()
    xp_percentage = (profile.exp / next_level_exp) * 100 ## i don't want it baby
    exp_remaining = next_level_exp - profile.exp

    context = {
        'active_tasks': active_tasks,
        'completed_tasks': complete_tasks,
        'completed_count': completed_count,
        'xp_percentage': xp_percentage,
        'next_level_exp': next_level_exp,
        'exp_remaining': exp_remaining,
    }
    return render(request, 'core/dashboard.html',context)
@login_required
@require_POST
def add_task(request):
    title = request.POST.get('title', '').strip()
    difficulty = request.POST.get('difficulty', '10')

    if not title:
        return JsonResponse({'status': 'error', 'message': 'Title is required.'}, status=400)

    # Validate difficulty is one of the allowed values
    allowed = {10, 30, 50, 100}
    try:
        difficulty = int(difficulty)
        if difficulty not in allowed:
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid difficulty.'}, status=400)

    task = Task.objects.create(
        user=request.user,
        title=title,
        difficulty=difficulty,
    )

    return JsonResponse({
        'status': 'success',
        'quest': {
            'id': task.id,
            'title': task.title,
            'difficulty': task.difficulty,
            'created_at': task.created_at.strftime('%b %d, %I:%M %p'),
        },
    })

@login_required
@require_POST
def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)

    if task.status != 'pending':
        return JsonResponse({'status': 'error', 'message': 'Task already completed.'}, status=400)

    task.status = 'completed'
    task.completed_at = timezone.now()
    task.save()

    profile = request.user.profile
    profile.exp += task.difficulty
    leveled_up = profile.check_level_up()
    profile.save()

    next_level_exp = profile.get_next_level_exp()
    exp_percentage = round((profile.exp / next_level_exp) * 100, 2)

    return JsonResponse({
        'status': 'success',
        'quest_id': task.id,
        'quest': {
            'id': task.id,
            'title': task.title,
            'difficulty': task.difficulty,
            'completed_at': task.completed_at.strftime('%b %d, %I:%M %p'),
        },
        'new_exp': profile.exp,
        'new_level': profile.level,
        'exp_percentage': exp_percentage,
        'next_level_exp': next_level_exp,
        'leveled_up': leveled_up,
        'xp_gained': task.difficulty,
    })

@login_required
@require_POST
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    return JsonResponse({'status': 'success', 'quest_id': task_id})

@login_required
@require_POST
def uncomplete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)

    if task.status != 'completed':
        return JsonResponse({'status': 'error', 'message': 'Task is not completed.'}, status=400)

    profile = request.user.profile
    profile.remove_exp(task.difficulty)

    task.status = 'pending'
    task.completed_at = None
    task.save()

    next_level_exp = profile.get_next_level_exp()
    exp_percentage = round((profile.exp / next_level_exp) * 100, 2)

    # After this undo the completed list shows at most 3 tasks.
    # Fetch the 3rd remaining completed task (index 2) so the frontend
    # can append it and keep the visible list full.
    next_completed = None
    replacement = Task.objects.filter(
        user=request.user, status='completed'
    ).order_by('-completed_at')[2:3].first()
    if replacement:
        next_completed = {
            'id': replacement.id,
            'title': replacement.title,
            'difficulty': replacement.difficulty,
            'completed_at': replacement.completed_at.strftime('%b %d, %I:%M %p'),
        }

    return JsonResponse({
        'status': 'success',
        'quest_id': task.id,
        'quest': {
            'id': task.id,
            'title': task.title,
            'difficulty': task.difficulty,
            'created_at': task.created_at.strftime('%b %d, %I:%M %p'),
        },
        'next_completed': next_completed,
        'new_exp': profile.exp,
        'new_level': profile.level,
        'exp_percentage': exp_percentage,
        'next_level_exp': next_level_exp,
        'xp_lost': task.difficulty,
    })


@login_required(login_url='login')
def completed_quests_view(request):
    completed_tasks = Task.objects.filter(
        user=request.user, status='completed'
    ).annotate(
        completion_date=TruncDate('completed_at')
    ).order_by('-completed_at')

    total_completed_quests = completed_tasks.count()
    total_earned_xp = completed_tasks.aggregate(Sum('difficulty'))['difficulty__sum'] or 0

    return render(request, 'core/completed_quests.html', {
        'completed_tasks': completed_tasks,
        'total_completed_quests': total_completed_quests,
        'total_earned_xp': total_earned_xp,
    })