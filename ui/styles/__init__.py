"""
样式配置模块
"""

# 橙色主题配置
ORANGE_THEME = {
    'colors': {
        'primary': '#FF7F50',      # 主橙色
        'primary_dark': '#FF6347', # 深橙色
        'primary_light': '#FFE4B5', # 浅橙色
        'background': '#F5F5F5',   # 背景色
        'white': '#FFFFFF',        # 白色
        'text': '#333333',         # 文字色
        'text_light': '#666666',   # 浅文字色
        'border': '#DDDDDD',       # 边框色
        'success': '#32CD32',      # 成功色
        'warning': '#FFD700',      # 警告色
        'danger': '#DC143C',       # 危险色
        'gray': '#999999',         # 灰色
        'grid_line': '#E0E0E0',    # 网格线色
    },
    'fonts': {
        'default': ('Microsoft YaHei', 9),
        'title': ('Microsoft YaHei', 12, 'bold'),
        'button': ('Microsoft YaHei', 9, 'bold'),
        'small': ('Microsoft YaHei', 8),
    }
}

def get_color(name):
    """获取颜色值"""
    return ORANGE_THEME['colors'].get(name, '#000000')

def get_font(name):
    """获取字体配置"""
    return ORANGE_THEME['fonts'].get(name, ('Microsoft YaHei', 9))