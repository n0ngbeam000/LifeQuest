from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

# --- 1. User Profile (ระบบเก็บเลเวลและ Avatar) ---
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    exp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    
    # RPG Mechanics - HP and Coins
    hp = models.IntegerField(default=100)
    coins = models.IntegerField(default=0)
    
    # Daily Limits Tracking
    daily_xp_count = models.IntegerField(default=0)  # Track daily XP earned (max 678)
    daily_hp_healed = models.IntegerField(default=0)  # Track daily HP healed (max 10)
    last_daily_reset = models.DateField(default=timezone.now)  # Last reset date
    
    def get_next_level_exp(self):
        """สูตรคำนวณ EXP ที่ต้องใช้: เลเวลปัจจุบัน * 100"""
        return self.level * 123

    def check_level_up(self):
        """เช็คว่า EXP เกินหลอดหรือยัง ถ้าเกินให้ Level Up"""
        required_exp = self.get_next_level_exp()
        if self.exp >= required_exp:
            self.exp -= required_exp # หัก EXP ออกเพื่อเริ่มหลอดใหม่ (แบบเกม RPG)
            self.level += 1
            self.save()
            return True
        return False

    def get_avatar_image(self):
        """คืนค่า path ของรูปภาพตามเลเวล (ธีมวิศวะ KKU)"""
        if self.level <= 5:
            return 'images/avatars/freshy.png'      # เลเวล 1-5: ชุดนักศึกษา
        elif self.level <= 15:
            return 'images/avatars/engineer_gear.png' # เลเวล 6-15: เสื้อช็อป
        else:
            return 'images/avatars/graduate.png'    # เลเวล 16+: ชุดครุย

    def remove_exp(self, amount):
        """หัก EXP ออก และจัดการ Level Down ถ้า EXP ติดลบ"""
        self.exp -= amount

        # Level Down loop: ถ้า EXP ติดลบและยังไม่ถึง Lv1
        while self.exp < 0 and self.level > 1:
            self.level -= 1
            max_exp_this_level = self.level * 123  # same formula as get_next_level_exp
            self.exp += max_exp_this_level

        # Safety net: ไม่ให้ต่ำกว่า Lv1 / 0 XP
        if self.level == 1 and self.exp < 0:
            self.exp = 0

        self.save()

    def __str__(self):
        return f"{self.user.username} - Lv {self.level}"

# Signal: เมื่อมีการสร้าง User ใหม่ ให้สร้าง UserProfile ตามมาด้วยอัตโนมัติ
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# --- 2. Task (ระบบ To-Do List) ---
class Task(models.Model):
    # ความยากง่าย (ได้ XP ต่างกัน)
    DIFFICULTY_CHOICES = [
        (10,  'Easy (+10 XP)'),
        (30,  'Medium (+30 XP)'),
        (50,  'Hard (+50 XP)'),
        (100, 'Epic (+100 XP)'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES, default=10)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)  # set when task is completed
    
    # Deadline and Penalty System
    due_date = models.DateField()  # Required deadline for the task
    deadline_extensions = models.IntegerField(default=0)  # Track extension purchases (max 3)
    last_damage_date = models.DateField(null=True, blank=True)  # Track overdue damage application
    
    # Coin Exploit Fix: Track exact coins earned to prevent farming
    coins_earned = models.IntegerField(default=0)  # Exact coins this task gave

    def __str__(self):
        return f"{self.title} ({self.get_difficulty_display()})"