# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile
from django.contrib.auth.decorators import login_required
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
    # 渲染刚才新建的 home.html
    return render(request, 'home.html')

def logout_view(request):
    logout(request)
    return redirect('auth') # 退出后跳回登录页

@login_required(login_url='/auth/')
def profile_edit_view(request):
    user = request.user
    profile = user.userprofile

    if request.method == 'POST':
        # 1. 获取普通文本数据
        gender = request.POST.get('gender')
        height = request.POST.get('height')
        target_weight = request.POST.get('target_weight')

        # 2. 更新资料
        profile.gender = gender
        if height:
            profile.height = float(height)
        if target_weight:
            profile.target_weight = float(target_weight)

        # 3. 处理头像文件上传 (关键点：从 request.FILES 获取)
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']

        # 4. 保存到数据库
        profile.save()
        messages.success(request, '个人资料与头像已成功更新！')
        return redirect('profile_edit') # 更新后刷新当前页面

    # GET 请求：渲染页面
    return render(request, 'profile_edit.html', {'profile': profile})