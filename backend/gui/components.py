"""
自定义组件
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QSpinBox, QDoubleSpinBox, QComboBox,
    QStyledItemDelegate, QStyle, QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPainter, QColor, QPen, QPolygon, QPainterPath
from PySide6.QtCore import QPoint, QRect

from gui.styles import COLORS


def confirm_dialog(parent, title, message):
    """显示中文确认对话框，返回 True 表示确认"""
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setIcon(QMessageBox.Question)
    
    yes_btn = msg_box.addButton("确定", QMessageBox.YesRole)
    no_btn = msg_box.addButton("取消", QMessageBox.NoRole)
    msg_box.setDefaultButton(no_btn)
    
    msg_box.exec()
    return msg_box.clickedButton() == yes_btn


class StyledComboBox(QComboBox):
    """自定义下拉框，带正确显示的箭头"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QComboBox {
                padding: 8px 28px 8px 12px;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background-color: #FFFFFF;
                color: #1F2937;
                font-size: 14px;
                min-width: 80px;
            }
            QComboBox:hover {
                border-color: #D1D5DB;
            }
            QComboBox:focus {
                border-color: #2563EB;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border: none;
                background: transparent;
            }
            QComboBox::down-arrow {
                width: 0;
                height: 0;
                background: none;
                border: none;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background-color: #FFFFFF;
                selection-background-color: #EFF6FF;
                selection-color: #2563EB;
                padding: 4px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                min-height: 24px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #F3F4F6;
            }
        """)
        
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制箭头区域
        arrow_rect = QRect(self.width() - 24, 0, 20, self.height())
        
        # 使用字体绘制向下箭头符号
        painter.setPen(QColor("#6B7280"))
        font = painter.font()
        font.setPixelSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(arrow_rect, Qt.AlignCenter, "▼")
        
        painter.end()


class StyledLineEdit(QLineEdit):
    """自定义输入框，确保样式正确显示"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background-color: #FFFFFF;
                color: #1F2937;
                font-size: 14px;
                selection-background-color: #2563EB;
                selection-color: #FFFFFF;
            }
            QLineEdit:hover {
                border-color: #D1D5DB;
            }
            QLineEdit:focus {
                border-color: #2563EB;
            }
            QLineEdit:disabled {
                background-color: #F3F4F6;
                color: #9CA3AF;
            }
        """)


class StyledCheckBox(QWidget):
    """自定义复选框，带正确显示的对勾"""
    toggled = Signal(bool)
    
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self._checked = False
        self._text = text
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 复选框按钮
        self.check_btn = CheckBoxButton()
        self.check_btn.setFixedSize(22, 22)
        self.check_btn.setCursor(Qt.PointingHandCursor)
        self.check_btn.clicked.connect(self._toggle)
        layout.addWidget(self.check_btn)
        
        # 文本标签
        if text:
            label = QLabel(text)
            label.setStyleSheet("color: #1F2937; font-size: 14px;")
            layout.addWidget(label)
    
    def _toggle(self):
        self._checked = not self._checked
        self.check_btn.setChecked(self._checked)
        self.toggled.emit(self._checked)
    
    def isChecked(self):
        return self._checked
    
    def setChecked(self, checked):
        self._checked = checked
        self.check_btn.setChecked(checked)


class CheckBoxButton(QPushButton):
    """自定义复选框按钮，使用QPainter绘制对勾"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #D1D5DB;
                border-radius: 4px;
            }
            QPushButton:hover {
                border-color: #2563EB;
            }
        """)
    
    def setChecked(self, checked):
        self._checked = checked
        if checked:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2563EB;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #1D4ED8;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    border: 2px solid #D1D5DB;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    border-color: #2563EB;
                }
            """)
        self.update()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        if self._checked:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 绘制白色对勾
            pen = QPen(QColor("#FFFFFF"), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            
            # 对勾路径
            w, h = self.width(), self.height()
            painter.drawLine(int(w * 0.25), int(h * 0.5), int(w * 0.45), int(h * 0.7))
            painter.drawLine(int(w * 0.45), int(h * 0.7), int(w * 0.75), int(h * 0.3))
            
            painter.end()


class StyledSpinBox(QWidget):
    """带自定义加减按钮的数字输入框"""
    valueChanged = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._min = 0
        self._max = 100
        self._value = 0
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 减号按钮
        self.minus_btn = QPushButton()
        self.minus_btn.setText("-")
        self.minus_btn.setObjectName("spinMinus")
        self.minus_btn.setFixedSize(36, 36)
        self.minus_btn.setCursor(Qt.PointingHandCursor)
        self.minus_btn.setStyleSheet("""
            #spinMinus {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-right: none;
                border-top-left-radius: 8px;
                border-bottom-left-radius: 8px;
                font-size: 20px;
                font-weight: bold;
                color: #6B7280;
                padding: 0;
                padding-bottom: 3px;
            }
            #spinMinus:hover {
                background-color: #EFF6FF;
                color: #2563EB;
            }
            #spinMinus:pressed {
                background-color: #DBEAFE;
            }
        """)
        self.minus_btn.clicked.connect(self._decrease)
        layout.addWidget(self.minus_btn)
        
        # 数字输入框
        self.spin = QSpinBox()
        self.spin.setObjectName("spinInput")
        self.spin.setButtonSymbols(QSpinBox.NoButtons)
        self.spin.setAlignment(Qt.AlignCenter)
        self.spin.setFixedHeight(36)
        self.spin.setStyleSheet("""
            #spinInput {
                border: 1px solid #E5E7EB;
                border-left: none;
                border-right: none;
                border-radius: 0;
                background-color: #FFFFFF;
                color: #1F2937;
                font-size: 14px;
                font-weight: 500;
                padding: 0 8px;
                min-width: 50px;
            }
            #spinInput:focus {
                border-color: #2563EB;
            }
        """)
        self.spin.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.spin)
        
        # 加号按钮
        self.plus_btn = QPushButton()
        self.plus_btn.setText("+")
        self.plus_btn.setObjectName("spinPlus")
        self.plus_btn.setFixedSize(36, 36)
        self.plus_btn.setCursor(Qt.PointingHandCursor)
        self.plus_btn.setStyleSheet("""
            #spinPlus {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-left: none;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                font-size: 20px;
                font-weight: bold;
                color: #6B7280;
                padding: 0;
                padding-bottom: 3px;
            }
            #spinPlus:hover {
                background-color: #EFF6FF;
                color: #2563EB;
            }
            #spinPlus:pressed {
                background-color: #DBEAFE;
            }
        """)
        self.plus_btn.clicked.connect(self._increase)
        layout.addWidget(self.plus_btn)
    
    def _decrease(self):
        self.spin.setValue(self.spin.value() - 1)
    
    def _increase(self):
        self.spin.setValue(self.spin.value() + 1)
    
    def _on_value_changed(self, val):
        self._value = val
        self.valueChanged.emit(val)
    
    def setRange(self, min_val, max_val):
        self._min = min_val
        self._max = max_val
        self.spin.setRange(min_val, max_val)
    
    def setValue(self, val):
        self._value = val
        self.spin.setValue(val)
    
    def value(self):
        return self.spin.value()
    
    def setFixedWidth(self, width):
        # 调整内部组件宽度
        btn_width = 36
        spin_width = width - btn_width * 2
        self.spin.setFixedWidth(max(spin_width, 40))


class Card(QFrame):
    """卡片组件"""
    _card_id = 0
    
    def __init__(self, parent=None):
        super().__init__(parent)
        Card._card_id += 1
        obj_name = f"card_{Card._card_id}"
        self.setObjectName(obj_name)
        self.setStyleSheet(f"""
            #{obj_name} {{
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }}
            #{obj_name} QLabel {{
                background: transparent;
            }}
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 20, 24, 20)
        self.layout.setSpacing(16)


class CardWithTitle(QFrame):
    """带标题的卡片"""
    _card_id = 0
    
    def __init__(self, title, subtitle=None, parent=None):
        super().__init__(parent)
        CardWithTitle._card_id += 1
        obj_name = f"cardWithTitle_{CardWithTitle._card_id}"
        self.setObjectName(obj_name)
        self.setStyleSheet(f"""
            #{obj_name} {{
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }}
            #{obj_name} QLabel {{
                background: transparent;
            }}
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)
        
        # 标题区
        header = QVBoxLayout()
        header.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #1F2937;
        """)
        header.addWidget(title_label)
        
        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet("font-size: 13px; color: #6B7280;")
            header.addWidget(sub_label)
        
        main_layout.addLayout(header)
        
        # 内容区
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(12)
        main_layout.addLayout(self.content_layout)
    
    def addWidget(self, widget):
        self.content_layout.addWidget(widget)
    
    def addLayout(self, layout):
        self.content_layout.addLayout(layout)
    
    def addStretch(self):
        self.content_layout.addStretch()


class PrimaryButton(QPushButton):
    """主要按钮"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
            QPushButton:pressed {
                background-color: #1E40AF;
            }
            QPushButton:disabled {
                background-color: #93C5FD;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)


class SecondaryButton(QPushButton):
    """次要按钮"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #1F2937;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 10px 20px;
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
        """)
        self.setCursor(Qt.PointingHandCursor)


class DangerButton(QPushButton):
    """危险按钮"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #FEE2E2;
                color: #DC2626;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #FECACA;
            }
            QPushButton:pressed {
                background-color: #FCA5A5;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)


class LinkButton(QPushButton):
    """链接按钮"""
    def __init__(self, text, color="#2563EB", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {color};
                border: none;
                padding: 4px 6px;
                font-size: 13px;
                text-decoration: none;
                min-width: 32px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)


class PageTitle(QWidget):
    """页面标题组件"""
    def __init__(self, title, subtitle=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: 700;
            color: #1F2937;
        """)
        layout.addWidget(title_label)
        
        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet("font-size: 14px; color: #6B7280;")
            layout.addWidget(sub_label)


class FormRow(QWidget):
    """表单行"""
    def __init__(self, label, widget, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 14px; color: #374151;")
        label_widget.setFixedWidth(100)
        layout.addWidget(label_widget)
        
        layout.addWidget(widget, 1)


class Badge(QLabel):
    """徽章"""
    def __init__(self, text, color="primary", parent=None):
        super().__init__(text, parent)
        
        colors = {
            "primary": ("#EFF6FF", "#2563EB"),
            "success": ("#D1FAE5", "#059669"),
            "warning": ("#FEF3C7", "#D97706"),
            "danger": ("#FEE2E2", "#DC2626"),
            "gray": ("#F3F4F6", "#6B7280"),
        }
        
        bg, fg = colors.get(color, colors["gray"])
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
            }}
        """)
        self.setAlignment(Qt.AlignCenter)


class Divider(QFrame):
    """分割线"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setStyleSheet("background-color: #E5E7EB;")
        self.setFixedHeight(1)


class Pagination(QWidget):
    """分页组件"""
    pageChanged = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_page = 1
        self._total_pages = 1
        self._page_size = 20
        self._total_items = 0
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(8)
        
        # 左侧信息
        self.info_label = QLabel("共 0 条")
        self.info_label.setStyleSheet("color: #6B7280; font-size: 13px;")
        layout.addWidget(self.info_label)
        
        layout.addStretch()
        
        # 上一页
        self.prev_btn = QPushButton("上一页")
        self.prev_btn.setFixedHeight(32)
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 0 12px;
                color: #374151;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #F9FAFB;
                border-color: #D1D5DB;
            }
            QPushButton:disabled {
                color: #D1D5DB;
                background-color: #F9FAFB;
            }
        """)
        self.prev_btn.clicked.connect(self._prev_page)
        layout.addWidget(self.prev_btn)
        
        # 页码显示
        self.page_label = QLabel("1 / 1")
        self.page_label.setStyleSheet("color: #374151; font-size: 13px; min-width: 60px;")
        self.page_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.page_label)
        
        # 下一页
        self.next_btn = QPushButton("下一页")
        self.next_btn.setFixedHeight(32)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 0 12px;
                color: #374151;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #F9FAFB;
                border-color: #D1D5DB;
            }
            QPushButton:disabled {
                color: #D1D5DB;
                background-color: #F9FAFB;
            }
        """)
        self.next_btn.clicked.connect(self._next_page)
        layout.addWidget(self.next_btn)
    
    def _prev_page(self):
        if self._current_page > 1:
            self._current_page -= 1
            self._update_ui()
            self.pageChanged.emit(self._current_page)
    
    def _next_page(self):
        if self._current_page < self._total_pages:
            self._current_page += 1
            self._update_ui()
            self.pageChanged.emit(self._current_page)
    
    def _update_ui(self):
        self.page_label.setText(f"{self._current_page} / {self._total_pages}")
        self.info_label.setText(f"共 {self._total_items} 条")
        self.prev_btn.setEnabled(self._current_page > 1)
        self.next_btn.setEnabled(self._current_page < self._total_pages)
    
    def setPageInfo(self, total_items, page_size=20, current_page=1):
        """设置分页信息"""
        self._total_items = total_items
        self._page_size = page_size
        self._current_page = current_page
        self._total_pages = max(1, (total_items + page_size - 1) // page_size)
        self._update_ui()
    
    def currentPage(self):
        return self._current_page
    
    def pageSize(self):
        return self._page_size


class Toast(QWidget):
    """Toast 提示组件 - 现代简洁风格"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 主容器
        self.container = QFrame(self)
        self.container.setObjectName("toastContainer")
        
        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(16, 12, 20, 12)
        layout.setSpacing(10)
        
        # 图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(18, 18)
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)
        
        # 消息文本
        self.msg_label = QLabel()
        self.msg_label.setObjectName("toastMsg")
        layout.addWidget(self.msg_label)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)
        
        self._timer = None
    
    def show_message(self, message, msg_type="success", duration=2000):
        """显示提示消息"""
        styles = {
            "success": {
                "bg": "#ECFDF5",
                "border": "#A7F3D0",
                "text": "#065F46",
                "icon": "✓",
                "icon_bg": "#10B981"
            },
            "error": {
                "bg": "#FEF2F2",
                "border": "#FECACA",
                "text": "#991B1B",
                "icon": "✕",
                "icon_bg": "#EF4444"
            },
            "warning": {
                "bg": "#FFFBEB",
                "border": "#FDE68A",
                "text": "#92400E",
                "icon": "!",
                "icon_bg": "#F59E0B"
            },
            "info": {
                "bg": "#EFF6FF",
                "border": "#BFDBFE",
                "text": "#1E40AF",
                "icon": "i",
                "icon_bg": "#3B82F6"
            }
        }
        
        s = styles.get(msg_type, styles["info"])
        
        self.container.setStyleSheet(f"""
            #toastContainer {{
                background-color: {s['bg']};
                border: 1px solid {s['border']};
                border-radius: 10px;
            }}
        """)
        
        self.icon_label.setText(s['icon'])
        self.icon_label.setStyleSheet(f"""
            background-color: {s['icon_bg']};
            color: #FFFFFF;
            font-size: 11px;
            font-weight: bold;
            border-radius: 9px;
        """)
        
        self.msg_label.setText(message)
        self.msg_label.setStyleSheet(f"""
            color: {s['text']};
            font-size: 14px;
            font-weight: 500;
            background: transparent;
        """)
        
        # 调整大小
        self.adjustSize()
        self.container.adjustSize()
        
        # 定位到父窗口顶部中央
        if self.parent():
            parent = self.parent()
            while parent.parent():
                parent = parent.parent()
            x = parent.x() + (parent.width() - self.width()) // 2
            y = parent.y() + 80
            self.move(x, y)
        
        self.show()
        self.raise_()
        
        # 自动隐藏
        if self._timer:
            self._timer.stop()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)
        self._timer.start(duration)


class ToastManager:
    """Toast 管理器 - 单例模式"""
    _instance = None
    _toast = None
    
    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def show(cls, message, msg_type="success", parent=None):
        if cls._toast is None or not cls._toast.isVisible():
            cls._toast = Toast(parent)
        cls._toast.show_message(message, msg_type)
    
    @classmethod
    def success(cls, message, parent=None):
        cls.show(message, "success", parent)
    
    @classmethod
    def error(cls, message, parent=None):
        cls.show(message, "error", parent)
    
    @classmethod
    def warning(cls, message, parent=None):
        cls.show(message, "warning", parent)
    
    @classmethod
    def info(cls, message, parent=None):
        cls.show(message, "info", parent)
