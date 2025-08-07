"""
修复版CustomTkinter现代化样式配置 - 橙色主题
"""
import customtkinter as ctk
from typing import Dict, Any

# 设置 CustomTkinter 外观模式（使用内置主题）
ctk.set_appearance_mode("light")  # 亮色模式
ctk.set_default_color_theme("blue")  # 使用蓝色主题作为基础

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
        'text_hint': '#9E9E9E',    # 提示文字色
        'border': '#E0E0E0',       # 边框色
        'border_light': '#F5F5F5', # 浅边框色
        'success': '#4CAF50',      # 绿色
        'warning': '#FF9800',      # 橙色
        'danger': '#F44336',       # 红色
        'info': '#2196F3',         # 蓝色
        'gray': '#757575',         # 中灰色
        'gray_light': '#EEEEEE',   # 浅灰色
        'gray_dark': '#424242',    # 深灰色
        'shadow': '#E0E0E0',       # 阴影色
        'hover_bg': '#FFF3E0',     # 悬停背景
        'selected': '#FFE0B2',     # 选中背景
    },
    'fonts': {
        'default': ('Microsoft YaHei', 12),
        'title': ('Microsoft YaHei', 18, 'bold'),
        'subtitle': ('Microsoft YaHei', 14, 'bold'),
        'button': ('Microsoft YaHei', 12, 'bold'),
        'large': ('Microsoft YaHei', 20, 'bold'),
        'medium': ('Microsoft YaHei', 14),
        'small': ('Microsoft YaHei', 10),
    },
    'spacing': {
        'xs': 4,    # 小间距
        'sm': 8,    # 标准间距
        'md': 16,   # 中等间距
        'lg': 24,   # 大间距
        'xl': 32    # 特大间距
    }
}

def get_color(name: str) -> str:
    """获取颜色值"""
    return ORANGE_THEME['colors'].get(name, '#000000')

def get_font(name: str):
    """获取字体配置"""
    return ORANGE_THEME['fonts'].get(name, ('Microsoft YaHei', 12))

def get_spacing(name: str) -> int:
    """获取间距值"""
    return ORANGE_THEME['spacing'].get(name, 8)

def create_modern_button(parent, text: str, style: str = "primary", command=None, width: int = None, **kwargs):
    """创建现代化 CustomTkinter 按钮"""

    # 按钮颜色配置
    color_configs = {
        'primary': {
            'fg_color': get_color('primary'),
            'hover_color': get_color('primary_hover'),
            'text_color': 'white',
        },
        'secondary': {
            'fg_color': 'transparent',
            'hover_color': get_color('hover_bg'),
            'text_color': get_color('text'),
            'border_color': get_color('border'),
            'border_width': 2,
        },
        'success': {
            'fg_color': get_color('success'),
            'hover_color': '#45A049',
            'text_color': 'white',
        },
        'danger': {
            'fg_color': get_color('danger'),
            'hover_color': '#E53935',
            'text_color': 'white',
        },
        'warning': {
            'fg_color': get_color('warning'),
            'hover_color': '#FB8C00',
            'text_color': 'white',
        },
        'gray': {
            'fg_color': get_color('gray_light'),
            'hover_color': '#E0E0E0',
            'text_color': get_color('text'),
        },
    }

    config = color_configs.get(style, color_configs['primary'])

    button = ctk.CTkButton(
        parent,
        text=text,
        command=command,
        font=get_font('button'),
        width=width or 120,
        height=28,
        corner_radius=8,
        **config,
        **kwargs
    )

    return button

def create_card_frame(parent, title: str = None, **kwargs):
    """创建现代化卡片框架"""
    # 主容器
    card_container = ctk.CTkFrame(
        parent,
        fg_color='transparent',
        **kwargs
    )

    # 卡片框架
    card_frame = ctk.CTkFrame(
        card_container,
        fg_color=get_color('card_bg'),
        corner_radius=12,
        border_width=1,
        border_color=get_color('border_light')
    )
    card_frame.pack(fill='both', expand=True, padx=4, pady=4)

    if title:
        # 标题头部
        header_frame = ctk.CTkFrame(
            card_frame,
            fg_color=get_color('primary_light'),
            corner_radius=8,
            height=45
        )
        header_frame.pack(fill='x', padx=8, pady=(8, 4))
        header_frame.pack_propagate(False)

        title_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=get_font('title'),
            text_color=get_color('text')
        )
        title_label.pack(side='left', padx=get_spacing('md'), pady=get_spacing('sm'))

        # 内容区域
        content_frame = ctk.CTkFrame(
            card_frame,
            fg_color='transparent'
        )
        content_frame.pack(fill='both', expand=True, padx=8, pady=(4, 8))

        return card_container, content_frame

    return card_container, card_frame

def create_scrollable_frame(parent, **kwargs):
    """创建可滚动框架"""
    scrollable_frame = ctk.CTkScrollableFrame(
        parent,
        fg_color=get_color('card_bg'),
        corner_radius=8,
        **kwargs
    )
    return scrollable_frame

def create_entry(parent, placeholder: str = "", **kwargs):
    """创建现代化输入框"""
    # 过滤掉不支持的参数
    supported_kwargs = {}
    for key, value in kwargs.items():
        if key not in ['textvariable']:  # textvariable需要特殊处理
            supported_kwargs[key] = value

    entry = ctk.CTkEntry(
        parent,
        placeholder_text=placeholder,
        font=get_font('default'),
        corner_radius=8,
        border_width=2,
        border_color=get_color('border'),
        fg_color=get_color('white'),
        text_color=get_color('text'),
        placeholder_text_color=get_color('text_hint'),
        **supported_kwargs
    )

    # 手动处理textvariable
    if 'textvariable' in kwargs:
        entry.configure(textvariable=kwargs['textvariable'])

    return entry

def create_textbox(parent, **kwargs):
    """创建现代化文本框"""
    textbox = ctk.CTkTextbox(
        parent,
        font=get_font('default'),
        corner_radius=8,
        border_width=2,
        border_color=get_color('border'),
        fg_color=get_color('white'),
        text_color=get_color('text'),
        **kwargs
    )
    return textbox

def create_combobox(parent, values: list, **kwargs):
    """创建现代化下拉框"""
    combobox = ctk.CTkComboBox(
        parent,
        values=values,
        font=get_font('default'),
        corner_radius=8,
        border_width=2,
        border_color=get_color('border'),
        fg_color=get_color('white'),
        text_color=get_color('text'),
        dropdown_fg_color=get_color('card_bg'),
        dropdown_text_color=get_color('text'),
        dropdown_hover_color=get_color('primary_light'),
        button_color=get_color('primary'),
        button_hover_color=get_color('primary_hover'),
        **kwargs
    )
    return combobox

def create_label(parent, text: str, style: str = "default", **kwargs):
    """创建现代化标签"""
    font_styles = {
        'default': get_font('default'),
        'title': get_font('title'),
        'subtitle': get_font('subtitle'),
        'small': get_font('small'),
        'medium': get_font('medium'),
        'large': get_font('large'),
    }

    text_colors = {
        'default': get_color('text'),
        'light': get_color('text_light'),
        'hint': get_color('text_hint'),
        'primary': get_color('primary'),
        'success': get_color('success'),
        'warning': get_color('warning'),
        'danger': get_color('danger'),
    }

    color = text_colors.get(style, text_colors['default'])
    font = font_styles.get(style, font_styles['default'])

    label = ctk.CTkLabel(
        parent,
        text=text,
        font=font,
        text_color=color,
        **kwargs
    )
    return label

def create_checkbox(parent, text: str, **kwargs):
    """创建现代化复选框"""
    checkbox = ctk.CTkCheckBox(
        parent,
        text=text,
        width = 18,
        height = 18,
        font=get_font('default'),
        text_color=get_color('text'),
        fg_color=get_color('primary'),
        hover_color=get_color('primary_hover'),
        checkmark_color='white',
        corner_radius=4,
        **kwargs
    )
    return checkbox

def create_progress_bar(parent, **kwargs):
    """创建现代化进度条"""
    progress = ctk.CTkProgressBar(
        parent,
        corner_radius=8,
        height=8,
        progress_color=get_color('primary'),
        fg_color=get_color('gray_light'),
        **kwargs
    )
    return progress

def create_status_badge(parent, text: str, status_type: str = "info", **kwargs):
    """创建状态徽章"""
    colors = {
        'success': get_color('success'),
        'warning': get_color('warning'),
        'danger': get_color('danger'),
        'info': get_color('info'),
        'gray': get_color('gray'),
        'primary': get_color('primary')
    }

    color = colors.get(status_type, colors['info'])

    badge = ctk.CTkLabel(
        parent,
        text=text,
        font=get_font('small'),
        text_color='white',
        fg_color=color,
        corner_radius=8,
        width=60,
        height=22,
        **kwargs
    )
    return badge

def create_switch(parent, text: str = "", **kwargs):
    """创建现代化开关"""
    switch = ctk.CTkSwitch(
        parent,
        text=text,
        font=get_font('default'),
        text_color=get_color('text'),
        fg_color=get_color('gray_light'),
        progress_color=get_color('primary'),
        button_color='white',
        button_hover_color=get_color('gray_light'),
        **kwargs
    )
    return switch

def create_tabview(parent, **kwargs):
    """创建现代化标签页"""
    tabview = ctk.CTkTabview(
        parent,
        corner_radius=8,
        border_width=2,
        border_color=get_color('border'),
        fg_color=get_color('card_bg'),
        segmented_button_fg_color=get_color('gray_light'),
        segmented_button_selected_color=get_color('primary'),
        segmented_button_selected_hover_color=get_color('primary_hover'),
        segmented_button_unselected_color=get_color('gray_light'),
        segmented_button_unselected_hover_color=get_color('hover_bg'),
        text_color=get_color('text'),
        text_color_disabled=get_color('text_hint'),
        **kwargs
    )
    return tabview

def create_toplevel(title: str = "对话框"):
    """创建现代化顶层窗口"""
    window = ctk.CTkToplevel()
    window.title(title)
    window.geometry("400x300")

    # 设置窗口样式
    window.configure(fg_color=get_color('background'))

    return window

# 为了兼容原有代码，添加一些旧版本的函数
def create_shadow_frame(parent, **kwargs):
    """创建带阴影效果的框架 - 兼容函数"""
    return create_card_frame(parent, **kwargs)

if __name__ == "__main__":
    # 测试现代化组件
    root = ctk.CTk()
    root.title("CustomTkinter 现代化组件测试")
    root.geometry("800x600")
    root.configure(fg_color=get_color('background'))

    # 创建主容器
    main_frame = ctk.CTkFrame(root, fg_color='transparent')
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)

    # 标题
    title_label = create_label(main_frame, "现代化UI组件测试", "title")
    title_label.pack(pady=(0, 20))

    # 按钮测试
    button_frame = ctk.CTkFrame(main_frame, fg_color='transparent')
    button_frame.pack(fill='x', pady=10)

    create_modern_button(button_frame, "主要按钮", "primary").pack(side='left', padx=5)
    create_modern_button(button_frame, "成功按钮", "success").pack(side='left', padx=5)
    create_modern_button(button_frame, "危险按钮", "danger").pack(side='left', padx=5)
    create_modern_button(button_frame, "警告按钮", "warning").pack(side='left', padx=5)

    # 输入框测试
    input_frame = ctk.CTkFrame(main_frame, fg_color='transparent')
    input_frame.pack(fill='x', pady=10)

    entry = create_entry(input_frame, "请输入内容...", width=200)
    entry.pack(side='left', padx=5)

    combobox = create_combobox(input_frame, ["选项1", "选项2", "选项3"], width=150)
    combobox.pack(side='left', padx=5)

    # 卡片测试
    card_container, card_content = create_card_frame(main_frame, "测试卡片")
    card_container.pack(fill='both', expand=True, pady=10)

    create_label(card_content, "这是卡片内容", "default").pack(pady=10)
    create_progress_bar(card_content).pack(fill='x', pady=5)

    root.mainloop()