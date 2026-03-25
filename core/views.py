# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from core.models import UserProfile, DailyRecord, Inspiration, ExerciseRecommendation
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
import json
import urllib.request

# 登录注册视图（合并在一起，前端通过隐藏字段区分）
def auth_view(request):
    # 如果用户已经登录，直接跳回首页
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        action = request.POST.get('action') # 通过前端隐藏字段判断是登录还是注册
        # ================= 登录逻辑 =================
        if action == 'login':
            u = request.POST.get('username')
            p = request.POST.get('password')
            user = authenticate(request, username=u, password=p)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, '用户名或密码错误，请重试！')
        # ================= 注册逻辑 =================
        elif action == 'register':
            u = request.POST.get('username')
            p = request.POST.get('password')
            cp = request.POST.get('confirm_password')
            gender = request.POST.get('gender')
            height = request.POST.get('height')
            weight = request.POST.get('initial_weight')
            target = request.POST.get('target_weight')
            # 基础校验
            if p != cp:
                messages.error(request, '两次输入的密码不一致！')
            elif User.objects.filter(username=u).exists():
                messages.error(request, '该用户名已被注册！')
            else:
                try:
                    # 1. 创建基础账号
                    user = User.objects.create_user(username=u, password=p)
                    # 2. 绑定创建身体档案 (UserProfile)
                    UserProfile.objects.create(
                        user=user,
                        gender=gender,
                        height=float(height),
                        initial_weight=float(weight),
                        target_weight=float(target)
                    )
                    # 3. 注册成功后自动登录并跳转
                    login(request, user)
                    messages.success(request, '注册成功，欢迎开启减肥之旅！')
                    return redirect('home')
                except Exception as e:
                    # 捕获数据转换错误（比如身高填了字母）
                    messages.error(request, f'注册失败，请检查数据格式是否正确。')

    return render(request, 'auth.html')

@login_required(login_url='/auth/')
def home_view(request):
    user = request.user
    profile = user.userprofile
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)

    records = list(DailyRecord.objects.filter(user=user, date__gte=thirty_days_ago).order_by('date'))

    dates = [r.date.strftime('%m-%d') for r in records]
    weights = [r.weight for r in records]
    calories_in = [r.calories_in for r in records]
    calories_out = [r.calories_out for r in records]

    # 目标进度：(初始体重 - 当前最新体重) / (初始体重 - 目标体重) * 100%
    latest_weight = records[-1].weight if records else profile.initial_weight
    initial = profile.initial_weight
    target = profile.target_weight
    if initial != target:
        progress = round((initial - latest_weight) / (initial - target) * 100, 1)
        progress = max(0, min(100, progress))
    else:
        progress = 0

    # 励志系统：找到 streak_count 能解锁的最高级语录
    inspiration = Inspiration.objects.filter(
        unlock_days__lte=profile.streak_count
    ).order_by('-unlock_days').first()

    # BMI 运动推荐：根据当前 BMI 匹配区间
    bmi = profile.get_bmi()
    exercise_rec = ExerciseRecommendation.objects.filter(
        min_bmi__lte=bmi, max_bmi__gte=bmi
    ).first()

    context = {
        'dates_json': json.dumps(dates),
        'weights_json': json.dumps(weights),
        'calories_in_json': json.dumps(calories_in),
        'calories_out_json': json.dumps(calories_out),
        'latest_weight': latest_weight,
        'progress': progress,
        'inspiration': inspiration,
        'exercise_rec': exercise_rec,
        'bmi': bmi,
    }
    return render(request, 'home.html', context)

def logout_view(request):
    logout(request)
    return redirect('auth') # 退出后跳回登录页

# 个人资料编辑视图（允许修改性别、身高、目标体重和头像）
@login_required(login_url='/auth/')
def profile_edit_view(request):
    user = request.user
    profile = user.userprofile

    if request.method == 'POST':
        # 1. 获取普通文本数据
        gender = request.POST.get('gender')
        height = request.POST.get('height')
        target_weight = request.POST.get('target_weight')
        initial_weight = request.POST.get('initial_weight')

        # 2. 更新资料
        profile.gender = gender
        if height:
            profile.height = float(height)
        if target_weight:
            profile.target_weight = float(target_weight)
        if initial_weight:
            profile.initial_weight = float(initial_weight)

        # 3. 处理头像文件上传 (关键点：从 request.FILES 获取)
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']

        # 4. 保存到数据库
        profile.save()
        messages.success(request, '个人资料与头像已成功更新！')
        return redirect('profile_edit') # 更新后刷新当前页面

    # GET 请求：渲染页面
    return render(request, 'profile_edit.html', {'profile': profile})

# 打卡视图：每天记录体重、摄入热量、消耗热量和总结
@login_required(login_url='/auth/')
def check_in_view(request):
    today = timezone.now().date()
    user = request.user
    has_checked_in = DailyRecord.objects.filter(user=user, date=today).exists()
    if request.method == 'POST':
        if has_checked_in:
            messages.warning(request, '今日已完成打卡')
            return redirect('check_in')
        weight = request.POST.get('weight')
        calories_in = request.POST.get('calories_in')
        calories_out = request.POST.get('calories_out')
        summary = request.POST.get('summary')
        DailyRecord.objects.create(
            user=user,
            date=today,
            weight=float(weight),
            calories_in=int(calories_in),
            calories_out=int(calories_out),
            summary=summary
        )
        profile = user.userprofile
        yesterday = today - timedelta(days=1)
        if DailyRecord.objects.filter(user=user, date=yesterday).exists():
            profile.streak_count += 1
        else:
            profile.streak_count = 1
        profile.save()
        messages.success(request, '打卡成功')
        return redirect('home')
    return render(request, 'check_in.html', {'has_checked_in': has_checked_in})

@login_required(login_url='/auth/')
def history_view(request):
    records = DailyRecord.objects.filter(user=request.user).order_by('-date')
    return render(request, 'history.html', {'records': records})

@login_required(login_url='/auth/')
def record_edit_view(request, record_id):
    record = get_object_or_404(DailyRecord, id=record_id, user=request.user)
    
    if request.method == 'POST':
        record.weight = float(request.POST.get('weight'))
        record.calories_in = int(request.POST.get('calories_in'))
        record.calories_out = int(request.POST.get('calories_out'))
        record.summary = request.POST.get('summary')
        record.save()
        messages.success(request, '记录已更新')
        return redirect('history')
        
    return render(request, 'record_edit.html', {'record': record})

@login_required(login_url='/auth/')
def record_delete_view(request, record_id):
    record = get_object_or_404(DailyRecord, id=record_id, user=request.user)
    if request.method == 'POST':
        record.delete()
        messages.success(request, '记录已删除')
    return redirect('history')


@login_required(login_url='/auth/')
def ai_chat_view(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': '请求格式错误'}, status=400)

        user_message = body.get('message', '').strip()
        history = body.get('history', [])  # 前端维护的多轮对话历史

        if not user_message:
            return JsonResponse({'error': '消息不能为空'}, status=400)

        profile = request.user.userprofile
        bmi = profile.get_bmi()
        gender_str = '男' if profile.gender == 'M' else '女'
        system_prompt = (
            f"你是一位专业的减肥健康顾问。用户基本信息：性别{gender_str}、"
            f"身高{profile.height}cm、当前体重{profile.initial_weight}kg、"
            f"目标体重{profile.target_weight}kg、BMI {bmi}、"
            f"已连续打卡{profile.streak_count}天。"
            "请根据用户实际情况给出科学、实用、鼓励性的减肥建议，回答简洁易懂。"
        )

        # 构造多轮对话消息列表
        api_messages = [{"role": "system", "content": system_prompt}]
        api_messages.extend(history)
        api_messages.append({"role": "user", "content": user_message})

        payload = json.dumps({
            "model": "deepseek-chat",
            "messages": api_messages,
            "max_tokens": 1024,
        }).encode()

        req = urllib.request.Request(
            'https://api.deepseek.com/chat/completions',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {settings.DEEPSEEK_API_KEY}',
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
            reply = result['choices'][0]['message']['content']
            return JsonResponse({'reply': reply})
        except Exception:
            return JsonResponse({'error': 'AI 服务暂时不可用，请稍后重试。'}, status=500)

    return render(request, 'ai_chat.html')


@login_required(login_url='/auth/')
def calendar_view(request):
    user = request.user
    year = timezone.now().year

    records = DailyRecord.objects.filter(
        user=user, date__year=year
    ).values('date', 'calories_in', 'calories_out')

    # ECharts calendar 数据格式：[日期字符串, 净摄入热量]
    # 正数 = 热量盈余（摄入>消耗），负数 = 赤字（消耗>摄入，减脂有效）
    calendar_data = [
        [r['date'].strftime('%Y-%m-%d'), r['calories_in'] - r['calories_out']]
        for r in records
    ]

    context = {
        'calendar_json': json.dumps(calendar_data),
        'year': year,
        'total_days': len(calendar_data),
    }
    return render(request, 'calendar.html', context)