"""
系统配置页面
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QLineEdit, QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt

from gui.components import CardWithTitle, PageTitle, PrimaryButton, SecondaryButton, StyledSpinBox, ToastManager


class ConfigTab(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        layout.addWidget(PageTitle("系统设置", "配置 DeepSeek API 及其他参数"))
        
        # API 配置
        api_card = CardWithTitle("DeepSeek API 配置")
        
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("API Key"))
        r1.addStretch()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("sk-...")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setFixedWidth(300)
        r1.addWidget(self.api_key_edit)
        api_card.addLayout(r1)
        
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("API 地址"))
        r2.addStretch()
        self.api_url_edit = QLineEdit()
        self.api_url_edit.setPlaceholderText("https://api.deepseek.com")
        self.api_url_edit.setFixedWidth(300)
        r2.addWidget(self.api_url_edit)
        api_card.addLayout(r2)
        
        r3 = QHBoxLayout()
        r3.addWidget(QLabel("模型"))
        r3.addStretch()
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("deepseek-chat")
        self.model_edit.setFixedWidth(200)
        r3.addWidget(self.model_edit)
        api_card.addLayout(r3)
        
        r4 = QHBoxLayout()
        r4.addWidget(QLabel("超时时间"))
        r4.addStretch()
        self.timeout_spin = StyledSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setValue(60)
        r4.addWidget(self.timeout_spin)
        r4.addWidget(QLabel("秒"))
        api_card.addLayout(r4)
        
        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("状态"))
        status_row.addStretch()
        self.status_label = QLabel("● 未配置")
        self.status_label.setStyleSheet("color: #EF4444;")
        status_row.addWidget(self.status_label)
        api_card.addLayout(status_row)
        
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save_btn = PrimaryButton("保存配置")
        save_btn.clicked.connect(self.save_config)
        btn_row.addWidget(save_btn)
        api_card.addLayout(btn_row)
        
        layout.addWidget(api_card)
        
        # 帮助
        help_card = CardWithTitle("获取 API Key")
        steps = [
            "1. 访问 platform.deepseek.com",
            "2. 注册并登录账号",
            "3. 进入 API Keys 页面",
            "4. 创建新的 API Key",
            "5. 复制并保存到上方",
        ]
        for s in steps:
            l = QLabel(s)
            l.setStyleSheet("color: #6B7280; font-size: 13px;")
            help_card.addWidget(l)
        help_card.addStretch()
        layout.addWidget(help_card)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(scroll)
    
    def load_config(self):
        try:
            r = self.api_client.get("/config/deepseek")
            c = r.get("data", {})
            self.api_url_edit.setText(c.get("api_url", ""))
            self.model_edit.setText(c.get("model", "deepseek-chat"))
            self.timeout_spin.setValue(c.get("timeout", 60))
            
            if c.get("has_api_key"):
                self.status_label.setText("● 已配置")
                self.status_label.setStyleSheet("color: #10B981;")
            else:
                self.status_label.setText("● 未配置")
                self.status_label.setStyleSheet("color: #EF4444;")
        except:
            pass
    
    def save_config(self):
        try:
            data = {
                "api_url": self.api_url_edit.text().strip(),
                "model": self.model_edit.text().strip(),
                "timeout": self.timeout_spin.value()
            }
            key = self.api_key_edit.text().strip()
            if key:
                data["api_key"] = key
            else:
                data["api_key"] = ""  # 不更新 key
            
            self.api_client.put("/config/deepseek", json=data)
            self.api_key_edit.clear()
            self.load_config()
            ToastManager.success("配置已保存", self)
        except Exception as e:
            ToastManager.error(f"保存失败: {str(e)}", self)
