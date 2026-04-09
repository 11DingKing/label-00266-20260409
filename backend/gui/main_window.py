"""
AI文章自动生成系统 - 主窗口
现代简洁设计风格
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon

from gui.styles import STYLESHEET
from gui.tabs.articles_tab import ArticlesTab
from gui.tabs.keywords_tab import KeywordsTab
from gui.tabs.knowledge_base_tab import KnowledgeBaseTab
from gui.tabs.cms_tab import CMSTab
from gui.tabs.config_tab import ConfigTab
from gui.tabs.logs_tab import LogsTab
from gui.api_client import APIClient


class NavButton(QPushButton):
    """导航按钮"""
    def __init__(self, text, icon_char=None, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(44)
        self.update_style(False)
    
    def update_style(self, active):
        if active:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #EFF6FF;
                    color: #2563EB;
                    border: none;
                    border-radius: 8px;
                    padding: 0 16px;
                    font-size: 14px;
                    font-weight: 500;
                    text-align: left;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #6B7280;
                    border: none;
                    border-radius: 8px;
                    padding: 0 16px;
                    font-size: 14px;
                    font-weight: 500;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #F3F4F6;
                    color: #1F2937;
                }
            """)


class Sidebar(QFrame):
    """侧边栏"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self.setStyleSheet("""
            Sidebar {
                background-color: #FFFFFF;
                border-right: 1px solid #E5E7EB;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(4)
        
        # Logo
        logo = QLabel("AI 文章生成")
        logo.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #1F2937;
            padding: 8px 16px 24px 16px;
        """)
        layout.addWidget(logo)
        
        # 导航按钮
        self.nav_buttons = []
        nav_items = [
            ("📄", "文章管理"),
            ("🏷️", "关键词"),
            ("📚", "知识库"),
            ("🌐", "CMS 配置"),
        ]
        
        for icon, text in nav_items:
            btn = NavButton(f"  {icon}  {text}")
            btn.clicked.connect(lambda checked, b=btn: self.on_nav_click(b))
            self.nav_buttons.append(btn)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # 底部导航
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #E5E7EB;")
        divider.setFixedHeight(1)
        layout.addWidget(divider)
        layout.addSpacing(8)
        
        bottom_items = [
            ("⚙️", "系统设置"),
            ("📋", "发布日志"),
        ]
        
        for icon, text in bottom_items:
            btn = NavButton(f"  {icon}  {text}")
            btn.clicked.connect(lambda checked, b=btn: self.on_nav_click(b))
            self.nav_buttons.append(btn)
            layout.addWidget(btn)
        
        # 默认选中第一个
        self.nav_buttons[0].setChecked(True)
        self.nav_buttons[0].update_style(True)
        
        self.current_index = 0
        self.on_index_changed = None
    
    def on_nav_click(self, button):
        index = self.nav_buttons.index(button)
        if index != self.current_index:
            # 更新样式
            self.nav_buttons[self.current_index].setChecked(False)
            self.nav_buttons[self.current_index].update_style(False)
            button.setChecked(True)
            button.update_style(True)
            self.current_index = index
            
            if self.on_index_changed:
                self.on_index_changed(index)


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.api_client = APIClient()
        self.init_ui()
        
        # 检查 API 连接
        QTimer.singleShot(500, self.check_api_connection)
    
    def init_ui(self):
        self.setWindowTitle("AI 文章自动生成系统")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # 中心部件
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 侧边栏
        self.sidebar = Sidebar()
        self.sidebar.on_index_changed = self.switch_page
        main_layout.addWidget(self.sidebar)
        
        # 内容区
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #F9FAFB;")
        main_layout.addWidget(self.stack, 1)
        
        # 添加页面
        self.stack.addWidget(ArticlesTab(self.api_client))
        self.stack.addWidget(KeywordsTab(self.api_client))
        self.stack.addWidget(KnowledgeBaseTab(self.api_client))
        self.stack.addWidget(CMSTab(self.api_client))
        self.stack.addWidget(ConfigTab(self.api_client))
        self.stack.addWidget(LogsTab(self.api_client))
    
    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
    
    def check_api_connection(self):
        try:
            import requests
            requests.get("http://localhost:8000/health", timeout=3)
        except Exception:
            pass  # 静默处理


def run_gui():
    """启动 GUI"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()
