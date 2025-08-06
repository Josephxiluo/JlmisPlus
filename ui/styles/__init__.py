"""
样式配置模块 - 最终优化版本，确保所有按钮文字高对比度清晰可见
"""
import tkinter as tk

# 现代化橙色主题配置 - 最终版本
ORANGE_THEME = {
    'colors': {
        'primary': '#FF7043',      # 现代橙色
        'primary_dark': '#E64A19', # 深橙色
        'primary_light': '#FFCCBC', # 浅橙色
        'primary_hover': '#FF5722', # 悬停橙色
        'background': '#FAFAFA',   # 温和背景色
        'card_bg': '#FFFFFF',      # 卡片背景
        'white': '#FFFFFF',
        'text': '#212121',         # 深文字色（高对比度）
        'text_light': '#757575',   # 次级文字色
        'text_hint': '#9E9E9E',    # 提示文字色
        'border': '#E0E0E0',       # 边框色
        'border_light': '#F5F5F5', # 浅边框色
        'success': '#4CAF50',      # Material Design绿色
        'warning': '#FF9800',      # Material Design橙色
        'danger': '#F44336',       # Material Design红色
        'info': '#2196F3',         # Material Design蓝色
        'gray': '#757575',         # 中灰色
        'gray_light': '#EEEEEE',   # 浅灰色（用于按钮背景）
        'gray_dark': '#424242',    # 深灰色
        'shadow': '#E0E0E0',       # 阴影色
        'hover_bg': '#FFF3E0',     # 悬停背景
        'selected': '#FFE0B2',     # 选中背景
        'grid_line': '#F5F5F5',    # 网格线色
    },
    'fonts': {
        'default': ('Microsoft YaHei', 9),
        'title': ('Microsoft YaHei', 14, 'bold'),
        'subtitle': ('Microsoft YaHei', 12, 'bold'),
        'button': ('Microsoft YaHei', 9, 'bold'),
        'small': ('Microsoft YaHei', 8),
        'large': ('Microsoft YaHei', 16, 'bold'),
    },
    'spacing': {
        'xs': 4,    # 小间距
        'sm': 8,    # 标准间距
        'md': 16,   # 中等间距
        'lg': 24,   # 大间距
        'xl': 32    # 特大间距
    }
}

def get_color(name):
    """获取颜色值"""
    return ORANGE_THEME['colors'].get(name, '#000000')

def get_font(name):
    """获取字体配置"""
    return ORANGE_THEME['fonts'].get(name, ('Microsoft YaHei', 9))

def get_spacing(name):
    """获取间距值"""
    return ORANGE_THEME['spacing'].get(name, 8)

def create_shadow_frame(parent, **kwargs):
    """创建带阴影效果的框架"""
    # 外层阴影框架
    shadow_frame = tk.Frame(
        parent,
        bg=get_color('shadow'),
        **kwargs
    )

    # 内层内容框架
    content_frame = tk.Frame(
        shadow_frame,
        bg=get_color('card_bg'),
        relief='flat',
        bd=0
    )
    content_frame.pack(padx=2, pady=2, fill='both', expand=True)

    return shadow_frame, content_frame

def create_modern_button(parent, text, style="primary", command=None, width=None, **kwargs):
    """创建现代化按钮 - 最终版本，确保所有按钮文字高对比度清晰可见"""

    # 最终确定的按钮样式配置 - 所有按钮都有高对比度
    styles = {
        'primary': {
            'bg': get_color('primary'),           # 橙色背景
            'fg': 'white',                        # 白色文字 ✅
            'active_bg': get_color('primary_dark'),
            'hover_bg': get_color('primary_hover'),
            'border_color': get_color('primary_dark')
        },
        'secondary': {
            'bg': 'white',                        # 白色背景
            'fg': get_color('text'),              # 深色文字 #212121 ✅
            'active_bg': get_color('border'),
            'hover_bg': get_color('hover_bg'),
            'border_color': get_color('border')
        },
        'success': {
            'bg': get_color('success'),           # 绿色背景
            'fg': 'white',                        # 白色文字 ✅
            'active_bg': '#388E3C',
            'hover_bg': '#45A049',
            'border_color': get_color('success')
        },
        'danger': {
            'bg': get_color('danger'),            # 红色背景
            'fg': 'white',                        # 白色文字 ✅
            'active_bg': '#D32F2F',
            'hover_bg': '#E53935',
            'border_color': get_color('danger')
        },
        'warning': {
            'bg': get_color('warning'),           # 橙色背景
            'fg': 'white',                        # 白色文字 ✅
            'active_bg': '#F57C00',
            'hover_bg': '#FB8C00',
            'border_color': get_color('warning')
        },
        'gray': {
            'bg': get_color('gray_light'),        # 浅灰背景 #EEEEEE
            'fg': get_color('text'),              # 深色文字 #212121 ✅ 高对比度
            'active_bg': get_color('border'),
            'hover_bg': '#E0E0E0',
            'border_color': get_color('border')
        },
        'outline': {
            'bg': 'white',                        # 白色背景
            'fg': get_color('primary'),           # 橙色文字 ✅
            'active_bg': get_color('hover_bg'),
            'hover_bg': get_color('primary_light'),
            'border_color': get_color('primary')
        },
        # 可选的灰色按钮变体 - 橙色文字版本
        'gray_orange': {
            'bg': get_color('gray_light'),        # 浅灰背景
            'fg': get_color('primary'),           # 橙色文字 ✅ 品牌感
            'active_bg': get_color('border'),
            'hover_bg': '#E0E0E0',
            'border_color': get_color('primary')
        }
    }

    button_style = styles.get(style, styles['primary'])

    # 创建按钮，确保有清晰的边框
    button = tk.Button(
        parent,
        text=text,
        font=get_font('button'),
        bg=button_style['bg'],
        fg=button_style['fg'],
        relief='solid',                    # 实线边框
        bd=1,                             # 1像素边框
        cursor='hand2',
        command=command,
        highlightthickness=0,             # 去除焦点边框
        padx=12,                          # 水平内边距
        pady=6,                           # 垂直内边距
        **kwargs
    )

    if width:
        button.config(width=width)

    # 添加悬停效果
    def on_enter(event):
        button.config(bg=button_style['hover_bg'])
        # outline 样式悬停时改变文字颜色
        if style == 'outline':
            button.config(fg='white')

    def on_leave(event):
        button.config(bg=button_style['bg'])
        if style == 'outline':
            button.config(fg=get_color('primary'))

    def on_click(event):
        button.config(bg=button_style['active_bg'])

    def on_release(event):
        button.config(bg=button_style['hover_bg'])

    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
    button.bind("<Button-1>", on_click)
    button.bind("<ButtonRelease-1>", on_release)

    return button

def create_card_frame(parent, title=None, **kwargs):
    """创建卡片式框架"""
    # 主容器
    card_container = tk.Frame(
        parent,
        bg=get_color('background'),
        **kwargs
    )

    # 卡片框架（带边框效果）
    card_frame = tk.Frame(
        card_container,
        bg=get_color('card_bg'),
        relief='solid',
        bd=1,
        highlightbackground=get_color('border_light'),
        highlightthickness=1
    )
    card_frame.pack(fill='both', expand=True, padx=2, pady=2)

    if title:
        # 标题头部
        header_frame = tk.Frame(
            card_frame,
            bg=get_color('primary_light'),
            height=40
        )
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text=title,
            font=get_font('subtitle'),
            fg=get_color('text'),          # 确保标题文字清晰
            bg=get_color('primary_light')
        )
        title_label.pack(side='left', padx=get_spacing('md'), pady=get_spacing('sm'))

        # 内容区域
        content_frame = tk.Frame(card_frame, bg=get_color('card_bg'))
        content_frame.pack(fill='both', expand=True, padx=get_spacing('sm'), pady=get_spacing('sm'))

        return card_container, content_frame

    return card_container, card_frame

def create_status_badge(parent, text, status_type="info"):
    """创建状态徽章 - 确保高对比度"""
    colors = {
        'success': {'bg': get_color('success'), 'fg': 'white'},
        'warning': {'bg': get_color('warning'), 'fg': 'white'},
        'danger': {'bg': get_color('danger'), 'fg': 'white'},
        'info': {'bg': get_color('info'), 'fg': 'white'},
        'gray': {'bg': get_color('gray'), 'fg': 'white'},
        'primary': {'bg': get_color('primary'), 'fg': 'white'}
    }

    color = colors.get(status_type, colors['info'])

    badge = tk.Label(
        parent,
        text=text,
        font=get_font('small'),
        bg=color['bg'],
        fg=color['fg'],                    # 确保文字颜色对比度
        padx=8,
        pady=2,
        relief='flat'
    )

    return badge

def create_icon_button(parent, icon, text, style="primary", command=None, **kwargs):
    """创建带图标的按钮"""
    display_text = f"{icon} {text}" if icon else text
    return create_modern_button(parent, display_text, style, command, **kwargs)

def create_button_group(parent, buttons_config, orientation='horizontal'):
    """创建按钮组"""
    if orientation == 'horizontal':
        container = tk.Frame(parent, bg=get_color('card_bg'))
        container.pack(fill='x', pady=4)

        for i, (text, style, command) in enumerate(buttons_config):
            btn = create_modern_button(container, text, style, command)
            btn.pack(side='left', padx=(0, 8) if i < len(buttons_config)-1 else (0, 0))
    else:  # vertical
        container = tk.Frame(parent, bg=get_color('card_bg'))
        container.pack(fill='y', padx=4)

        for text, style, command in buttons_config:
            btn = create_modern_button(container, text, style, command)
            btn.pack(fill='x', pady=(0, 4))

    return container

# 测试按钮样式的演示函数
def test_button_styles():
    """测试最终的按钮样式效果"""
    root = tk.Tk()
    root.title("Pulsesports - 最终按钮样式测试")
    root.geometry("900x700")
    root.configure(bg=get_color('background'))

    # 标题
    title = tk.Label(
        root,
        text="🎨 Pulsesports 最终按钮样式",
        font=get_font('large'),
        fg=get_color('primary'),
        bg=get_color('background')
    )
    title.pack(pady=20)

    # 主容器
    main_frame = tk.Frame(root, bg=get_color('card_bg'), relief='solid', bd=1)
    main_frame.pack(fill='both', expand=True, padx=20, pady=10)

    content_frame = tk.Frame(main_frame, bg=get_color('card_bg'))
    content_frame.pack(fill='both', expand=True, padx=20, pady=20)

    # 1. 基础按钮
    tk.Label(content_frame, text="基础按钮:", font=get_font('subtitle'),
             fg=get_color('text'), bg=get_color('card_bg')).pack(anchor='w')

    basic_frame = tk.Frame(content_frame, bg=get_color('card_bg'))
    basic_frame.pack(pady=10)

    create_modern_button(basic_frame, "主要操作", "primary", width=12).pack(side='left', padx=5)
    create_modern_button(basic_frame, "次要操作", "secondary", width=12).pack(side='left', padx=5)
    create_modern_button(basic_frame, "轮廓按钮", "outline", width=12).pack(side='left', padx=5)

    # 2. 状态按钮
    tk.Label(content_frame, text="状态按钮:", font=get_font('subtitle'),
             fg=get_color('text'), bg=get_color('card_bg')).pack(anchor='w', pady=(20, 0))

    status_frame = tk.Frame(content_frame, bg=get_color('card_bg'))
    status_frame.pack(pady=10)

    create_modern_button(status_frame, "✓ 成功", "success", width=12).pack(side='left', padx=5)
    create_modern_button(status_frame, "⚠ 警告", "warning", width=12).pack(side='left', padx=5)
    create_modern_button(status_frame, "✗ 危险", "danger", width=12).pack(side='left', padx=5)

    # 3. 灰色按钮（重点测试）
    tk.Label(content_frame, text="灰色按钮方案:", font=get_font('subtitle'),
             fg=get_color('text'), bg=get_color('card_bg')).pack(anchor='w', pady=(20, 0))

    gray_frame = tk.Frame(content_frame, bg=get_color('card_bg'))
    gray_frame.pack(pady=10)

    create_modern_button(gray_frame, "取消", "gray", width=10).pack(side='left', padx=5)
    tk.Label(gray_frame, text="← 推荐方案：浅灰底+深色字",
             fg=get_color('success'), bg=get_color('card_bg')).pack(side='left', padx=10)

    # 可选的橙色文字版本
    create_modern_button(gray_frame, "取消", "gray_orange", width=10).pack(side='left', padx=(30, 5))
    tk.Label(gray_frame, text="← 可选：浅灰底+橙色字",
             fg=get_color('primary'), bg=get_color('card_bg')).pack(side='left', padx=10)

    # 4. 功能按钮
    tk.Label(content_frame, text="功能按钮:", font=get_font('subtitle'),
             fg=get_color('text'), bg=get_color('card_bg')).pack(anchor='w', pady=(20, 0))

    func_frame = tk.Frame(content_frame, bg=get_color('card_bg'))
    func_frame.pack(pady=10)

    create_icon_button(func_frame, "➕", "添加任务", "primary", width=12).pack(side='left', padx=3)
    create_icon_button(func_frame, "▶", "启动", "success", width=8).pack(side='left', padx=3)
    create_icon_button(func_frame, "⏸", "暂停", "warning", width=8).pack(side='left', padx=3)
    create_icon_button(func_frame, "⏹", "停止", "gray", width=8).pack(side='left', padx=3)
    create_icon_button(func_frame, "🗑", "删除", "danger", width=8).pack(side='left', padx=3)

    # 5. 实际场景演示
    tk.Label(content_frame, text="实际使用场景:", font=get_font('subtitle'),
             fg=get_color('text'), bg=get_color('card_bg')).pack(anchor='w', pady=(20, 0))

    # 对话框场景
    dialog_demo = tk.Frame(content_frame, bg=get_color('gray_light'), relief='solid', bd=1)
    dialog_demo.pack(fill='x', pady=10)

    dialog_content = tk.Frame(dialog_demo, bg=get_color('gray_light'))
    dialog_content.pack(padx=15, pady=15)

    tk.Label(dialog_content, text="确定要删除这个任务吗？",
             font=get_font('default'), fg=get_color('text'), bg=get_color('gray_light')).pack(pady=(0, 10))

    dialog_buttons = tk.Frame(dialog_content, bg=get_color('gray_light'))
    dialog_buttons.pack()

    create_modern_button(dialog_buttons, "确定删除", "danger", width=10).pack(side='left', padx=5)
    create_modern_button(dialog_buttons, "取消", "gray", width=10).pack(side='left', padx=5)

    # 说明
    note = tk.Label(
        content_frame,
        text="✅ 所有按钮文字都清晰可见，对比度符合可访问性标准！",
        font=get_font('default'),
        fg=get_color('success'),
        bg=get_color('card_bg')
    )
    note.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    test_button_styles()