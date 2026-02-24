from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# 用户扩展信息表
class UserProfile(models.Model):
    GENDER_CHOICES = (
        ('M', '男'),
        ('F', '女'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="用户")
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png', verbose_name="头像")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M', verbose_name="性别")
    height = models.FloatField(verbose_name="身高(cm)")
    initial_weight = models.FloatField(verbose_name="初始体重(kg)")
    target_weight = models.FloatField(verbose_name="目标体重(kg)")
    streak_count = models.IntegerField(default=0, verbose_name="连续打卡天数")

    def get_bmi(self):
        # 避免除以 0 的错误
        if self.height <= 0:
            return 0
        height_m = self.height / 100
        return round(self.initial_weight / (height_m ** 2), 2)

    class Meta:
        verbose_name = "用户信息"
        verbose_name_plural = verbose_name
        
    def __str__(self):
        return f"{self.user.username} 的档案"

# 每日打卡记录表
class DailyRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    date = models.DateField(default=timezone.now, verbose_name="打卡日期")
    weight = models.FloatField(verbose_name="当日体重(kg)")
    calories_in = models.IntegerField(default=0, verbose_name="摄入热量(kcal)")
    calories_out = models.IntegerField(default=0, verbose_name="消耗热量(kcal)")
    summary = models.TextField(blank=True, verbose_name="减肥小结")

    class Meta:
        unique_together = ('user', 'date') # 保证每日一打卡
        verbose_name = "打卡记录"
        verbose_name_plural = verbose_name
        
    def __str__(self):
        return f"{self.user.username} - {self.date}"

# 励志内容表
class Inspiration(models.Model):
    unlock_days = models.IntegerField(unique=True, verbose_name="解锁天数")
    content = models.TextField(verbose_name="励志语录")

    class Meta:
        verbose_name = "励志语录"
        verbose_name_plural = verbose_name
        
    def __str__(self):
        return f"连续 {self.unlock_days} 天解锁内容"

# 运动推荐表 (满足要求基于 BMI 值的推荐)
class ExerciseRecommendation(models.Model):
    min_bmi = models.FloatField(verbose_name="最小 BMI 值")
    max_bmi = models.FloatField(verbose_name="最大 BMI 值")
    recommendation = models.TextField(verbose_name="运动推荐方案")

    class Meta:
        verbose_name = "BMI运动推荐"
        verbose_name_plural = verbose_name
        
    def __str__(self):
        return f"BMI ({self.min_bmi} - {self.max_bmi}) 推荐"