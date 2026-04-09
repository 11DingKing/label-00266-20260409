"""
现代简洁风格样式表
"""

# 颜色定义
COLORS = {
    "primary": "#2563EB",        # 主色调蓝
    "primary_hover": "#1D4ED8",
    "primary_light": "#EFF6FF",
    "success": "#10B981",
    "warning": "#F59E0B", 
    "danger": "#EF4444",
    "text": "#1F2937",
    "text_secondary": "#6B7280",
    "text_muted": "#9CA3AF",
    "border": "#E5E7EB",
    "border_focus": "#2563EB",
    "bg": "#FFFFFF",
    "bg_secondary": "#F9FAFB",
    "bg_hover": "#F3F4F6",
}

STYLESHEET = """
/* 全局样式 */
* {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

QWidget {
    font-size: 14px;
    color: #1F2937;
}

QMainWindow {
    background-color: #F9FAFB;
}

QMainWindow > QWidget {
    background-color: #F9FAFB;
}

/* 标签始终透明 */
QLabel {
    background: transparent;
    background-color: transparent;
    border: none;
}

/* QFrame 内的标签 */
QFrame QLabel {
    background: transparent;
    background-color: transparent;
    border: none;
}

/* 卡片内的标签 */
CardWithTitle QLabel, Card QLabel {
    background: transparent;
    border: none;
}

/* 滚动区域 */
QScrollArea {
    border: none;
    background-color: #F9FAFB;
}

QScrollArea QWidget {
    background-color: transparent;
}

QScrollArea > QWidget > QWidget {
    background-color: #F9FAFB;
}

QScrollBar:vertical {
    background: #F3F4F6;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #D1D5DB;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #9CA3AF;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* 输入框 */
QLineEdit, QTextEdit, QPlainTextEdit {
    padding: 10px 14px;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    background-color: #FFFFFF;
    color: #1F2937;
    font-size: 14px;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
    outline: none;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #2563EB;
    outline: none;
}

QLineEdit:disabled, QTextEdit:disabled {
    background-color: #F3F4F6;
    color: #9CA3AF;
}

/* 数字输入框 - 隐藏原生按钮，使用自定义组件 */
QSpinBox, QDoubleSpinBox {
    padding: 8px 12px;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    background-color: #FFFFFF;
    color: #1F2937;
    font-size: 14px;
    min-width: 60px;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #2563EB;
}

QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: #D1D5DB;
}

QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    width: 0;
    height: 0;
    border: none;
    background: transparent;
}

QSpinBox::up-arrow, QSpinBox::down-arrow,
QDoubleSpinBox::up-arrow, QDoubleSpinBox::down-arrow {
    width: 0;
    height: 0;
    border: none;
    background: transparent;
}

QSpinBox:disabled, QDoubleSpinBox:disabled {
    background-color: #F3F4F6;
    color: #9CA3AF;
}

/* 下拉框 */
QComboBox {
    padding: 8px 14px;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    background-color: #FFFFFF;
    color: #1F2937;
    font-size: 14px;
    min-width: 120px;
}

QComboBox:focus {
    border-color: #2563EB;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #6B7280;
}

QComboBox QAbstractItemView {
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    background-color: #FFFFFF;
    selection-background-color: #EFF6FF;
    selection-color: #2563EB;
    padding: 4px;
}

/* 按钮 */
QPushButton {
    padding: 10px 20px;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    background-color: #FFFFFF;
    color: #1F2937;
    font-size: 14px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #F3F4F6;
    border-color: #D1D5DB;
}

QPushButton:pressed {
    background-color: #E5E7EB;
}

QPushButton:disabled {
    background-color: #F3F4F6;
    color: #9CA3AF;
    border-color: #E5E7EB;
}

/* 主要按钮 */
QPushButton[class="primary"] {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
}

QPushButton[class="primary"]:hover {
    background-color: #1D4ED8;
}

QPushButton[class="primary"]:pressed {
    background-color: #1E40AF;
}

/* 危险按钮 */
QPushButton[class="danger"] {
    background-color: #EF4444;
    color: #FFFFFF;
    border: none;
}

QPushButton[class="danger"]:hover {
    background-color: #DC2626;
}

/* 表格 */
QTableWidget {
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    background-color: #FFFFFF;
    gridline-color: #F3F4F6;
    color: #1F2937;
}

QTableWidget::item {
    padding: 12px 16px;
    border-bottom: 1px solid #F3F4F6;
    color: #1F2937;
}

QTableWidget::item:selected {
    background-color: #EFF6FF;
    color: #2563EB;
}

QHeaderView::section {
    background-color: #F9FAFB;
    color: #6B7280;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    padding: 12px 16px;
    border: none;
    border-bottom: 1px solid #E5E7EB;
}

/* 复选框 */
QCheckBox {
    spacing: 8px;
    color: #1F2937;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #D1D5DB;
    border-radius: 4px;
    background-color: #FFFFFF;
}

QCheckBox::indicator:checked {
    background-color: #2563EB;
    border-color: #2563EB;
}

/* 标签页 */
QTabWidget::pane {
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    background-color: #FFFFFF;
}

QTabBar::tab {
    padding: 12px 24px;
    margin-right: 4px;
    border: none;
    background-color: transparent;
    color: #6B7280;
    font-weight: 500;
}

QTabBar::tab:selected {
    color: #2563EB;
    border-bottom: 2px solid #2563EB;
}

QTabBar::tab:hover:!selected {
    color: #1F2937;
}

/* 进度条 */
QProgressBar {
    border: none;
    border-radius: 4px;
    background-color: #E5E7EB;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #2563EB;
    border-radius: 4px;
}

/* 分组框 */
QGroupBox {
    font-weight: 600;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    background-color: #FFFFFF;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: #1F2937;
}

/* 工具提示 */
QToolTip {
    background-color: #1F2937;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}

/* 菜单 */
QMenu {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 8px;
}

QMenu::item {
    padding: 8px 16px;
    border-radius: 4px;
    color: #1F2937;
}

QMenu::item:selected {
    background-color: #EFF6FF;
    color: #2563EB;
}

/* 分割线 */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    background-color: #E5E7EB;
}
"""
