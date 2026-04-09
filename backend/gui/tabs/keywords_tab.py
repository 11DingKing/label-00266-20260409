"""
关键词管理页面
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit,
    QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from gui.components import CardWithTitle, PageTitle, PrimaryButton, SecondaryButton, LinkButton, Pagination, ToastManager, confirm_dialog
from gui.api_client import format_datetime


class KeywordsTab(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.init_ui()
        self.load_keywords()
    
    def init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)
        
        # 标题
        header = QHBoxLayout()
        header.addWidget(PageTitle("关键词管理", "管理用于 AI 文章生成的关键词"))
        header.addStretch()
        self.count_label = QLabel("共 0 个")
        self.count_label.setStyleSheet("color: #2563EB; font-size: 14px; font-weight: 600;")
        header.addWidget(self.count_label)
        layout.addLayout(header)
        
        # 内容
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)
        
        # 添加卡片
        add_card = QFrame()
        add_card.setObjectName("addCard")
        add_card.setStyleSheet("#addCard { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; } #addCard QLabel { background: transparent; }")
        add_layout = QVBoxLayout(add_card)
        add_layout.setContentsMargins(16, 12, 16, 12)
        add_layout.setSpacing(10)
        
        add_title = QLabel("添加关键词")
        add_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #1F2937;")
        add_layout.addWidget(add_title)
        add_hint = QLabel("每行输入一个关键词")
        add_hint.setStyleSheet("font-size: 12px; color: #9CA3AF;")
        add_layout.addWidget(add_hint)
        
        self.keywords_edit = QTextEdit()
        self.keywords_edit.setPlaceholderText("人工智能\n机器学习\n深度学习")
        self.keywords_edit.setMinimumHeight(150)
        self.keywords_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background-color: #FFFFFF;
                padding: 10px;
            }
            QTextEdit:focus {
                border-color: #2563EB;
            }
        """)
        add_layout.addWidget(self.keywords_edit)
        
        add_btn = PrimaryButton("添加")
        add_btn.clicked.connect(self.add_keywords)
        add_layout.addWidget(add_btn)
        content_layout.addWidget(add_card, 1)
        
        # 列表卡片
        list_frame = QFrame()
        list_frame.setObjectName("listFrame")
        list_frame.setStyleSheet("#listFrame { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; } #listFrame QLabel { background: transparent; }")
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(16, 12, 16, 12)
        list_layout.setSpacing(10)
        
        toolbar = QHBoxLayout()
        list_title = QLabel("关键词列表")
        list_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #1F2937;")
        toolbar.addWidget(list_title)
        toolbar.addStretch()
        refresh_btn = SecondaryButton("刷新")
        refresh_btn.clicked.connect(self.refresh_keywords)
        toolbar.addWidget(refresh_btn)
        clear_btn = SecondaryButton("清空")
        clear_btn.clicked.connect(self.clear_all)
        toolbar.addWidget(clear_btn)
        list_layout.addLayout(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "关键词", "添加时间", "操作"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 140)
        self.table.setColumnWidth(3, 70)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { border: 1px solid #E5E7EB; border-radius: 6px; background: #FFF; }
            QTableWidget::item { padding: 6px; color: #1F2937; }
            QTableWidget::item:alternate { background: #F9FAFB; }
        """)
        list_layout.addWidget(self.table, 1)
        
        # 分页
        self.pagination = Pagination()
        self.pagination.pageChanged.connect(self.on_page_changed)
        list_layout.addWidget(self.pagination)
        
        content_layout.addWidget(list_frame, 2)
        
        layout.addLayout(content_layout, 1)
        scroll.setWidget(content)
        
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(scroll)
    
    def on_page_changed(self, page):
        self.load_keywords()
    
    def refresh_keywords(self):
        self.load_keywords()
        ToastManager.success("刷新成功", self)
    
    def load_keywords(self):
        try:
            page = self.pagination.currentPage()
            page_size = self.pagination.pageSize()
            r = self.api_client.get("/keywords", params={"limit": page_size, "offset": (page - 1) * page_size})
            data = r.get("data", {})
            if isinstance(data, list):
                keywords = data
                total = len(keywords)
            else:
                keywords = data.get("items", [])
                total = data.get("total", len(keywords))
            
            self.pagination.setPageInfo(total, page_size, page)
            self.count_label.setText(f"共 {total} 个")
            
            self.table.setRowCount(len(keywords))
            for row, kw in enumerate(keywords):
                self.table.setItem(row, 0, QTableWidgetItem(str(kw.get("id", ""))))
                
                ki = QTableWidgetItem(kw.get("keyword", ""))
                ki.setForeground(QColor("#2563EB"))
                self.table.setItem(row, 1, ki)
                
                self.table.setItem(row, 2, QTableWidgetItem(format_datetime(kw.get("created_at"))))
                
                del_btn = LinkButton("删除", "#EF4444")
                del_btn.clicked.connect(lambda _, x=kw.get("id"): self.delete_keyword(x))
                self.table.setCellWidget(row, 3, del_btn)
                self.table.setRowHeight(row, 40)
        except:
            pass
    
    def add_keywords(self):
        text = self.keywords_edit.toPlainText().strip()
        if not text:
            return
        keywords = [k.strip() for k in text.split("\n") if k.strip()]
        if not keywords:
            return
        try:
            self.api_client.post("/keywords", json={"keywords": keywords})
            self.keywords_edit.clear()
            self.load_keywords()
            ToastManager.success(f"添加成功，共 {len(keywords)} 个", self)
        except Exception as e:
            ToastManager.error(f"添加失败: {str(e)}", self)
    
    def delete_keyword(self, kid):
        try:
            self.api_client.delete(f"/keywords/{kid}")
            self.load_keywords()
            ToastManager.success("删除成功", self)
        except Exception as e:
            ToastManager.error(f"删除失败: {str(e)}", self)
    
    def clear_all(self):
        if confirm_dialog(self, "确认", "清空所有关键词？"):
            try:
                r = self.api_client.get("/keywords", params={"limit": 1000})
                for kw in r.get("data", []):
                    self.api_client.delete(f"/keywords/{kw['id']}")
                self.load_keywords()
                ToastManager.success("关键词已清空", self)
            except Exception as e:
                ToastManager.error(f"清空失败: {str(e)}", self)
