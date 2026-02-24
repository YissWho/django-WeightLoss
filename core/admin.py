from django.contrib import admin
from django.utils.html import format_html # 必须导入这个工具
from .models import UserProfile, DailyRecord, Inspiration, ExerciseRecommendation

# 自定义后台标题
admin.site.site_header = '个人减肥打卡管理系统'
admin.site.site_title = '系统管理'
admin.site.index_title = '数据概览'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    # 在列表中添加 'display_avatar' 字段
    list_display = ['user', 'display_avatar', 'gender', 'height', 'initial_weight', 'target_weight', 'streak_count']
    search_fields = ['user__username']

    # 定义显示头像的方法
    def display_avatar(self, obj):
        if obj.avatar:
            # 返回 HTML 代码，设置图片宽高度，'border-radius' 配合 SimpleUI 效果更好
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; border-radius: 50%;" />',
                obj.avatar.url
            )
        return "无头像"
    
    # 设置后台显示的列标题
    display_avatar.short_description = '头像'
    
@admin.register(DailyRecord)
class DailyRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'weight', 'calories_in', 'calories_out']
    list_filter = ['date', 'user']
    ordering = ['-date']

@admin.register(Inspiration)
class InspirationAdmin(admin.ModelAdmin):
    list_display = ['unlock_days', 'content']

@admin.register(ExerciseRecommendation)
class ExerciseRecommendationAdmin(admin.ModelAdmin):
    list_display = ['min_bmi', 'max_bmi', 'recommendation']