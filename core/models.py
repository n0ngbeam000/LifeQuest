from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# --- 1. User Profile (ระบบเก็บเลเวลและ Avatar) ---
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    exp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    
    def get_next_level_exp(self):
        """สูตรคำนวณ EXP ที่ต้องใช้: เลเวลปัจจุบัน * 100"""
        return self.level * 100

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
        (10, 'Easy (+10 XP)'),
        (30, 'Medium (+30 XP)'),
        (50, 'Hard (+50 XP)'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE) # ผูกงานกับ User คนนั้นๆ
    title = models.CharField(max_length=200)
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES, default=10)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.get_difficulty_display()})"