"""
Sidebar Information Panel UI Component
"""
from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                            QGroupBox, QTextEdit, QListWidget, QPushButton,
                            QSplitter, QListWidgetItem)
from PyQt5.QtCore import QPropertyAnimation, QRect, Qt
from PyQt5.QtGui import QFont
from datetime import datetime
from collections import deque


class SidebarInfoPanel(QFrame):
    """Collapsible sidebar panel for conversion information"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_collapsed = True
        self.animation_duration = 200
        self.panel_width = 400  # 1/3 of typical 1200px width
        
        # Style
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f8f8;
                border: 1px solid #ccc;
                border-left: none;
            }
        """)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header
        self.header = QFrame()
        self.header.setFixedHeight(40)
        self.header.setStyleSheet("""
            QFrame {
                background-color: #e0e0e0;
                border-bottom: 1px solid #ccc;
            }
        """)
        
        self.header_layout = QHBoxLayout(self.header)
        self.title_label = QLabel("Conversion Information")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        
        # Content area with splitter
        self.content_splitter = QSplitter(Qt.Vertical)
        
        # Current conversion info
        self.current_group = QGroupBox("Current Conversion")
        self.current_layout = QVBoxLayout(self.current_group)
        self.current_info = QTextEdit()
        self.current_info.setReadOnly(True)
        self.current_layout.addWidget(self.current_info)
        
        # History
        self.history_group = QGroupBox("Conversion History (Last 10)")
        self.history_layout = QVBoxLayout(self.history_group)
        
        # History list
        self.history_list = QListWidget()
        self.history_list.setAlternatingRowColors(True)
        self.history_layout.addWidget(self.history_list)
        
        # Clear history button
        self.clear_history_btn = QPushButton("Clear History")
        self.clear_history_btn.clicked.connect(self.clear_history)
        self.history_layout.addWidget(self.clear_history_btn)
        
        # Add to splitter
        self.content_splitter.addWidget(self.current_group)
        self.content_splitter.addWidget(self.history_group)
        self.content_splitter.setSizes([200, 400])
        
        # Add to main layout
        self.main_layout.addWidget(self.header)
        self.main_layout.addWidget(self.content_splitter)
        
        # Animation
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(self.animation_duration)
        
        # History storage (max 10 items)
        self.history_items = deque(maxlen=10)
        
        # Initially collapsed
        self.setFixedWidth(0)
    
    def toggle(self):
        """Toggle sidebar visibility"""
        self.is_collapsed = not self.is_collapsed
        
        parent_rect = self.parent().rect()
        
        if self.is_collapsed:
            start_rect = QRect(0, 0, self.panel_width, parent_rect.height())
            end_rect = QRect(-self.panel_width, 0, self.panel_width, parent_rect.height())
        else:
            start_rect = QRect(-self.panel_width, 0, self.panel_width, parent_rect.height())
            end_rect = QRect(0, 0, self.panel_width, parent_rect.height())
            self.raise_()  # Bring to front
        
        self.setFixedWidth(self.panel_width)
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.start()
    
    def open(self):
        """Open sidebar if closed"""
        if self.is_collapsed:
            self.toggle()
    
    def set_current_info(self, text):
        """Update current conversion info"""
        self.current_info.setText(text)
    
    def add_history_item(self, item):
        """Add item to history"""
        self.history_items.append(item)
        self.update_history_display()
    
    def update_history_display(self):
        """Update history list display"""
        self.history_list.clear()
        
        for item in reversed(self.history_items):  # Show newest first
            # Create list item with formatted text
            text = f"{item.timestamp} - {item.filename} [{item.mode}]\n"
            text += f"Duration: {item.duration:.2f}s, Samples: {item.samples:,}\n"
            text += f"Size: {item.file_size:,} bytes - {item.status}"
            
            list_item = QListWidgetItem(text)
            if item.status != "Success":
                list_item.setForeground(Qt.red)
            
            self.history_list.addItem(list_item)
    
    def clear_history(self):
        """Clear conversion history"""
        self.history_items.clear()
        self.history_list.clear() 