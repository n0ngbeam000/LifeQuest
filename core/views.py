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
import random
from datetime import timedelta

User = get_user_model()


# ========== HELPER FUNCTIONS ==========

def reset_daily_limits(profile):
    """Reset daily counters if a new day has started."""
    today = timezone.now().date()
    if today > profile.last_daily_reset:
        profile.daily_xp_count = 0
        profile.daily_hp_healed = 0
        profile.last_daily_reset = today
        profile.save()


def check_game_over(profile):
    """
    Check if HP <= 0, trigger Game Over.
    Game Over resets: level = 1, xp = 0, hp = 100
    """
    if profile.hp <= 0:
        profile.level = 1
        profile.exp = 0
        profile.hp = 100
        profile.coins = 0  # Optional: reset coins too
        profile.daily_xp_count = 0
        profile.daily_hp_healed = 0
        profile.save()
        return True
    return False


def apply_overdue_damage(user):
    """
    Apply overdue damage for all overdue tasks.
    For each overdue task where due_date < today and last_damage_date != today:
    - Deduct 5 HP
    - Update last_damage_date to today
    """
    today = timezone.now().date()
    profile = user.profile
    
    overdue_tasks = Task.objects.filter(
        user=user,
        status='pending',
        due_date__lt=today
    ).exclude(last_damage_date=today)
    
    total_damage = 0
    for task in overdue_tasks:
        profile.hp -= 5
        task.last_damage_date = today
        task.save()
        total_damage += 5
    
    if total_damage > 0:
        profile.save()
        check_game_over(profile)
    
    return total_damage


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
    profile = user.profile
    
    # STEP 1: Reset daily limits if new day
    reset_daily_limits(profile)
    
    # STEP 2: Apply overdue damage for all overdue tasks
    damage_taken = apply_overdue_damage(user)
    if damage_taken > 0:
        messages.warning(request, f'⚠️ Overdue tasks dealt {damage_taken} HP damage!')
    
    # Fetch tasks
    active_tasks = Task.objects.filter(user=user, status='pending').order_by('due_date')
    complete_tasks = Task.objects.filter(user=user, status='completed').order_by('-completed_at')[:3]
    completed_count = Task.objects.filter(user=user, status='completed').count()

    next_level_exp = profile.get_next_level_exp()
    xp_percentage = (profile.exp / next_level_exp) * 100
    exp_remaining = next_level_exp - profile.exp
    
    # HP percentage for UI
    hp_percentage = (profile.hp / 100) * 100

    context = {
        'active_tasks': active_tasks,
        'completed_tasks': complete_tasks,
        'completed_count': completed_count,
        'xp_percentage': xp_percentage,
        'next_level_exp': next_level_exp,
        'exp_remaining': exp_remaining,
        'hp_percentage': hp_percentage,
    }
    return render(request, 'core/dashboard.html', context)
@login_required
@require_POST
def add_task(request):
    title = request.POST.get('title', '').strip()
    difficulty = request.POST.get('difficulty', '10')
    due_date_str = request.POST.get('due_date', '').strip()

    if not title:
        return JsonResponse({'status': 'error', 'message': 'Title is required.'}, status=400)
    
    if not due_date_str:
        return JsonResponse({'status': 'error', 'message': 'Due date is required.'}, status=400)

    # Validate difficulty is one of the allowed values
    allowed = {10, 30, 50, 100}
    try:
        difficulty = int(difficulty)
        if difficulty not in allowed:
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid difficulty.'}, status=400)
    
    # Parse due_date — accepts datetime-local format (YYYY-MM-DDTHH:MM)
    try:
        from datetime import datetime
        # Try datetime-local format first, fall back to date-only
        for fmt in ('%Y-%m-%dT%H:%M', '%Y-%m-%d'):
            try:
                due_date = datetime.strptime(due_date_str, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError('No valid format matched')
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid date/time format. Use YYYY-MM-DDTHH:MM.'}, status=400)

    # ✅ Strict server-side check: due_date must be in the future
    # Make due_date timezone-aware for comparison
    from django.utils.timezone import make_aware
    if timezone.is_naive(due_date):
        due_date_aware = make_aware(due_date)
    else:
        due_date_aware = due_date

    if due_date_aware < timezone.now():
        return JsonResponse({
            'status': 'error',
            'message': '⚠️ Deadline must be in the future. Please pick a later date and time.'
        }, status=400)

    task = Task.objects.create(
        user=request.user,
        title=title,
        difficulty=difficulty,
        due_date=due_date_aware,
    )

    return JsonResponse({
        'status': 'success',
        'quest': {
            'id': task.id,
            'title': task.title,
            'difficulty': task.difficulty,
            'due_date': task.due_date.strftime('%b %d, %I:%M %p'),
            'created_at': task.created_at.strftime('%b %d, %I:%M %p'),
        },
    })

@login_required
@require_POST
def complete_task(request, task_id):
    """
    STEP 2: Task Completion Logic with Coin Exploit Fix
    - Reset daily limits if new day
    - Check daily XP cap (678)
    - Award XP and random coin drop (10 coins with 50% chance)
    - Save coins_earned to task to prevent farming exploit
    - HP recovery (+2 HP per task, max +10/day, cap at 100)
    - Level up and instant heal to 100 HP
    """
    task = get_object_or_404(Task, id=task_id, user=request.user)

    if task.status != 'pending':
        return JsonResponse({'status': 'error', 'message': 'Task already completed.'}, status=400)

    profile = request.user.profile
    
    # Reset daily limits if new day
    reset_daily_limits(profile)
    
    # Task XP value
    task_xp = task.difficulty
    
    # Check daily XP cap (678)
    xp_gained = 0
    coins_gained = 0
    hp_gained = 0
    cap_reached = False
    
    if profile.daily_xp_count + task_xp <= 678:
        # Award XP
        xp_gained = task_xp
        profile.exp += xp_gained
        profile.daily_xp_count += xp_gained
        
        # True random coin drop: 30% chance to earn 10 coins
        if random.random() < 0.3:
            coins_gained = 10
            profile.coins += coins_gained
        
        # HP Recovery: +2 HP per task, but max +10 HP/day
        if profile.daily_hp_healed < 10:
            hp_to_heal = min(2, 10 - profile.daily_hp_healed)
            profile.hp = min(100, profile.hp + hp_to_heal)
            profile.daily_hp_healed += hp_to_heal
            hp_gained = hp_to_heal
    else:
        # Daily cap reached - no rewards
        cap_reached = True
    
    # Mark task as completed
    task.status = 'completed'
    task.completed_at = timezone.now()
    
    # 🔒 COIN EXPLOIT FIX: Save exact coins earned to prevent farming
    task.coins_earned = coins_gained
    task.save()
    
    # Level Up check
    leveled_up = False
    if xp_gained > 0:
        leveled_up = profile.check_level_up()
        if leveled_up:
            # Instant heal to 100 HP on level up
            profile.hp = 100
    
    profile.save()

    next_level_exp = profile.get_next_level_exp()
    exp_percentage = round((profile.exp / next_level_exp) * 100, 2)
    hp_percentage = round((profile.hp / 100) * 100, 2)
    
    # Build conditional toast message per spec:
    # - Coin drop  → "Quest Completed! + 10 coin"
    # - No coin    → "Quest Completed!"
    if cap_reached:
        message = "⚠️ Daily XP cap reached (678/678). Task completed but no rewards."
    elif task.coins_earned > 0:
        message = "Quest Completed! + 10 coin"
    else:
        message = "Quest Completed!"

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
        'new_hp': profile.hp,
        'new_coins': profile.coins,
        'exp_percentage': exp_percentage,
        'hp_percentage': hp_percentage,
        'next_level_exp': next_level_exp,
        'leveled_up': leveled_up,
        'xp_gained': xp_gained,
        'coins_gained': coins_gained,
        'hp_gained': hp_gained,
        'cap_reached': cap_reached,
        'daily_xp_count': profile.daily_xp_count,
        'message': message,
    })

@login_required
@require_POST
def delete_task(request, task_id):
    """
    STEP 3: Delete Task Penalty
    - If deleting an active (pending) task, deduct 10 HP
    - Check for game over after HP deduction
    """
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    profile = request.user.profile
    hp_lost = 0
    game_over = False
    
    # Penalty for deleting active quest
    if task.status == 'pending':
        profile.hp -= 10
        hp_lost = 10
        profile.save()
        
        # Check for game over
        game_over = check_game_over(profile)
    
    task.delete()
    
    hp_percentage = round((profile.hp / 100) * 100, 2)
    next_level_exp = profile.get_next_level_exp()
    exp_percentage = round((profile.exp / next_level_exp) * 100, 2)
    
    # Determine message based on whether it was an active or completed quest
    if hp_lost > 0:
        message = f'Quest Abandoned! -{hp_lost} HP'
    else:
        message = 'Completed quest removed.'

    return JsonResponse({
        'status': 'success',
        'quest_id': task_id,
        'hp_lost': hp_lost,
        'new_hp': profile.hp,
        'hp_percentage': hp_percentage,
        'game_over': game_over,
        'new_level': profile.level,
        'new_exp': profile.exp,
        'next_level_exp': next_level_exp,
        'exp_percentage': exp_percentage,
        'new_coins': profile.coins,
        'message': message,
    })


@login_required
@require_POST
def extend_deadline(request, task_id):
    """
    STEP 4: Extend Deadline via Coins
    - Max 3 extensions allowed per task
    - Cost scaling: 1st = 2 coins, 2nd = 5 coins, 3rd = 10 coins
    - Adds +1 day to due_date
    """
    task = get_object_or_404(Task, id=task_id, user=request.user, status='pending')
    profile = request.user.profile
    
    # Check max extensions
    if task.deadline_extensions >= 3:
        return JsonResponse({
            'status': 'error',
            'message': 'Maximum extensions (3) reached for this task.'
        }, status=400)
    
    # Cost scaling
    cost_map = {0: 2, 1: 5, 2: 10}
    cost = cost_map[task.deadline_extensions]
    
    # Check if user has enough coins
    if profile.coins < cost:
        return JsonResponse({
            'status': 'error',
            'message': f'Not enough coins. Need {cost} coins, you have {profile.coins}.'
        }, status=400)
    
    # Deduct coins and extend deadline
    profile.coins -= cost
    profile.save()
    
    task.due_date += timedelta(days=1)
    task.deadline_extensions += 1
    task.save()
    
    return JsonResponse({
        'status': 'success',
        'quest_id': task.id,
        'new_due_date': task.due_date.strftime('%Y-%m-%d'),
        'new_coins': profile.coins,
        'cost': cost,
        'extensions_used': task.deadline_extensions,
        'extensions_remaining': 3 - task.deadline_extensions,
    })

@login_required
@require_POST
def uncomplete_task(request, task_id):
    """
    🔒 COIN EXPLOIT FIX: Undo task and deduct EXACT coins earned
    - Remove XP gained from this task
    - Deduct EXACT coins that were earned (task.coins_earned)
    - Reset coins_earned to 0
    - Return task to pending state
    """
    task = get_object_or_404(Task, id=task_id, user=request.user)

    if task.status != 'completed':
        return JsonResponse({'status': 'error', 'message': 'Task is not completed.'}, status=400)

    profile = request.user.profile
    
    # Remove XP
    profile.remove_exp(task.difficulty)
    
    # 🔒 COIN EXPLOIT FIX: Deduct EXACT coins that this task gave
    coins_lost = task.coins_earned
    profile.coins = max(0, profile.coins - coins_lost)  # Don't go below 0
    profile.save()
    
    # Reset task state
    task.status = 'pending'
    task.completed_at = None
    task.coins_earned = 0  # Reset coins tracker
    task.save()

    next_level_exp = profile.get_next_level_exp()
    exp_percentage = round((profile.exp / next_level_exp) * 100, 2)
    hp_percentage = round((profile.hp / 100) * 100, 2)

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
    
    # Simple undo message per spec
    message = "Quest Undone"

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
        'new_hp': profile.hp,
        'new_coins': profile.coins,
        'exp_percentage': exp_percentage,
        'hp_percentage': hp_percentage,
        'next_level_exp': next_level_exp,
        'xp_lost': task.difficulty,
        'coins_lost': coins_lost,
        'message': message,
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