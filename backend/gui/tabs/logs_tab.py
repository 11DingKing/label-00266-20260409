"""
发布日志页面
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from gui.components import CardWithTitle, PageTitle, SecondaryButton, Pagination, ToastManager
from gui.api_client import format_datetime


class LogsTab(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.init_ui()
        self.load_logs()
    
    def init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)
        
        # 标题和统计
        header = QHBoxLayout()
        header.addWidget(PageTitle("发布日志", "查看文章发布历史记录"))
        header.addStretch()
        self.total_label = QLabel("总记录: 0")
        self.total_label.setStyleSheet("color: #2563EB; font-size: 14px; font-weight: 600;")
        header.addWidget(self.total_label)
        self.success_label = QLabel("成功: 0")
        self.success_label.setStyleSheet("color: #10B981; font-size: 13px; margin-left: 16px;")
        header.addWidget(self.success_label)
        self.failed_label = QLabel("失败: 0")
        self.failed_label.setStyleSheet("color: #EF4444; font-size: 13px; margin-left: 8px;")
        header.addWidget(self.failed_label)
        refresh_btn = SecondaryButton("刷新")
        refresh_btn.clicked.connect(self.refresh_logs)
        header.addWidget(refresh_btn)
        layout.addLayout(header)
        
        # 日志列表
        list_frame = QFrame()
        list_frame.setObjectName("listFrame")
        list_frame.setStyleSheet("#listFrame { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; } #listFrame QLabel { background: transparent; }")
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(16, 12, 16, 12)
        list_layout.setSpacing(10)
        
        list_title = QLabel("发布记录")
        list_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #1F2937;")
        list_layout.addWidget(list_title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "文章 ID", "状态", "错误信息", "时间"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(4, 140)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(300)
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
        
        layout.addWidget(list_frame, 1)
        
        scroll.setWidget(content)
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(scroll)
    
    def on_page_changed(self, page):
        self.load_logs()
    
    def refresh_logs(self):
        self.load_logs()
        ToastManager.success("刷新成功", self)
    
    def load_logs(self):
        try:
            page = self.pagination.currentPage()
            page_size = self.pagination.pageSize()
            r = self.api_client.get("/logs", params={"limit": page_size, "offset": (page - 1) * page_size})
            data = r.get("data", {})
            if isinstance(data, list):
                logs = data
                total = len(logs)
            else:
                logs = data.get("items", [])
                total = data.get("total", len(logs))
            
            # 更新分页
            self.pagination.setPageInfo(total, page_size, page)
            
            success = len([l for l in logs if l.get("status") == "success"])
            failed = len([l for l in logs if l.get("status") == "failed"])
            
            self.total_label.setText(f"总记录: {total}")
            self.success_label.setText(f"成功: {success}")
            self.failed_label.setText(f"失败: {failed}")
            
            self.table.setRowCount(len(logs))
            for row, log in enumerate(logs):
                self.table.setItem(row, 0, QTableWidgetItem(str(log.get("id", ""))))
                self.table.setItem(row, 1, QTableWidgetItem(str(log.get("article_id", ""))))
                
                status = log.get("status", "")
                if status == "success":
                    si = QTableWidgetItem("成功")
                    si.setForeground(QColor("#10B981"))
                else:
                    si = QTableWidgetItem("失败")
                    si.setForeground(QColor("#EF4444"))
                si.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 2, si)
                
                error = log.get("error_message", "") or "-"
                ei = QTableWidgetItem(error[:50] + "..." if len(error) > 50 else error)
                if error != "-":
                    ei.setForeground(QColor("#EF4444"))
                    ei.setToolTip(error)
                self.table.setItem(row, 3, ei)
                
                self.table.setItem(row, 4, QTableWidgetItem(format_datetime(log.get("created_at"))))
                self.table.setRowHeight(row, 44)
        except:
            pass
