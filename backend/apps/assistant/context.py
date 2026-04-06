from datetime import date, timedelta

from apps.tracking.models import HealthGoal, MealRecord


GOAL_TYPE_MAP = {
    "weight_loss": "减重", "muscle_gain": "增肌", "blood_sugar_control": "控糖",
    "fat_control": "控脂", "protein_up": "提升蛋白摄入", "diet_balance": "饮食均衡",
}

ADMIN_PAGE_CONTEXTS = {
    "ops": {
        "label": "后台总览页",
        "summary": "用于判断今天后台最该先处理哪条主线，再跳到具体模块。",
        "features": [
            "顶部动作：刷新总览、进入操作日志、进入运营复核、回前台首页。",
            "汇总卡片：待处理账号、当前活跃用户、内容待处理总量、报表失败任务。",
            "队列提醒：按积压量给出可直接进入处理的后台入口。",
            "最近待处理对象：可直接跳到具体对象或模块继续处理。",
            "快捷入口：待确认账号、社区举报、待审核菜谱、报表链路、操作日志。",
            "最近报表任务与附加指标：辅助判断系统最近是否有人在持续使用。",
        ],
        "workflow": [
            "先看四张汇总卡片判断当前是账号问题、内容积压还是报表链路问题。",
            "再看队列提醒和最近待处理对象，优先处理最容易阻塞后台节奏的入口。",
            "如果没有明显积压，再回看最近报表任务和操作日志做常规复核。",
        ],
        "risks": [
            "不要在总览页假设已经完成了具体处理，真正修改通常要跳到对应模块。",
            "如果用户问具体按钮，优先引导到当前可见的快捷入口或对应模块，而不是编造总览内不存在的编辑动作。",
        ],
    },
    "ops:users": {
        "label": "用户管理页",
        "summary": "用于处理账号状态、角色、套餐、资料和健康约束。",
        "features": [
            "筛选：关键词、角色、状态，支持应用筛选、重置筛选和预设视角。",
            "批量动作：批量启用、批量停用。",
            "列表字段：用户、联系方式、角色、状态、套餐、档案完整度、健康提示、最近登录、管理判断。",
            "单个处理入口：查看并处理，会打开右侧抽屉。",
            "抽屉可改：用户名、昵称、邮箱、手机号、角色、状态、套餐、签名、身高体重目标体重、活动水平、饮食偏好、饮食类型、职业、外食频率、过敏标签、忌口标签、备注。",
            "抽屉底部：保存修改，并可查看该用户相关操作日志。",
        ],
        "workflow": [
            "先用关键词、角色、状态缩小范围。",
            "再看表格里的角色、状态、档案完整度和健康提示，判断是资料问题还是权限/状态问题。",
            "需要落地处理时打开“查看并处理”抽屉，再做单个保存或批量启停。",
        ],
        "risks": [
            "角色变更、停用账号和管理员账号修改都属于高风险动作，回答时要提醒复核权限边界。",
            "批量动作适合处理明确同类对象，不适合替代逐个复核资料差异。",
        ],
    },
    "ops:community": {
        "label": "社区审核页",
        "summary": "用于处理帖子审核、举报协作和评论隐藏。",
        "features": [
            "帖子侧筛选：关键词、帖子状态、审核结论。",
            "帖子批量动作：批量通过、批量驳回、批量归档。",
            "帖子列表会显示状态、审核、互动、隐藏评论数、举报数、管理判断。",
            "帖子抽屉可改：帖子状态、审核结论、标题、正文，并可隐藏评论。",
            "举报侧筛选：关键词、处理状态、优先级、处理人。",
            "举报批量动作：批量标记已处理、批量驳回。",
            "举报抽屉可改：处理状态、优先级、指派处理人、跟进时间、内部备注，并可直接标记已处理或驳回。",
        ],
        "workflow": [
            "先区分当前要处理的是帖子审核还是举报。",
            "帖子侧先看审核状态、举报数和隐藏评论数，再决定通过、驳回还是归档。",
            "举报侧先核对目标帖子当前状态，再决定指派、备注、标记已处理或驳回。",
        ],
        "risks": [
            "不要把“隐藏评论”和“驳回帖子/举报”混为一谈，它们处理层级不同。",
            "复杂举报应先补指派和内部备注，再给最终结论。",
        ],
    },
    "ops:reports": {
        "label": "运营复核页",
        "summary": "用于查看活跃指标、待处理内容、报表失败任务和最近报表任务。",
        "features": [
            "顶部动作：刷新总览、去前台报表页。",
            "汇总卡片：活跃用户、待处理内容、报表失败任务等。",
            "队列提醒：用来判断当前更偏审核清队列，还是偏报表链路排查。",
            "最近待处理对象：可直接跳到具体对象处理。",
            "最近报表任务：查看处理状态，区分 waiting、processing、completed、failed。",
            "附加指标：帮助判断增长、留存、真实记录量和报表链路稳定性。",
        ],
        "workflow": [
            "先看活跃、待处理内容和失败任务三类信号，判断当前后台主线。",
            "如果失败任务多，优先排报表链路；如果内容积压多，优先回审核模块；如果活跃和记录量不匹配，再回前台链路复核。",
            "最后结合最近报表任务确认是单点异常还是持续性问题。",
        ],
        "risks": [
            "这页偏判断和分流，不是直接编辑数据的主战场。",
            "不要把运营指标异常直接解释成单一原因，应先引导去对应模块复核。",
        ],
    },
    "ops:logs": {
        "label": "操作日志页",
        "summary": "用于追溯谁改了什么、改了哪些字段、属于哪个模块。",
        "features": [
            "筛选：模块、操作人、关键词，支持应用筛选、重置筛选和预设视角。",
            "摘要卡片：按用户管理、菜谱管理、社区审核、运营复核拆分动作量。",
            "日志列表：重点看对象、动作摘要、字段前后变化、操作人和时间。",
            "适合按对象或操作人回看完整处理轨迹。",
        ],
        "workflow": [
            "先按模块或操作人收窄范围。",
            "再看字段前后变化，确认是状态改动、内容改动还是备注类动作。",
            "如果要继续处理问题，再跳回原模块，而不是停留在日志页本身。",
        ],
        "risks": [
            "日志页主要用于追溯，不适合把它说成直接处理页面。",
            "没有字段变化的日志更多是轨迹记录，不能等同于有效处理结果。",
        ],
    },
    "ops:recipes": {
        "label": "菜谱管理页",
        "summary": "用于处理菜谱审核、发布状态、Pro 标记和基础营养信息。",
        "features": [
            "筛选：关键词、状态、审核结论、来源。",
            "批量动作：批量通过、批量驳回、批量归档。",
            "列表字段：菜谱、餐次/用时、状态、审核、Pro 专属、来源、内容完整度、管理判断。",
            "单个处理入口：查看并处理，会打开右侧抽屉。",
            "抽屉可改：状态、审核结论、Pro 专属、标题、描述、餐次、来源名称和多项营养字段。",
            "需要深度编辑时，会引导回前台菜谱页处理完整内容。",
        ],
        "workflow": [
            "先按状态、审核结论和来源缩小范围。",
            "再看内容完整度和管理判断，决定是通过、驳回、归档还是补基础信息。",
            "单个处理时进入抽屉，先定状态和审核，再补标题描述与营养信息。",
        ],
        "risks": [
            "Pro 专属不是普通质量标签，只适用于管理员上传的菜谱。",
            "缺营养信息会影响前台推荐与报表解释，回答时要提醒优先补齐。",
        ],
    },
}


def _admin_role_label(user):
    role = getattr(user, "role", "") or ""
    if role == "auditor":
        return "审核员"
    if role == "admin" or getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return "管理员"
    return "后台用户"


def _build_admin_context(user, page_context: str):
    parts = [
        "你是一位智能后台操作助手，名叫「小食」，服务于健康管理系统的运营和管理人员。",
        "请直接、简洁地回答后台管理相关问题，包括用户管理、内容审核、运营数据分析、系统操作等。",
        "所有回复必须使用中文。如用户询问具体操作步骤，优先给出清晰的步骤说明。",
        "优先使用当前页面真实存在的按钮、筛选项、抽屉、批量动作和字段名称，不要编造不存在的后台能力。",
        "如果当前页面做不到用户要的动作，要明确指出应该跳到哪个后台模块继续处理，并说明原因。",
        "如果用户没有提供具体对象或真实数据，不要假设后台结果；按当前页面的通用处理流程回答。",
        "当用户问“先看哪里”“下一步做什么”“有哪些风险”时，优先按“先看 -> 再做 -> 风险提醒”的结构回答。",
        f"当前提问者身份：{_admin_role_label(user)}。",
    ]

    page_info = ADMIN_PAGE_CONTEXTS.get(page_context)
    if page_info:
        parts.append(f"\n## 当前页面\n{page_info['label']}——{page_info['summary']}")
        parts.append("\n## 页面能力\n" + "\n".join(f"- {item}" for item in page_info["features"]))
        parts.append("\n## 推荐处理顺序\n" + "\n".join(f"- {item}" for item in page_info["workflow"]))
        parts.append("\n## 风险提醒\n" + "\n".join(f"- {item}" for item in page_info["risks"]))

    return "\n".join(parts)


def build_user_context(user, page_context: str = ""):
    is_admin = bool(page_context and (page_context == "ops" or page_context.startswith("ops:")))

    if is_admin:
        return _build_admin_context(user, page_context)
    else:
        parts = [
            "你是一位专业的营养师AI助手，名叫「小食」。请基于以下用户档案提供个性化的营养和饮食建议。",
            "所有回复必须使用中文。建议应具体、可执行。",
        ]

    # 基本信息
    try:
        p = user.profile
        info = []
        if p.gender:
            info.append(f"性别：{p.gender}")
        if p.birthday:
            age = (date.today() - p.birthday).days // 365
            info.append(f"年龄：{age}岁")
        if p.height_cm:
            info.append(f"身高：{p.height_cm}cm")
        if p.weight_kg:
            info.append(f"体重：{p.weight_kg}kg")
        if p.target_weight_kg:
            info.append(f"目标体重：{p.target_weight_kg}kg")
        if p.activity_level:
            info.append(f"活动水平：{p.activity_level}")
        if p.cooking_skill:
            info.append(f"烹饪水平：{p.cooking_skill}")
        if p.diet_type:
            info.append(f"饮食类型：{p.diet_type}")
        if info:
            parts.append(f"\n## 用户基本信息\n{'，'.join(info)}")
    except Exception:
        pass

    # 健康状况
    try:
        h = user.health_condition
        items = []
        if h.allergy_tags:
            items.append(f"过敏原：{', '.join(h.allergy_tags)}")
        if h.avoid_food_tags:
            items.append(f"忌口：{', '.join(h.avoid_food_tags)}")
        if h.has_hypertension:
            items.append("高血压：是")
        if h.has_diabetes:
            items.append("糖尿病：是")
        if h.has_hyperlipidemia:
            items.append("高血脂：是")
        if h.is_pregnant:
            items.append("孕期：是")
        if h.is_lactating:
            items.append("哺乳期：是")
        if items:
            parts.append(f"\n## 健康状况\n{'；'.join(items)}")
    except Exception:
        pass

    # 当前目标
    goals = HealthGoal.objects.filter(user=user, status="active")
    if goals.exists():
        lines = []
        for g in goals[:3]:
            label = GOAL_TYPE_MAP.get(g.goal_type, g.goal_type)
            line = f"- {label}"
            if g.target_value:
                line += f"，目标值{g.target_value}"
            if g.current_value:
                line += f"，当前{g.current_value}"
            lines.append(line)
        parts.append(f"\n## 当前健康目标\n" + "\n".join(lines))

    # 近7天饮食
    week_ago = date.today() - timedelta(days=7)
    records = (
        MealRecord.objects.filter(user=user, record_date__gte=week_ago)
        .prefetch_related("items")
        .order_by("-record_date")[:14]
    )
    if records:
        meal_lines = []
        for r in records:
            items_str = "、".join(
                f"{i.ingredient_name_snapshot or '食物'}({int(i.energy or 0)}kcal)"
                for i in r.items.all()[:5]
            )
            if items_str:
                meal_type_map = {"breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐", "snack": "加餐"}
                meal_lines.append(f"- {r.record_date} {meal_type_map.get(r.meal_type, r.meal_type)}：{items_str}")
        if meal_lines:
            parts.append(f"\n## 近7天饮食记录\n" + "\n".join(meal_lines[:10]))

    # 收藏菜谱
    favs = user.favorite_recipes.select_related("recipe").order_by("-created_at")[:10]
    if favs:
        titles = [f.recipe.title for f in favs if f.recipe]
        if titles:
            parts.append(f"\n## 收藏的菜谱\n{'、'.join(titles)}")

    parts.append("\n## 注意事项\n- 必须考虑用户的过敏原和忌口\n- 回复简洁实用，避免过长")
    return "\n".join(parts)
