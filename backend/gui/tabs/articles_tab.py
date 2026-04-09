"""
文章管理页面
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QSpinBox, QComboBox, QTextEdit, QLineEdit, QScrollArea,
    QCheckBox, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor

from gui.components import CardWithTitle, PageTitle, PrimaryButton, SecondaryButton, LinkButton, StyledSpinBox, StyledComboBox, StyledCheckBox, Pagination, ToastManager, confirm_dialog
from gui.api_client import format_datetime, get_status_text


class GenerateThread(QThread):
    progress = Signal(dict)
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, api_client, params):
        super().__init__()
        self.api_client = api_client
        self.params = params
        self.running = True
        
    def run(self):
        try:
            self.api_client.post("/articles/generate", json=self.params)
            while self.running:
                status = self.api_client.get("/articles/generate/status")
                data = status.get("data", {})
                if data.get("status") == "running":
                    self.progress.emit(data)
                    self.msleep(1000)
                elif data.get("status") == "completed":
                    self.finished.emit(data)
                    break
                elif data.get("status") == "failed":
                    self.error.emit(data.get("errors", ["失败"])[0])
                    break
                else:
                    self.msleep(500)
        except Exception as e:
            self.error.emit(str(e))
    
    def stop(self):
        self.running = False


class ArticleDialog(QDialog):
    def __init__(self, parent, article, edit_mode=False):
        super().__init__(parent)
        self.setWindowTitle("编辑文章" if edit_mode else "查看文章")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("background-color: #FFFFFF;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)
        
        layout.addWidget(QLabel("标题"))
        self.title_edit = QLineEdit()
        self.title_edit.setText(article.get("title", ""))
        self.title_edit.setReadOnly(not edit_mode)
        layout.addWidget(self.title_edit)
        
        content = article.get("content", "")
        layout.addWidget(QLabel(f"内容 ({len(content)} 字)"))
        self.content_edit = QTextEdit()
        self.content_edit.setPlainText(content)
        self.content_edit.setReadOnly(not edit_mode)
        layout.addWidget(self.content_edit, 1)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        if edit_mode:
            cancel = SecondaryButton("取消")
            cancel.clicked.connect(self.reject)
            btn_layout.addWidget(cancel)
            save = PrimaryButton("保存")
            save.clicked.connect(self.accept)
            btn_layout.addWidget(save)
        else:
            close = SecondaryButton("关闭")
            close.clicked.connect(self.reject)
            btn_layout.addWidget(close)
        layout.addLayout(btn_layout)
    
    def get_data(self):
        return {"title": self.title_edit.text(), "content": self.content_edit.toPlainText()}


class ArticlesTab(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.generate_thread = None
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
        
        header = QHBoxLayout()
        header.addWidget(PageTitle("文章管理", "使用 AI 自动生成并发布文章"))
        header.addStretch()
        refresh = SecondaryButton("刷新")
        refresh.clicked.connect(self.refresh_data)
        header.addWidget(refresh)
        layout.addLayout(header)
        
        # 紧凑卡片布局
        cards = QHBoxLayout()
        cards.setSpacing(16)
        
        # AI 生成文章卡片 - 紧凑版
        gen_card = QFrame()
        gen_card.setObjectName("genCard")
        gen_card.setStyleSheet("#genCard { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; } #genCard QLabel { background: transparent; }")
        gen_layout = QVBoxLayout(gen_card)
        gen_layout.setContentsMargins(16, 12, 16, 12)
        gen_layout.setSpacing(10)
        
        gen_title = QLabel("AI 生成文章")
        gen_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #1F2937;")
        gen_layout.addWidget(gen_title)
        
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("生成数量"))
        r1.addStretch()
        self.count_spin = StyledSpinBox()
        self.count_spin.setRange(1, 50)
        self.count_spin.setValue(5)
        r1.addWidget(self.count_spin)
        r1.addWidget(QLabel("篇"))
        gen_layout.addLayout(r1)
        
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("结合知识库"))
        r2.addStretch()
        self.use_kb = StyledCheckBox()
        self.use_kb.setChecked(True)
        r2.addWidget(self.use_kb)
        gen_layout.addLayout(r2)
        
        # 进度显示区域 - 优化样式
        self.progress_widget = QFrame()
        self.progress_widget.setObjectName("progressFrame")
        self.progress_widget.setStyleSheet("""
            #progressFrame {
                background-color: #F0F9FF;
                border: 1px solid #BAE6FD;
                border-radius: 8px;
                padding: 8px;
            }
            #progressFrame QLabel {
                background: transparent;
            }
        """)
        pl = QVBoxLayout(self.progress_widget)
        pl.setContentsMargins(12, 10, 12, 10)
        pl.setSpacing(8)
        
        # 进度文字行
        progress_header = QHBoxLayout()
        self.progress_icon = QLabel("⏳")
        self.progress_icon.setStyleSheet("font-size: 16px;")
        progress_header.addWidget(self.progress_icon)
        self.progress_label = QLabel("准备中...")
        self.progress_label.setStyleSheet("color: #0369A1; font-size: 13px; font-weight: 500;")
        progress_header.addWidget(self.progress_label)
        progress_header.addStretch()
        self.progress_percent = QLabel("0%")
        self.progress_percent.setStyleSheet("color: #0369A1; font-size: 13px; font-weight: 600;")
        progress_header.addWidget(self.progress_percent)
        pl.addLayout(progress_header)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 3px;
                background-color: #E0F2FE;
            }
            QProgressBar::chunk {
                border-radius: 3px;
                background-color: #0EA5E9;
            }
        """)
        pl.addWidget(self.progress_bar)
        
        self.progress_widget.setVisible(False)
        gen_layout.addWidget(self.progress_widget)
        
        self.gen_btn = PrimaryButton("开始生成")
        self.gen_btn.clicked.connect(self.start_generate)
        gen_layout.addWidget(self.gen_btn)
        cards.addWidget(gen_card)
        
        # 定时发布卡片 - 紧凑版
        sched_card = QFrame()
        sched_card.setObjectName("schedCard")
        sched_card.setStyleSheet("#schedCard { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; } #schedCard QLabel { background: transparent; }")
        sched_layout = QVBoxLayout(sched_card)
        sched_layout.setContentsMargins(16, 12, 16, 12)
        sched_layout.setSpacing(8)
        
        sched_title = QLabel("定时发布")
        sched_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #1F2937;")
        sched_layout.addWidget(sched_title)
        
        s1 = QHBoxLayout()
        s1.addWidget(QLabel("每次生成"))
        s1.addStretch()
        self.gen_count = StyledSpinBox()
        self.gen_count.setRange(1, 100)
        self.gen_count.setValue(5)
        s1.addWidget(self.gen_count)
        s1.addWidget(QLabel("篇"))
        sched_layout.addLayout(s1)
        
        s2 = QHBoxLayout()
        s2.addWidget(QLabel("每次发布"))
        s2.addStretch()
        self.pub_count = StyledSpinBox()
        self.pub_count.setRange(1, 20)
        self.pub_count.setValue(1)
        s2.addWidget(self.pub_count)
        s2.addWidget(QLabel("篇"))
        sched_layout.addLayout(s2)
        
        s3 = QHBoxLayout()
        s3.addWidget(QLabel("发布间隔"))
        s3.addStretch()
        self.freq_val = StyledSpinBox()
        self.freq_val.setRange(1, 1000)
        self.freq_val.setValue(1)
        s3.addWidget(self.freq_val)
        self.freq_unit = StyledComboBox()
        self.freq_unit.addItems(["分钟", "小时", "天"])
        self.freq_unit.setCurrentIndex(1)
        self.freq_unit.setFixedWidth(90)
        s3.addWidget(self.freq_unit)
        sched_layout.addLayout(s3)
        
        status_btns = QHBoxLayout()
        self.sched_status = QLabel("● 未启动")
        self.sched_status.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        status_btns.addWidget(self.sched_status)
        status_btns.addStretch()
        save = SecondaryButton("保存")
        save.clicked.connect(self.save_config)
        status_btns.addWidget(save)
        self.toggle_btn = PrimaryButton("启动")
        self.toggle_btn.clicked.connect(self.toggle_sched)
        status_btns.addWidget(self.toggle_btn)
        sched_layout.addLayout(status_btns)
        cards.addWidget(sched_card, 2)
        
        # 快捷操作卡片 - 居中布局
        quick_card = QFrame()
        quick_card.setObjectName("quickCard")
        quick_card.setStyleSheet("#quickCard { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; } #quickCard QLabel { background: transparent; }")
        quick_layout = QVBoxLayout(quick_card)
        quick_layout.setContentsMargins(16, 12, 16, 12)
        quick_layout.setSpacing(8)
        
        quick_title = QLabel("快捷操作")
        quick_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #1F2937;")
        quick_layout.addWidget(quick_title)
        
        # 待发布数量
        self.pending_count_label = QLabel("待发布: 0 篇")
        self.pending_count_label.setStyleSheet("color: #F59E0B; font-size: 13px; font-weight: 500;")
        self.pending_count_label.setAlignment(Qt.AlignCenter)
        quick_layout.addWidget(self.pending_count_label)
        
        quick_layout.addStretch()
        self.pub_all_btn = PrimaryButton("一键发布全部")
        self.pub_all_btn.clicked.connect(self.publish_all)
        quick_layout.addWidget(self.pub_all_btn, 0, Qt.AlignCenter)
        self.quick_tip = QLabel("将所有待发布文章发布到 CMS")
        self.quick_tip.setStyleSheet("color: #6B7280; font-size: 12px;")
        self.quick_tip.setAlignment(Qt.AlignCenter)
        quick_layout.addWidget(self.quick_tip)
        quick_layout.addStretch()
        cards.addWidget(quick_card)
        
        layout.addLayout(cards)
        
        # 文章列表 - 紧凑版
        list_frame = QFrame()
        list_frame.setObjectName("listFrame")
        list_frame.setStyleSheet("#listFrame { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; } #listFrame QLabel { background: transparent; }")
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(16, 12, 16, 12)
        list_layout.setSpacing(10)
        
        fr = QHBoxLayout()
        list_title = QLabel("文章列表")
        list_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #1F2937;")
        fr.addWidget(list_title)
        fr.addSpacing(20)
        fr.addWidget(QLabel("状态"))
        self.status_filter = StyledComboBox()
        self.status_filter.addItems(["全部", "待发布", "已发布", "失败"])
        self.status_filter.setFixedWidth(100)
        self.status_filter.currentIndexChanged.connect(self.load_articles)
        fr.addWidget(self.status_filter)
        fr.addStretch()
        list_layout.addLayout(fr)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "标题", "状态", "生成时间", "发布时间", "操作"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 140)
        self.table.setColumnWidth(4, 140)
        self.table.setColumnWidth(5, 240)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(300)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                background: #FFFFFF;
            }
            QTableWidget::item {
                padding: 6px;
                color: #1F2937;
            }
            QTableWidget::item:alternate {
                background: #F9FAFB;
            }
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
        self.load_articles()

    def refresh_data(self):
        self.load_data()
        ToastManager.success("刷新成功", self)

    def load_data(self):
        self.load_config()
        self.load_articles()
        self.load_sched_status()
    
    def update_pending_count(self):
        """更新待发布文章数量"""
        try:
            r = self.api_client.get("/articles", params={"status": "pending", "limit": 1, "skip": 0})
            data = r.get("data", {})
            count = data.get("total", 0)
            if count > 0:
                self.pending_count_label.setText(f"待发布: {count} 篇")
                self.pending_count_label.setStyleSheet("color: #F59E0B; font-size: 13px; font-weight: 500;")
                self.pub_all_btn.setEnabled(True)
            else:
                self.pending_count_label.setText("全部已发布 ✓")
                self.pending_count_label.setStyleSheet("color: #10B981; font-size: 13px; font-weight: 500;")
                self.pub_all_btn.setEnabled(False)
        except Exception as e:
            print(f"update_pending_count error: {e}")
    
    def load_config(self):
        try:
            r = self.api_client.get("/articles/generation-config")
            c = r.get("data", {})
            self.gen_count.setValue(c.get("count", 5))
            self.pub_count.setValue(c.get("publish_count", 1))
            self.freq_val.setValue(c.get("frequency_value", 1))
            m = {"minute": 0, "hour": 1, "day": 2}
            self.freq_unit.setCurrentIndex(m.get(c.get("frequency_unit", "hour"), 1))
        except:
            pass
    
    def load_articles(self):
        try:
            m = {"全部": None, "待发布": "pending", "已发布": "published", "失败": "failed"}
            s = m.get(self.status_filter.currentText())
            page = self.pagination.currentPage()
            page_size = self.pagination.pageSize()
            p = {"limit": page_size, "skip": (page - 1) * page_size}
            if s:
                p["status"] = s
            r = self.api_client.get("/articles", params=p)
            data = r.get("data", {})
            articles = data.get("items", [])
            total = data.get("total", len(articles))
            
            # 更新分页
            self.pagination.setPageInfo(total, page_size, page)
            
            # 更新待发布数量
            self.update_pending_count()
            
            self.table.setRowCount(len(articles))
            for row, a in enumerate(articles):
                self.table.setItem(row, 0, QTableWidgetItem(str(a.get("id", ""))))
                self.table.setItem(row, 1, QTableWidgetItem(a.get("title", "")[:60]))
                st = a.get("status", "")
                si = QTableWidgetItem(get_status_text(st))
                si.setTextAlignment(Qt.AlignCenter)
                if st == "published":
                    si.setForeground(QColor("#10B981"))
                elif st == "failed":
                    si.setForeground(QColor("#EF4444"))
                else:
                    si.setForeground(QColor("#F59E0B"))
                self.table.setItem(row, 2, si)
                self.table.setItem(row, 3, QTableWidgetItem(format_datetime(a.get("generated_at"))))
                self.table.setItem(row, 4, QTableWidgetItem(format_datetime(a.get("published_at"))))
                w = QWidget()
                l = QHBoxLayout(w)
                l.setContentsMargins(2, 2, 2, 2)
                l.setSpacing(4)
                v = LinkButton("查看")
                v.clicked.connect(lambda _, x=a: self.view_article(x))
                l.addWidget(v)
                e = LinkButton("编辑")
                e.clicked.connect(lambda _, x=a: self.edit_article(x))
                l.addWidget(e)
                if st in ["pending", "failed"]:
                    pb = LinkButton("发布", "#10B981")
                    pb.clicked.connect(lambda _, x=a.get("id"): self.pub_one(x))
                    l.addWidget(pb)
                d = LinkButton("删除", "#EF4444")
                d.clicked.connect(lambda _, x=a.get("id"): self.del_one(x))
                l.addWidget(d)
                l.addStretch()
                self.table.setCellWidget(row, 5, w)
                self.table.setRowHeight(row, 44)
        except:
            pass
    
    def load_sched_status(self):
        try:
            r = self.api_client.get("/articles/scheduled-publish/status")
            d = r.get("data", {})
            if d.get("running"):
                self.sched_status.setText("● 运行中")
                self.sched_status.setStyleSheet("color: #10B981; font-size: 13px;")
                self.toggle_btn.setText("停止")
            else:
                self.sched_status.setText("● 未启动")
                self.sched_status.setStyleSheet("color: #9CA3AF; font-size: 13px;")
                self.toggle_btn.setText("启动")
        except:
            pass
    
    def save_config(self):
        try:
            m = {0: "minute", 1: "hour", 2: "day"}
            self.api_client.put("/articles/generation-config", json={
                "count": self.gen_count.value(),
                "publish_count": self.pub_count.value(),
                "frequency_unit": m[self.freq_unit.currentIndex()],
                "frequency_value": self.freq_val.value()
            })
            ToastManager.success("配置保存成功", self)
        except Exception as e:
            ToastManager.error(f"保存失败: {str(e)}", self)
    
    def toggle_sched(self):
        try:
            r = self.api_client.get("/articles/scheduled-publish/status")
            if r.get("data", {}).get("running"):
                self.api_client.post("/articles/scheduled-publish/stop")
                ToastManager.success("定时发布已停止", self)
            else:
                self.api_client.post("/articles/scheduled-publish/start")
                ToastManager.success("定时发布已启动", self)
            self.load_sched_status()
        except Exception as e:
            ToastManager.error(f"操作失败: {str(e)}", self)
    
    def start_generate(self):
        if self.generate_thread and self.generate_thread.isRunning():
            # 调用后端取消 API
            try:
                self.api_client.post("/articles/generate/cancel")
            except:
                pass
            self.generate_thread.stop()
            self.generate_thread.wait()
            self.gen_btn.setText("开始生成")
            self.progress_widget.setVisible(False)
            ToastManager.info("已取消生成", self)
            return
        self.gen_btn.setText("取消")
        self.progress_widget.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_percent.setText("0%")
        self.progress_label.setText("准备中...")
        self.progress_icon.setText("⏳")
        self.generate_thread = GenerateThread(self.api_client, {
            "count": self.count_spin.value(),
            "use_knowledge_base": self.use_kb.isChecked()
        })
        self.generate_thread.progress.connect(self.on_progress)
        self.generate_thread.finished.connect(self.on_done)
        self.generate_thread.error.connect(self.on_err)
        self.generate_thread.start()
    
    def on_progress(self, d):
        t, c = d.get("total", 1), d.get("completed", 0)
        percent = int(c / t * 100)
        self.progress_bar.setValue(percent)
        self.progress_percent.setText(f"{percent}%")
        if c < t:
            self.progress_label.setText(f"正在生成第 {c + 1} 篇，共 {t} 篇")
        else:
            self.progress_label.setText(f"已完成 {c}/{t} 篇")
        self.progress_icon.setText("✨")
    
    def on_done(self, d):
        self.gen_btn.setText("开始生成")
        self.progress_widget.setVisible(False)
        self.load_articles()
        ToastManager.success(f"生成完成，共 {d.get('completed', 0)} 篇", self)
    
    def on_err(self, e):
        self.gen_btn.setText("开始生成")
        self.progress_widget.setVisible(False)
        ToastManager.error(f"生成失败: {e}", self)
    
    def publish_all(self):
        if confirm_dialog(self, "确认", "发布所有待发布文章？"):
            try:
                self.api_client.post("/articles/publish-all")
                self.load_articles()
                ToastManager.success("全部发布成功", self)
            except Exception as e:
                ToastManager.error(f"发布失败: {str(e)}", self)
    
    def view_article(self, a):
        try:
            r = self.api_client.get(f"/articles/{a['id']}")
            ArticleDialog(self, r.get("data", {}), False).exec()
        except:
            pass
    
    def edit_article(self, a):
        try:
            r = self.api_client.get(f"/articles/{a['id']}")
            dlg = ArticleDialog(self, r.get("data", a), True)
            if dlg.exec() == QDialog.Accepted:
                self.api_client.put(f"/articles/{a['id']}", json=dlg.get_data())
                self.load_articles()
                ToastManager.success("文章保存成功", self)
        except Exception as e:
            ToastManager.error(f"保存失败: {str(e)}", self)
    
    def pub_one(self, aid):
        try:
            self.api_client.post(f"/articles/{aid}/publish")
            self.load_articles()
            ToastManager.success("发布成功", self)
        except Exception as e:
            ToastManager.error(f"发布失败: {str(e)}", self)
    
    def del_one(self, aid):
        if confirm_dialog(self, "确认", "删除这篇文章？"):
            try:
                self.api_client.delete(f"/articles/{aid}")
                self.load_articles()
                ToastManager.success("删除成功", self)
            except Exception as e:
                ToastManager.error(f"删除失败: {str(e)}", self)
