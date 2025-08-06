"""
修复后的按钮样式配置 - 解决"添加任务"和"启动端口"按钮文字看不清的问题
"""
import tkinter as tk

# 现代化橙色主题配置 - 按钮样式修复版本
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
        'default': ('Microsoft YaHei', 10),      # 增大默认字体
        'title': ('Microsoft YaHei', 14, 'bold'),
        'subtitle': ('Microsoft YaHei', 12, 'bold'),
        'button': ('Microsoft YaHei', 10, 'bold'), # 增大按钮字体
        'small': ('Microsoft YaHei', 9),          # 增大小字体
        'large': ('Microsoft YaHei', 16, 'bold'),
        'medium': ('Microsoft YaHei', 11),        # 新增中等字体
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

def create_modern_button(parent, text, style="primary", command=None, width=None, **kwargs):
    """创建现代化按钮 - 重点修复primary和success按钮的文字显示问题"""

    # 修复后的按钮样式配置
    styles = {
        'primary': {
            'bg': get_color('primary'),           # 橙色背景 #FF7043
            'fg': '#FFFFFF',                      # 纯白色文字 - 确保高对比度 ✅
            'active_bg': get_color('primary_dark'),
            'hover_bg': get_color('primary_hover'),
            'border_color': get_color('primary_dark')
        },
        'secondary': {
            'bg': 'white',                        # 白色背景
            'fg': get_color('text'),              # 深色文字 #212121
            'active_bg': get_color('border'),
            'hover_bg': get_color('hover_bg'),
            'border_color': get_color('border')
        },
        'success': {
            'bg': get_color('success'),           # 绿色背景 #4CAF50
            'fg': '#FFFFFF',                      # 纯白色文字 - 确保高对比度 ✅
            'active_bg': '#388E3C',
            'hover_bg': '#45A049',
            'border_color': get_color('success')
        },
        'danger': {
            'bg': get_color('danger'),            # 红色背景
            'fg': '#FFFFFF',                      # 纯白色文字
            'active_bg': '#D32F2F',
            'hover_bg': '#E53935',
            'border_color': get_color('danger')
        },
        'warning': {
            'bg': get_color('warning'),           # 橙色背景
            'fg': '#FFFFFF',                      # 纯白色文字
            'active_bg': '#F57C00',
            'hover_bg': '#FB8C00',
            'border_color': get_color('warning')
        },
        'gray': {
            'bg': get_color('gray_light'),        # 浅灰背景 #EEEEEE
            'fg': '#000000',                      # 纯黑色文字，确保高对比度
            'active_bg': get_color('border'),
            'hover_bg': '#E0E0E0',
            'border_color': get_color('border')
        },
        'outline': {
            'bg': 'white',                        # 白色背景
            'fg': get_color('primary'),           # 橙色文字
            'active_bg': get_color('hover_bg'),
            'hover_bg': get_color('primary_light'),
            'border_color': get_color('primary')
        }
    }

    button_style = styles.get(style, styles['primary'])

    # 创建按钮 - 增加更明显的样式
    button = tk.Button(
        parent,
        text=text,
        font=('Microsoft YaHei', 11, 'bold'),  # 使用更大更粗的字体
        bg=button_style['bg'],
        fg=button_style['fg'],
        relief='solid',
        bd=2,  # 增加边框宽度
        cursor='hand2',
        command=command,
        highlightthickness=0,
        padx=16,  # 增加水平内边距
        pady=8,   # 增加垂直内边距
        **kwargs
    )

    if width:
        button.config(width=width)

    # 添加悬停效果 - 确保文字始终可见
    def on_enter(event):
        button.config(bg=button_style['hover_bg'])
        # 确保悬停时文字颜色正确
        if style in ['primary', 'success']:
            button.config(fg='#FFFFFF')  # 白色文字
        elif style == 'outline':
            button.config(fg='white')

    def on_leave(event):
        button.config(bg=button_style['bg'])
        # 恢复原文字颜色
        button.config(fg=button_style['fg'])

    def on_click(event):
        button.config(bg=button_style['active_bg'])

    def on_release(event):
        button.config(bg=button_style['hover_bg'])

    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
    button.bind("<Button-1>", on_click)
    button.bind("<ButtonRelease-1>", on_release)

    return button

# 其他函数保持不变...
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
        pady=2,
        relief='flat'
    )

    return badge

def create_icon_button(parent, icon, text, style="primary", command=None, **kwargs):
    """创建带图标的按钮"""
    display_text = f"{icon} {text}" if icon else text
    return create_modern_button(parent, display_text, style, command, **kwargs)

def create_resizable_paned_window(parent, orientation='horizontal'):
    """创建可调整大小的分割窗口"""
    paned_window = tk.PanedWindow(
        parent,
        orient=tk.HORIZONTAL if orientation == 'horizontal' else tk.VERTICAL,
        bg=get_color('background'),
        sashwidth=6,
        sashrelief='flat',
        showhandle=True,
        handlesize=8,
        handlepad=20,
        sashpad=2,
        relief='flat',
        bd=0
    )
    return paned_window

if __name__ == "__main__":
    # 测试修复后的按钮样式
    root = tk.Tk()
    root.title("按钮样式修复测试")
    root.geometry("700x400")
    root.configure(bg=get_color('background'))

    main_frame = tk.Frame(root, bg=get_color('card_bg'), relief='solid', bd=1)
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)

    tk.Label(main_frame, text="修复后的按钮样式:", font=get_font('subtitle'),
             fg=get_color('text'), bg=get_color('card_bg')).pack(pady=10)

    # 测试primary按钮（添加任务类型）
    primary_frame = tk.Frame(main_frame, bg=get_color('card_bg'))
    primary_frame.pack(pady=10)

    tk.Label(primary_frame, text="Primary按钮（添加任务类型）:", bg=get_color('card_bg')).pack()
    create_modern_button(primary_frame, "➕ 添加任务", "primary", width=12).pack(side='left', padx=5)
    create_modern_button(primary_frame, "⚙ 选项", "primary", width=8).pack(side='left', padx=5)

    # 测试success按钮（启动类型）
    success_frame = tk.Frame(main_frame, bg=get_color('card_bg'))
    success_frame.pack(pady=10)

    tk.Label(success_frame, text="Success按钮（启动类型）:", bg=get_color('card_bg')).pack()
    create_modern_button(success_frame, "▶ 启动端口", "success", width=12).pack(side='left', padx=5)
    create_modern_button(success_frame, "▶ 开始", "success", width=8).pack(side='left', padx=5)

    # 测试其他按钮样式
    other_frame = tk.Frame(main_frame, bg=get_color('card_bg'))
    other_frame.pack(pady=10)

    tk.Label(other_frame, text="其他按钮样式:", bg=get_color('card_bg')).pack()
    create_modern_button(other_frame, "⏹ 停止端口", "gray", width=12).pack(side='left', padx=5)
    create_modern_button(other_frame, "🗑 删除", "danger", width=8).pack(side='left', padx=5)
    create_modern_button(other_frame, "⚠ 警告", "warning", width=8).pack(side='left', padx=5)

    tk.Label(main_frame, text="✅ 修复要点:\n• Primary和Success按钮现在使用纯白色文字（#FFFFFF）\n• 增大了字体和按钮尺寸\n• 加粗了文字显示\n• 增加了边框宽度提高可见性",
             fg=get_color('success'), bg=get_color('card_bg'), justify='left').pack(pady=20)

    root.mainloop()