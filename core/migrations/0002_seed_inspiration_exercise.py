from django.db import migrations


INSPIRATIONS = [
    (1,   "千里之行，始于足下。今天迈出的第一步，就是最重要的一步！"),
    (3,   "三天打鱼两天晒网？不，你已经连续坚持 3 天了，继续加油！"),
    (7,   "一周了！科学证明，坚持 7 天会让行动开始成为习惯。"),
    (14,  "两周的坚持，你的身体已经悄悄发生了变化，继续保持！"),
    (21,  "21 天养成一个习惯——恭喜你，健康生活已经刻进你的基因！"),
    (30,  "一个月！你做到了许多人做不到的事情，你就是自己最好的榜样。"),
    (60,  "两个月的征途，汗水不会说谎，坚持的人最终都会被命运厚待。"),
    (100, "100 天！这不只是数字，这是意志力的勋章，是你写给自己的传奇。"),
]

EXERCISES = [
    (0.0,  18.5, "体重偏轻，建议以增肌为主：\n• 每周 3 次力量训练（深蹲、卧推、硬拉）\n• 配合高蛋白饮食，每公斤体重摄入 1.5g 蛋白质\n• 避免高强度有氧，以免消耗过多肌肉"),
    (18.5, 24.0, "体重正常，保持均衡运动：\n• 每周 3～5 次有氧（慢跑、游泳、骑车），每次 30～45 分钟\n• 每周 2 次力量训练维持肌肉量\n• 保持规律作息和均衡饮食即可"),
    (24.0, 28.0, "体重略超，建议适度减脂：\n• 每周 4～5 次有氧（快走、跳绳、游泳），每次 40～60 分钟\n• 控制精制碳水和油脂摄入，增加蔬菜比例\n• 每周 2 次低强度力量训练，防止肌肉流失"),
    (28.0, 32.0, "体重超重，需系统减脂：\n• 以低冲击有氧为主（快走、椭圆机、水中运动），保护关节\n• 每天保证 7000～10000 步基础活动量\n• 严格控制总热量摄入，建议咨询营养师"),
    (32.0, 99.9, "体重肥胖，优先保护关节安全运动：\n• 从每天 20～30 分钟散步开始，逐步增加强度\n• 推荐水中运动（浮力减轻关节压力）\n• 强烈建议在医生或专业教练指导下制定运动方案"),
]


def seed_data(apps, schema_editor):
    Inspiration = apps.get_model('core', 'Inspiration')
    ExerciseRecommendation = apps.get_model('core', 'ExerciseRecommendation')

    for days, content in INSPIRATIONS:
        Inspiration.objects.get_or_create(unlock_days=days, defaults={'content': content})

    for min_bmi, max_bmi, rec in EXERCISES:
        ExerciseRecommendation.objects.get_or_create(
            min_bmi=min_bmi, max_bmi=max_bmi,
            defaults={'recommendation': rec}
        )


def unseed_data(apps, schema_editor):
    # 回滚时只删除本次插入的行（通过 unlock_days 精确匹配）
    Inspiration = apps.get_model('core', 'Inspiration')
    ExerciseRecommendation = apps.get_model('core', 'ExerciseRecommendation')
    Inspiration.objects.filter(unlock_days__in=[d for d, _ in INSPIRATIONS]).delete()
    ExerciseRecommendation.objects.filter(
        min_bmi__in=[m for m, _, _ in EXERCISES]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_data, reverse_code=unseed_data),
    ]
