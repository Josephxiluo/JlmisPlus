"""
优化后的样式配置模块 - 现代化视觉设计
"""

# 现代化橙色主题配置
ORANGE_THEME = {
    'colors': {
        'primary': '#FF7043',      # 现代橙色
        'primary_dark': '#E64A19', # 深橙色
        'primary_light': '#FFCCBC', # 浅橙色
        'primary_hover': '#FF5722', # 悬停橙色
        'background': '#FAFAFA',   # 温和背景色
        'card_bg': '#FFFFFF',      # 卡片背景
        'white': '#FFFFFF',
        'text': '#212121',         # 深文字色
        'text_light': '#757575',   # 次级文字色
        'text_hint': '#BDBDBD',    # 提示文字色
        'border': '#E0E0E0',       # 边框色
        'border_light': '#F5F5F5', # 浅边框色
        'success': '#4CAF50',      # Material Design绿色
        'warning': '#FF9800',      # Material Design橙色
        'danger': '#F44336',       # Material Design红色
        'info': '#2196F3',         # Material Design蓝色
        'gray': '#9E9E9E',
        'gray_light': '#EEEEEE',
        'gray_dark': '#616161',
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
    """创建现代化按钮"""
    import tkinter as tk

    # 按钮样式配置
    styles = {
        'primary': {
            'bg': get_color('primary'),
            'fg': 'white',
            'active_bg': get_color('primary_dark'),
            'hover_bg': get_color('primary_hover')
        },
        'secondary': {
            'bg': get_color('gray_light'),
            'fg': get_color('text'),
            'active_bg': get_color('border'),
            'hover_bg': get_color('border')
        },
        'success': {
            'bg': get_color('success'),
            'fg': 'white',
            'active_bg': '#388E3C',
            'hover_bg': '#45A049'
        },
        'danger': {
            'bg': get_color('danger'),
            'fg': 'white',
            'active_bg': '#D32F2F',
            'hover_bg': '#E53935'
        },
        'warning': {
            'bg': get_color('warning'),
            'fg': 'white',
            'active_bg': '#F57C00',
            'hover_bg': '#FB8C00'
        },
        'gray': {
            'bg': get_color('gray'),
            'fg': 'white',
            'active_bg': get_color('gray_dark'),
            'hover_bg': '#757575'
        }
    }

    button_style = styles.get(style, styles['primary'])

    button = tk.Button(
        parent,
        text=text,
        font=get_font('button'),
        bg=button_style['bg'],
        fg=button_style['fg'],
        relief='flat',
        bd=0,
        cursor='hand2',
        command=command,
        **kwargs
    )

    if width:
        button.config(width=width)

    # 添加悬停效果
    def on_enter(event):
        button.config(bg=button_style['hover_bg'])

    def on_leave(event):
        button.config(bg=button_style['bg'])

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
    import tkinter as tk

    # 主容器
    card_container = tk.Frame(
        parent,
        bg=get_color('background'),
        **kwargs
    )

    # 卡片框架（带阴影效果）
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
            fg=get_color('text'),
            bg=get_color('primary_light')
        )
        title_label.pack(side='left', padx=get_spacing('md'), pady=get_spacing('sm'))

        # 内容区域
        content_frame = tk.Frame(card_frame, bg=get_color('card_bg'))
        content_frame.pack(fill='both', expand=True, padx=get_spacing('sm'), pady=get_spacing('sm'))

        return card_container, content_frame

    return card_container, card_frame

def create_status_badge(parent, text, status_type="info"):
    """创建状态徽章"""
    import tkinter as tk

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
        fg=color['fg'],
        padx=8,
        pady=2
    )

    return badge