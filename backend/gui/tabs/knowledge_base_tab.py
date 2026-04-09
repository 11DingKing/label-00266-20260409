"""
知识库管理页面
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QScrollArea, QMessageBox, QFileDialog, QProgressBar, QDialog, QTextEdit
)
from PySide6.QtCore import Qt, QThread, Signal
import os

from gui.components import CardWithTitle, PageTitle, PrimaryButton, SecondaryButton, LinkButton, Pagination, ToastManager, confirm_dialog
from gui.api_client import format_datetime


class UploadThread(QThread):
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, api_client, files):
        super().__init__()
        self.api_client = api_client
        self.files = files
    
    def run(self):
        try:
            import requests
            files_data = []
            for f in self.files:
                with open(f, "rb") as fp:
                    files_data.append(("files", (os.path.basename(f), fp.read())))
            r = requests.post(f"{self.api_client.base_url}/knowledge-base/upload", files=files_data, timeout=120)
            r.raise_for_status()
            self.finished.emit(r.json())
        except Exception as e:
            self.error.emit(str(e))


class ScanThread(QThread):
    progress = Signal(dict)
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, api_client, folder):
        super().__init__()
        self.api_client = api_client
        self.folder = folder
        self.running = True
    
    def run(self):
        try:
            r = self.api_client.post("/knowledge-base/scan", json={"folder_path": self.folder})
            task_id = r.get("data", {}).get("task_id")
            if not task_id:
                self.error.emit("无任务ID")
                return
            while self.running:
                s = self.api_client.get(f"/knowledge-base/scan/status/{task_id}")
                d = s.get("data", {})
                self.progress.emit(d)
                if d.get("status") == "completed":
                    self.finished.emit(d)
                    break
                elif d.get("status") == "failed":
                    self.error.emit(d.get("message", "失败"))
                    break
                self.msleep(1000)
        except Exception as e:
            self.error.emit(str(e))


class ContentDialog(QDialog):
    def __init__(self, parent, content, path):
        super().__init__(parent)
        self.setWindowTitle(f"内容 - {os.path.basename(path)}")
        self.setMinimumSize(700, 500)
        self.setStyleSheet("background-color: #FFFFFF;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        edit = QTextEdit()
        edit.setPlainText(content)
        edit.setReadOnly(True)
        layout.addWidget(edit)
        
        btn = SecondaryButton("关闭")
        btn.clicked.connect(self.reject)
        layout.addWidget(btn)


class KnowledgeBaseTab(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.upload_thread = None
        self.scan_thread = None
        self.selected_files = []
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)
        
        # 标题和统计放一行
        header = QHBoxLayout()
        header.addWidget(PageTitle("知识库", "上传文档作为 AI 生成文章的参考资料"))
        header.addStretch()
        
        # 统计放右边
        self.total_label = QLabel("总计: 0")
        self.total_label.setStyleSheet("color: #2563EB; font-size: 14px; font-weight: 600;")
        header.addWidget(self.total_label)
        self.txt_label = QLabel("TXT: 0")
        self.txt_label.setStyleSheet("color: #6B7280; font-size: 13px; margin-left: 16px;")
        header.addWidget(self.txt_label)
        self.pdf_label = QLabel("PDF: 0")
        self.pdf_label.setStyleSheet("color: #6B7280; font-size: 13px; margin-left: 8px;")
        header.addWidget(self.pdf_label)
        self.doc_label = QLabel("DOCX: 0")
        self.doc_label.setStyleSheet("color: #6B7280; font-size: 13px; margin-left: 8px;")
        header.addWidget(self.doc_label)
        layout.addLayout(header)
        
        # 操作区 - 更紧凑
        actions = QHBoxLayout()
        actions.setSpacing(16)
        
        # 上传卡片 - 简化
        upload_card = QFrame()
        # 上传卡片 - 简化
        upload_card = QFrame()
        upload_card.setObjectName("uploadCard")
        upload_card.setStyleSheet("#uploadCard { background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; } #uploadCard QLabel { background: transparent; }")
        upload_layout = QVBoxLayout(upload_card)
        upload_layout.setContentsMargins(16, 12, 16, 12)
        upload_layout.setSpacing(10)
        
        upload_title = QLabel("上传文件")
        upload_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #1F2937;")
        upload_layout.addWidget(upload_title)
        
        upload_hint = QLabel("支持 TXT, PDF, DOCX, XLSX, MD")
        upload_hint.setStyleSheet("font-size: 12px; color: #9CA3AF;")
        upload_layout.addWidget(upload_hint)
        
        self.file_label = QLabel("未选择文件")
        self.file_label.setStyleSheet("color: #9CA3AF; font-size: 13px;")
        self.file_label.setFixedHeight(20)
        upload_layout.addWidget(self.file_label)
        
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        sel_btn = SecondaryButton("选择文件")
        sel_btn.setFixedWidth(100)
        sel_btn.clicked.connect(self.select_files)
        btn_row.addWidget(sel_btn)
        self.upload_btn = PrimaryButton("上传")
        self.upload_btn.setFixedWidth(80)
        self.upload_btn.setEnabled(False)
        self.upload_btn.clicked.connect(self.upload_files)
        btn_row.addWidget(self.upload_btn)
        btn_row.addStretch()
        upload_layout.addLayout(btn_row)
        actions.addWidget(upload_card)
        
        # 扫描卡片 - 简化
        scan_card = QFrame()
        scan_card.setObjectName("scanCard")
        scan_card.setStyleSheet("#scanCard { background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; } #scanCard QLabel { background: transparent; }")
        scan_layout = QVBoxLayout(scan_card)
        scan_layout.setContentsMargins(16, 12, 16, 12)
        scan_layout.setSpacing(10)
        
        scan_title = QLabel("扫描文件夹")
        scan_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #1F2937; background: transparent;")
        scan_layout.addWidget(scan_title)
        
        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择文件夹路径")
        self.path_edit.setFixedHeight(36)
        path_row.addWidget(self.path_edit)
        browse_btn = SecondaryButton("浏览")
        browse_btn.setFixedWidth(70)
        browse_btn.clicked.connect(self.browse_folder)
        path_row.addWidget(browse_btn)
        scan_layout.addLayout(path_row)
        
        self.scan_progress = QProgressBar()
        self.scan_progress.setFixedHeight(4)
        self.scan_progress.setVisible(False)
        scan_layout.addWidget(self.scan_progress)
        
        self.scan_label = QLabel("")
        self.scan_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        self.scan_label.setVisible(False)
        scan_layout.addWidget(self.scan_label)
        
        self.scan_btn = PrimaryButton("扫描")
        self.scan_btn.clicked.connect(self.scan_folder)
        scan_layout.addWidget(self.scan_btn)
        actions.addWidget(scan_card, 2)
        
        layout.addLayout(actions)
        
        # 文件列表 - 占据更多空间
        list_frame = QFrame()
        list_frame.setObjectName("listFrame")
        list_frame.setStyleSheet("#listFrame { background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; } #listFrame QLabel { background: transparent; }")
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(16, 12, 16, 12)
        list_layout.setSpacing(10)
        
        toolbar = QHBoxLayout()
        list_title = QLabel("文件列表")
        list_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #1F2937;")
        toolbar.addWidget(list_title)
        toolbar.addStretch()
        refresh_btn = SecondaryButton("刷新")
        refresh_btn.clicked.connect(self.refresh_data)
        toolbar.addWidget(refresh_btn)
        clear_btn = SecondaryButton("清空")
        clear_btn.clicked.connect(self.clear_all)
        toolbar.addWidget(clear_btn)
        list_layout.addLayout(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "文件路径", "类型", "添加时间", "操作"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 140)
        self.table.setColumnWidth(4, 100)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(400)
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
        self.load_list()
    
    def refresh_data(self):
        self.load_data()
        ToastManager.success("刷新成功", self)
    
    def load_data(self):
        self.load_stats()
        self.load_list()
    
    def load_stats(self):
        try:
            r = self.api_client.get("/knowledge-base/stats")
            s = r.get("data", {})
            self.total_label.setText(f"总计: {s.get('total', 0)}")
            self.txt_label.setText(f"TXT: {s.get('txt', 0)}")
            self.pdf_label.setText(f"PDF: {s.get('pdf', 0)}")
            self.doc_label.setText(f"DOCX: {s.get('docx', 0)}")
        except:
            pass
    
    def load_list(self):
        try:
            page = self.pagination.currentPage()
            page_size = self.pagination.pageSize()
            r = self.api_client.get("/knowledge-base/list", params={"limit": page_size, "offset": (page - 1) * page_size})
            data = r.get("data", {})
            if isinstance(data, list):
                items = data
                total = len(items)
            else:
                items = data.get("items", [])
                total = data.get("total", len(items))
            
            # 更新分页
            self.pagination.setPageInfo(total, page_size, page)
            
            self.table.setRowCount(len(items))
            for row, item in enumerate(items):
                self.table.setItem(row, 0, QTableWidgetItem(str(item.get("id", ""))))
                self.table.setItem(row, 1, QTableWidgetItem(item.get("file_path", "")))
                
                ti = QTableWidgetItem(item.get("file_type", "").upper())
                ti.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 2, ti)
                
                self.table.setItem(row, 3, QTableWidgetItem(format_datetime(item.get("created_at"))))
                
                w = QWidget()
                l = QHBoxLayout(w)
                l.setContentsMargins(4, 2, 4, 2)
                l.setSpacing(8)
                
                v = LinkButton("查看")
                v.clicked.connect(lambda _, x=item: self.view_content(x))
                l.addWidget(v)
                
                d = LinkButton("删除", "#EF4444")
                d.clicked.connect(lambda _, x=item.get("id"): self.delete_item(x))
                l.addWidget(d)
                l.addStretch()
                
                self.table.setCellWidget(row, 4, w)
                self.table.setRowHeight(row, 44)
        except:
            pass
    
    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", "支持的文件 (*.txt *.pdf *.docx *.xlsx *.md)")
        if files:
            self.selected_files = files
            self.file_label.setText(f"已选择 {len(files)} 个文件")
            self.file_label.setStyleSheet("color: #2563EB;")
            self.upload_btn.setEnabled(True)
    
    def upload_files(self):
        if not self.selected_files:
            return
        self.upload_btn.setEnabled(False)
        self.upload_btn.setText("上传中...")
        self.upload_thread = UploadThread(self.api_client, self.selected_files)
        self.upload_thread.finished.connect(self.on_upload_done)
        self.upload_thread.error.connect(self.on_upload_err)
        self.upload_thread.start()
    
    def on_upload_done(self, r):
        self.upload_btn.setEnabled(True)
        self.upload_btn.setText("上传")
        self.selected_files = []
        self.file_label.setText("未选择文件")
        self.file_label.setStyleSheet("color: #9CA3AF;")
        self.upload_btn.setEnabled(False)
        self.load_data()
        ToastManager.success("上传成功", self)
    
    def on_upload_err(self, e):
        self.upload_btn.setEnabled(True)
        self.upload_btn.setText("上传")
        ToastManager.error(f"上传失败: {e}", self)
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.path_edit.setText(folder)
    
    def scan_folder(self):
        path = self.path_edit.text().strip()
        if not path:
            return
        self.scan_btn.setEnabled(False)
        self.scan_progress.setVisible(True)
        self.scan_label.setVisible(True)
        self.scan_label.setText("扫描中...")
        self.scan_thread = ScanThread(self.api_client, path)
        self.scan_thread.progress.connect(self.on_scan_progress)
        self.scan_thread.finished.connect(self.on_scan_done)
        self.scan_thread.error.connect(self.on_scan_err)
        self.scan_thread.start()
    
    def on_scan_progress(self, d):
        self.scan_progress.setValue(d.get("progress", 0))
        self.scan_label.setText(d.get("message", "扫描中..."))
    
    def on_scan_done(self, d):
        self.scan_btn.setEnabled(True)
        self.scan_progress.setVisible(False)
        self.scan_label.setVisible(False)
        self.load_data()
        ToastManager.success("扫描完成", self)
    
    def on_scan_err(self, e):
        self.scan_btn.setEnabled(True)
        self.scan_progress.setVisible(False)
        self.scan_label.setVisible(False)
        ToastManager.error(f"扫描失败: {e}", self)
    
    def view_content(self, item):
        try:
            r = self.api_client.get(f"/knowledge-base/{item['id']}")
            content = r.get("data", {}).get("content", "")
            ContentDialog(self, content, item.get("file_path", "")).exec()
        except:
            pass
    
    def delete_item(self, item_id):
        try:
            self.api_client.delete(f"/knowledge-base/{item_id}")
            self.load_data()
            ToastManager.success("删除成功", self)
        except Exception as e:
            ToastManager.error(f"删除失败: {str(e)}", self)
    
    def clear_all(self):
        if confirm_dialog(self, "确认", "清空知识库？"):
            try:
                self.api_client.delete("/knowledge-base")
                self.load_data()
                ToastManager.success("知识库已清空", self)
            except Exception as e:
                ToastManager.error(f"清空失败: {str(e)}", self)
