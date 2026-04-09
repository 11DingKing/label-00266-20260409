"""
CMS 配置页面
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QScrollArea, QMessageBox, QCheckBox, QDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from gui.components import CardWithTitle, PageTitle, PrimaryButton, SecondaryButton, LinkButton, StyledComboBox, StyledCheckBox, ToastManager, confirm_dialog


class CMSConfigDialog(QDialog):
    def __init__(self, parent, api_client, config_id):
        super().__init__(parent)
        self.api_client = api_client
        self.config_id = config_id
        self.setWindowTitle("编辑 CMS 配置")
        self.setMinimumSize(500, 400)
        self.setStyleSheet("background-color: #FFFFFF;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        
        self.load_config()
        
        layout.addWidget(QLabel("平台"))
        self.platform_edit = QLineEdit()
        self.platform_edit.setText(self.config.get("platform", "").upper())
        self.platform_edit.setReadOnly(True)
        layout.addWidget(self.platform_edit)
        
        layout.addWidget(QLabel("网站地址"))
        self.url_edit = QLineEdit()
        self.url_edit.setText(self.config.get("api_url", ""))
        layout.addWidget(self.url_edit)
        
        layout.addWidget(QLabel("用户名"))
        self.user_edit = QLineEdit()
        self.user_edit.setText(self.config.get("username", ""))
        layout.addWidget(self.user_edit)
        
        layout.addWidget(QLabel("应用密码/令牌"))
        self.pass_edit = QLineEdit()
        self.pass_edit.setText(self.config.get("password", ""))
        layout.addWidget(self.pass_edit)
        
        active_row = QHBoxLayout()
        active_row.addWidget(QLabel("激活"))
        active_row.addStretch()
        self.active_check = StyledCheckBox()
        self.active_check.setChecked(self.config.get("is_active", False))
        active_row.addWidget(self.active_check)
        layout.addLayout(active_row)
        
        layout.addStretch()
        
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = SecondaryButton("取消")
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)
        save = PrimaryButton("保存")
        save.clicked.connect(self.save_config)
        btn_row.addWidget(save)
        layout.addLayout(btn_row)
    
    def load_config(self):
        try:
            r = self.api_client.get(f"/cms/config/{self.config_id}")
            self.config = r.get("data", {})
        except:
            self.config = {}
    
    def save_config(self):
        try:
            self.api_client.post("/cms/config", json={
                "platform": self.config.get("platform", "wordpress"),
                "api_url": self.url_edit.text().strip(),
                "username": self.user_edit.text().strip(),
                "password": self.pass_edit.text().strip(),
                "is_active": self.active_check.isChecked()
            })
            ToastManager.success("配置保存成功", self)
            self.accept()
        except Exception as e:
            ToastManager.error(f"保存失败: {str(e)}", self)


class CMSTab(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.init_ui()
        self.load_configs()
    
    def init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        layout.addWidget(PageTitle("CMS 配置", "配置 WordPress 或其他 CMS 平台"))
        
        # 操作区
        actions = QHBoxLayout()
        actions.setSpacing(20)
        
        # 添加配置
        add_card = CardWithTitle("添加配置")
        
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("平台"))
        r1.addStretch()
        self.platform_combo = StyledComboBox()
        self.platform_combo.addItem("WordPress", "wordpress")
        self.platform_combo.setFixedWidth(180)
        r1.addWidget(self.platform_combo)
        add_card.addLayout(r1)
        
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("网站地址"))
        r2.addStretch()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://your-site.com")
        self.url_edit.setFixedWidth(260)
        r2.addWidget(self.url_edit)
        add_card.addLayout(r2)
        
        r3 = QHBoxLayout()
        r3.addWidget(QLabel("用户名"))
        r3.addStretch()
        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("WordPress 用户名")
        self.user_edit.setFixedWidth(180)
        r3.addWidget(self.user_edit)
        add_card.addLayout(r3)
        
        r4 = QHBoxLayout()
        r4.addWidget(QLabel("应用密码/令牌"))
        r4.addStretch()
        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText("WordPress 应用密码")
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.pass_edit.setFixedWidth(180)
        r4.addWidget(self.pass_edit)
        add_card.addLayout(r4)
        
        r5 = QHBoxLayout()
        r5.addWidget(QLabel("立即激活"))
        r5.addStretch()
        self.active_check2 = StyledCheckBox()
        self.active_check2.setChecked(True)
        r5.addWidget(self.active_check2)
        add_card.addLayout(r5)
        
        btn_row = QHBoxLayout()
        test_btn = SecondaryButton("测试连接")
        test_btn.clicked.connect(self.test_connection)
        btn_row.addWidget(test_btn)
        save_btn = PrimaryButton("保存")
        save_btn.clicked.connect(self.save_config)
        btn_row.addWidget(save_btn)
        add_card.addLayout(btn_row)
        add_card.addStretch()
        actions.addWidget(add_card, 2)
        
        # 帮助
        help_card = CardWithTitle("获取应用密码")
        steps = [
            "1. 登录 WordPress 后台",
            "2. 进入「用户 → 个人资料」",
            "3. 滚动到「应用程序密码」",
            "4. 输入名称，点击添加",
            "5. 复制生成的密码",
        ]
        for s in steps:
            l = QLabel(s)
            l.setStyleSheet("color: #6B7280; font-size: 13px;")
            help_card.addWidget(l)
        help_card.addStretch()
        actions.addWidget(help_card, 1)
        
        layout.addLayout(actions)
        
        # 配置列表
        list_card = CardWithTitle("已配置的 CMS")
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "平台", "网站地址", "用户名", "状态", "操作"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 70)
        self.table.setColumnWidth(5, 150)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { border: 1px solid #E5E7EB; border-radius: 8px; background: #FFF; }
            QTableWidget::item { padding: 8px; color: #1F2937; }
            QTableWidget::item:alternate { background: #F9FAFB; }
        """)
        list_card.addWidget(self.table)
        layout.addWidget(list_card)
        
        scroll.setWidget(content)
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(scroll)
    
    def load_configs(self):
        try:
            r = self.api_client.get("/cms/config")
            configs = r.get("data", [])
            
            self.table.setRowCount(len(configs))
            for row, c in enumerate(configs):
                self.table.setItem(row, 0, QTableWidgetItem(str(c.get("id", ""))))
                
                pi = QTableWidgetItem(c.get("platform", "").upper())
                pi.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 1, pi)
                
                self.table.setItem(row, 2, QTableWidgetItem(c.get("api_url", "")))
                
                ui = QTableWidgetItem(c.get("username", ""))
                ui.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 3, ui)
                
                if c.get("is_active"):
                    si = QTableWidgetItem("已激活")
                    si.setForeground(QColor("#10B981"))
                else:
                    si = QTableWidgetItem("未激活")
                    si.setForeground(QColor("#9CA3AF"))
                si.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 4, si)
                
                w = QWidget()
                l = QHBoxLayout(w)
                l.setContentsMargins(4, 2, 4, 2)
                l.setSpacing(8)
                
                e = LinkButton("编辑")
                e.clicked.connect(lambda _, x=c.get("id"): self.edit_config(x))
                l.addWidget(e)
                
                t = LinkButton("测试")
                t.clicked.connect(lambda _, x=c: self.test_existing(x))
                l.addWidget(t)
                
                d = LinkButton("删除", "#EF4444")
                d.clicked.connect(lambda _, x=c.get("id"): self.delete_config(x))
                l.addWidget(d)
                l.addStretch()
                
                self.table.setCellWidget(row, 5, w)
                self.table.setRowHeight(row, 48)
        except:
            pass
    
    def test_connection(self):
        url = self.url_edit.text().strip()
        user = self.user_edit.text().strip()
        pwd = self.pass_edit.text().strip()
        if not url or not user or not pwd:
            ToastManager.warning("请填写完整信息", self)
            return
        try:
            r = self.api_client.post("/cms/test-connection", json={
                "platform": self.platform_combo.currentData(),
                "api_url": url, "username": user, "password": pwd
            })
            if r.get("success"):
                ToastManager.success("连接测试通过", self)
            else:
                ToastManager.error(r.get("message", "连接失败"), self)
        except Exception as e:
            ToastManager.error(f"测试失败: {str(e)}", self)
    
    def test_existing(self, config):
        try:
            r = self.api_client.post("/cms/test-connection", json={"config_id": config.get("id")})
            if r.get("success"):
                ToastManager.success("连接测试通过", self)
            else:
                ToastManager.error(r.get("message", "连接失败"), self)
        except Exception as e:
            ToastManager.error(f"测试失败: {str(e)}", self)
    
    def save_config(self):
        url = self.url_edit.text().strip()
        user = self.user_edit.text().strip()
        pwd = self.pass_edit.text().strip()
        if not url or not user or not pwd:
            ToastManager.warning("请填写完整信息", self)
            return
        try:
            self.api_client.post("/cms/config", json={
                "platform": self.platform_combo.currentData(),
                "api_url": url, "username": user, "password": pwd,
                "is_active": self.active_check2.isChecked()
            })
            self.url_edit.clear()
            self.user_edit.clear()
            self.pass_edit.clear()
            self.load_configs()
            ToastManager.success("配置保存成功", self)
        except Exception as e:
            ToastManager.error(f"保存失败: {str(e)}", self)
    
    def edit_config(self, config_id):
        dlg = CMSConfigDialog(self, self.api_client, config_id)
        if dlg.exec() == QDialog.Accepted:
            self.load_configs()
    
    def delete_config(self, config_id):
        if confirm_dialog(self, "确认", "删除这个配置？"):
            try:
                self.api_client.delete(f"/cms/config/{config_id}")
                self.load_configs()
                ToastManager.success("删除成功", self)
            except Exception as e:
                ToastManager.error(f"删除失败: {str(e)}", self)
