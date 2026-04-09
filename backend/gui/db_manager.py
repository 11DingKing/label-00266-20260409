"""
GUI数据库连接管理器
支持重连机制和状态恢复
"""
import logging
from typing import Optional, Callable, Any
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar

from app.core.database_sync import test_db_connection, init_sync_db, sync_engine
from gui.sync_service import SyncService

logger = logging.getLogger(__name__)


class ReconnectDialog(QDialog):
    """重连对话框"""
    
    def __init__(self, parent=None, max_attempts: int = 5):
        super().__init__(parent)
        self.max_attempts = max_attempts
        self.current_attempt = 0
        self.cancelled = False
        self.reconnect_success = False
        
        self.setWindowTitle("数据库连接中断")
        self.setMinimumSize(400, 200)
        self.setModal(True)
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)
        
        self.status_label = QLabel("数据库连接已中断，正在尝试重连...")
        self.status_label.setStyleSheet("font-size: 14px; color: #374151;")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.max_attempts)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("尝试 %v/%m")
        layout.addWidget(self.progress_bar)
        
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("font-size: 12px; color: #6B7280;")
        layout.addWidget(self.info_label)
        
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(8)
        
        self.retry_btn = QPushButton("立即重试")
        self.retry_btn.clicked.connect(self._on_retry_clicked)
        btn_layout.addWidget(self.retry_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_retry_clicked(self):
        """立即重试"""
        self._attempt_reconnect()
    
    def _on_cancel_clicked(self):
        """取消"""
        self.cancelled = True
        self.reject()
    
    def _attempt_reconnect(self) -> bool:
        """尝试重连"""
        self.current_attempt += 1
        self.progress_bar.setValue(self.current_attempt)
        self.status_label.setText(f"正在尝试重连 (第 {self.current_attempt} 次)...")
        self.info_label.setText(f"剩余尝试次数: {self.max_attempts - self.current_attempt}")
        
        try:
            if test_db_connection():
                self.reconnect_success = True
                self.status_label.setText("✓ 连接成功！")
                self.progress_bar.setStyleSheet("""
                    QProgressBar::chunk {
                        background-color: #10B981;
                    }
                """)
                QTimer.singleShot(1000, self.accept)
                return True
        except Exception as e:
            logger.error(f"重连尝试 {self.current_attempt} 失败: {e}")
        
        if self.current_attempt >= self.max_attempts:
            self.status_label.setText("✗ 重连失败，请检查数据库配置")
            self.info_label.setText("点击\"立即重试\"继续尝试，或点击\"取消\"退出")
            self.retry_btn.setEnabled(True)
        else:
            QTimer.singleShot(2000, self._attempt_reconnect)
        
        return False
    
    def start_reconnect(self):
        """开始重连流程"""
        self.current_attempt = 0
        self.reconnect_success = False
        self.cancelled = False
        self._attempt_reconnect()


class DBConnectionManager(QObject):
    """
    数据库连接管理器
    负责监控数据库连接状态，处理重连和状态恢复
    """
    
    connection_lost = Signal()
    connection_restored = Signal()
    connection_failed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_connected = False
        self._last_operation: Optional[Callable] = None
        self._last_operation_args = ()
        self._last_operation_kwargs = {}
        self._monitor_timer = QTimer(self)
        self._monitor_timer.timeout.connect(self._check_connection)
        self._monitor_interval = 30000  # 30秒检查一次
    
    def initialize(self) -> bool:
        """初始化数据库连接"""
        try:
            init_sync_db()
            self._is_connected = test_db_connection()
            
            if self._is_connected:
                logger.info("数据库连接初始化成功")
                self._monitor_timer.start(self._monitor_interval)
                return True
            else:
                logger.error("数据库连接测试失败")
                return False
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            self._is_connected = False
            return False
    
    def is_connected(self) -> bool:
        """获取当前连接状态"""
        return self._is_connected
    
    def _check_connection(self):
        """定期检查连接状态"""
        try:
            if not test_db_connection():
                logger.warning("数据库连接检测失败")
                self._handle_connection_lost()
        except Exception as e:
            logger.error(f"连接检查异常: {e}")
            self._handle_connection_lost()
    
    def _handle_connection_lost(self):
        """处理连接丢失"""
        self._is_connected = False
        self._monitor_timer.stop()
        self.connection_lost.emit()
        logger.warning("数据库连接已丢失")
    
    def execute_with_reconnect(
        self,
        operation: Callable,
        *args,
        parent_widget=None,
        **kwargs
    ) -> Any:
        """
        执行数据库操作，支持自动重连
        
        Args:
            operation: 要执行的操作函数
            *args: 操作参数
            parent_widget: 父窗口（用于显示重连对话框）
            **kwargs: 操作关键字参数
            
        Returns:
            操作结果，如果重连失败则返回 None
        """
        try:
            if not self._is_connected:
                if not self._try_reconnect(parent_widget):
                    return None
            
            self._last_operation = operation
            self._last_operation_args = args
            self._last_operation_kwargs = kwargs
            
            return operation(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"数据库操作失败: {e}")
            
            if "connection" in str(e).lower() or "operational" in str(e).lower():
                self._handle_connection_lost()
                
                if self._try_reconnect(parent_widget):
                    try:
                        return operation(*args, **kwargs)
                    except Exception as e2:
                        logger.error(f"重连后操作仍然失败: {e2}")
                        self.connection_failed.emit(str(e2))
                        return None
                else:
                    self.connection_failed.emit(str(e))
                    return None
            else:
                raise
    
    def _try_reconnect(self, parent_widget=None) -> bool:
        """
        尝试重连
        
        Args:
            parent_widget: 父窗口
            
        Returns:
            是否重连成功
        """
        if parent_widget:
            dialog = ReconnectDialog(parent_widget)
            dialog.start_reconnect()
            result = dialog.exec()
            
            if dialog.reconnect_success:
                self._is_connected = True
                self._monitor_timer.start(self._monitor_interval)
                self.connection_restored.emit()
                logger.info("数据库连接已恢复")
                
                if self._last_operation:
                    logger.info("准备恢复之前的操作状态")
                
                return True
            else:
                logger.warning("用户取消了重连")
                return False
        else:
            for attempt in range(3):
                try:
                    if test_db_connection():
                        self._is_connected = True
                        self._monitor_timer.start(self._monitor_interval)
                        self.connection_restored.emit()
                        logger.info("数据库连接已恢复（静默模式）")
                        return True
                except Exception as e:
                    logger.warning(f"静默重连尝试 {attempt + 1} 失败: {e}")
            
            return False
    
    def get_saved_operation(self) -> Optional[dict]:
        """获取保存的操作（用于状态恢复）"""
        if self._last_operation:
            return {
                "operation": self._last_operation,
                "args": self._last_operation_args,
                "kwargs": self._last_operation_kwargs
            }
        return None
    
    def clear_saved_operation(self):
        """清除保存的操作"""
        self._last_operation = None
        self._last_operation_args = ()
        self._last_operation_kwargs = {}
    
    def stop_monitor(self):
        """停止连接监控"""
        self._monitor_timer.stop()
        logger.info("数据库连接监控已停止")


db_manager = DBConnectionManager()
