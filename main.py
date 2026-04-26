import sys
import os
import json
import random
import copy
import traceback
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QButtonGroup, QRadioButton,
    QMessageBox, QInputDialog, QScrollArea, QFrame, QDialog, QGroupBox,
    QCheckBox, QComboBox, QGridLayout, QFileDialog, QStatusBar, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QTimer, QPoint, QMimeData
from PyQt5.QtGui import QDrag, QPixmap, QPainter, QPen, QColor, QDragEnterEvent, QDropEvent, QPainterPath

# ==================== 全局配置 ====================
DEBUG_MODE = True
STYLE_FOLDER = "styles"
DEFAULT_STYLE = "web20"
QUESTIONS_FOLDER = "questions"

# ==================== 样式管理 ====================
def init_style_folder():
    Path(STYLE_FOLDER).mkdir(exist_ok=True)
    styles = {
        "web10.qss": """
QWidget {font-family: "SimSun", sans-serif; font-size: 12px; color: #000; background-color: #C0C0C0;}
QMainWindow, QDialog, QWidget {background-color: #C0C0C0;}
QLabel#TitleLabel {font-size:14px; font-weight:bold; color:#FFF; background:#000080; border:2px solid #000; padding:4px;}
QPushButton {background:#C0C0C0; color:#000; border:2px solid #FFF; border-right-color:#808080; border-bottom-color:#808080; padding:4px 10px;}
QPushButton:pressed {border:2px solid #808080; border-right-color:#FFF; border-bottom-color:#FFF;}
QLineEdit, QTextEdit, QComboBox {background:#FFF; border:2px solid #000; padding:2px;}
QGroupBox {border:2px solid #000; margin-top:10px;}
QScrollBar:vertical {width:16px; background:#C0C0C0; border:2px solid #000;}
QScrollBar::handle:vertical {background:#C0C0C0; border:2px solid #FFF; border-right-color:#808080; border-bottom-color:#808080;}
* {border-radius:0px;}
""",
        "web20.qss": """
QWidget {font-family: "Microsoft YaHei", sans-serif; font-size:14px; color:#303133; background:#F5F7FA;}
QLabel#TitleLabel {font-size:20px; font-weight:bold; color:#FFF; background:#409EFF; padding:12px; border-radius:8px;}
QPushButton {background:#409EFF; color:#FFF; border:none; border-radius:8px; padding:10px 20px;}
QPushButton:hover {background:#66B1FF;}
QLineEdit, QTextEdit, QComboBox {border:1px solid #DCDFE6; border-radius:6px; padding:8px 12px; background:#FFF;}
QLineEdit:focus {border:1px solid #409EFF;}
QGroupBox {border:1px solid #E4E7ED; border-radius:8px; margin-top:16px;}
QScrollBar:vertical {width:8px; background:#F5F7FA; border-radius:4px;}
QScrollBar::handle:vertical {background:#C0C4CC; border-radius:4px;}
""",
        "web30.qss": """
QWidget {font-family: "Segoe UI", sans-serif; font-size:14px; color:#E0E0E0; background:#121212;}
QLabel#TitleLabel {font-size:20px; font-weight:bold; color:#FFF; background:#1E1E1E; padding:12px; border-radius:12px; border:1px solid #333;}
QPushButton {background:#2D2D2D; color:#FFF; border:none; border-radius:12px; padding:10px 20px;}
QPushButton:hover {background:#404040;}
QLineEdit, QTextEdit, QComboBox {background:#1E1E1E; color:#E0E0E0; border:1px solid #333; border-radius:8px; padding:8px 12px;}
QLineEdit:focus {border:1px solid #00C853;}
QGroupBox {border:1px solid #333; border-radius:12px; margin-top:16px;}
QScrollBar:vertical {width:8px; background:#121212;}
QScrollBar::handle:vertical {background:#444; border-radius:4px;}
"""
    }
    for filename, content in styles.items():
        path = os.path.join(STYLE_FOLDER, filename)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(content.strip())

def load_style(style_name: str) -> str:
    path = os.path.join(STYLE_FOLDER, f"{style_name}.qss")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

# ==================== 路径处理 ====================
def get_base_dir() -> str:
    try:
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))
    except:
        return os.getcwd()

def get_file_path(filename: str) -> str:
    base_dir = get_base_dir()
    file_path = os.path.join(base_dir, filename)
    Path(os.path.dirname(file_path)).mkdir(parents=True, exist_ok=True)
    return file_path

# ==================== 用户管理 ====================
USER_FILE = get_file_path("users.json")
def load_users() -> Dict[str, str]:
    default = {"student1": "123456", "teacher1": "654321"}
    try:
        if not os.path.exists(USER_FILE):
            save_users(default)
            return default
        with open(USER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else default
    except:
        return default

def save_users(users: dict) -> bool:
    try:
        if not isinstance(users, dict):
            return False
        with open(USER_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

# ==================== 题库加载 ====================
def load_all_questions_from_folder(folder: str = QUESTIONS_FOLDER) -> Dict[str, Any]:
    base_dir = get_base_dir()
    questions_dir = os.path.join(base_dir, folder)
    Path(questions_dir).mkdir(exist_ok=True)
    merged_questions = []
    json_files = list(Path(questions_dir).glob("*.json"))
    if not json_files:
        default_questions = [
            {"type": "选择题", "question": "1+1 等于多少？", "answer": "2", "options": ["1", "2", "3"]},
            {"type": "填空题", "question": "中国的首都是____。", "answer": "北京"},
            {"type": "简答题", "question": "请简述学习的重要性。", "answer": "（主观题）"},
            {"type": "拖拽配对", "question": "将动物与叫声配对", "pairs": [{"left": "狗", "right": "汪汪"}, {"left": "猫", "right": "喵喵"}]},
            {"type": "连线题", "question": "匹配国家与首都", "pairs": [{"left": "中国", "right": "北京"}, {"left": "日本", "right": "东京"}]}
        ]
        merged_questions = default_questions
    else:
        for json_path in json_files:
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "questions" in data:
                    qlist = data["questions"]
                elif isinstance(data, list):
                    qlist = data
                else:
                    continue
                if isinstance(qlist, list):
                    for q in qlist:
                        if "type" not in q:
                            q["type"] = "简答题"
                        if "question" not in q:
                            q["question"] = "（题目缺失）"
                    merged_questions.extend(qlist)
            except Exception as e:
                if DEBUG_MODE:
                    print(f"加载题库文件 {json_path} 失败: {e}")
    return {"questions": merged_questions}

# ==================== 结果对话框 ====================
class ResultDialog(QDialog):
    def __init__(self, title: str, text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)
        text_edit = QTextEdit()
        text_edit.setPlainText(text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

# ==================== 连线题组件 ====================
class VisibleMatchingWidget(QWidget):
    def __init__(self, pairs, parent=None, on_match_callback=None):
        super().__init__(parent)
        self.original_pairs = pairs
        self.on_match_callback = on_match_callback
        self.left_items = [p["left"] for p in pairs]
        self.right_items = [p["right"] for p in pairs]
        random.shuffle(self.right_items)

        self.matches = {}
        self.left_buttons = []
        self.right_buttons = []
        self.selected_left = None

        self.init_ui()
        self.setMinimumHeight(300)

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(60)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        for i, text in enumerate(self.left_items):
            btn = QPushButton(text)
            btn.setFixedSize(160, 45)
            btn.clicked.connect(lambda checked, idx=i: self.on_left_click(idx))
            left_layout.addWidget(btn)
            self.left_buttons.append(btn)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        for i, text in enumerate(self.right_items):
            btn = QPushButton(text)
            btn.setFixedSize(160, 45)
            btn.clicked.connect(lambda checked, idx=i: self.on_right_click(idx))
            right_layout.addWidget(btn)
            self.right_buttons.append(btn)

        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)
        self.setLayout(main_layout)
        self.button_positions = {}
        self.update_button_positions()

    def update_button_positions(self):
        for i, btn in enumerate(self.left_buttons):
            local_center = self.mapFromGlobal(btn.mapToGlobal(btn.rect().center()))
            self.button_positions[('left', i)] = local_center
        for i, btn in enumerate(self.right_buttons):
            local_center = self.mapFromGlobal(btn.mapToGlobal(btn.rect().center()))
            self.button_positions[('right', i)] = local_center

    def showEvent(self, event):
        super().showEvent(event)
        self.update_button_positions()
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_button_positions()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(103, 194, 58), 3, Qt.PenStyle.SolidLine)
        painter.setPen(pen)

        for left_idx, right_idx in self.matches.items():
            left_center = self.button_positions.get(('left', left_idx))
            right_center = self.button_positions.get(('right', right_idx))
            if left_center and right_center:
                path = QPainterPath()
                path.moveTo(left_center)
                # 修复：将浮点数转为整数
                ctrl1 = QPoint(
                    int(left_center.x() + (right_center.x() - left_center.x()) * 0.3),
                    left_center.y()
                )
                ctrl2 = QPoint(
                    int(left_center.x() + (right_center.x() - left_center.x()) * 0.7),
                    right_center.y()
                )
                path.cubicTo(ctrl1, ctrl2, right_center)
                painter.drawPath(path)
                painter.setBrush(QColor(103, 194, 58))
                painter.drawEllipse(right_center, 5, 5)
        painter.end()

    def get_match_text_state(self) -> Dict[str, str]:
        state = {}
        for left_idx, right_idx in self.matches.items():
            state[self.left_items[left_idx]] = self.right_items[right_idx]
        return state

    def set_match_text_state(self, state: Dict[str, str]):
        for left_idx in list(self.matches.keys()):
            right_idx = self.matches[left_idx]
            self.left_buttons[left_idx].setStyleSheet("")
            self.right_buttons[right_idx].setStyleSheet("")
        self.matches.clear()

        for left_text, right_text in state.items():
            left_idx = next((i for i, lt in enumerate(self.left_items) if lt == left_text), None)
            if left_idx is None:
                continue
            right_idx = next((i for i, rt in enumerate(self.right_items) if rt == right_text), None)
            if right_idx is None:
                continue
            self.matches[left_idx] = right_idx
            self.left_buttons[left_idx].setStyleSheet("background-color: #67C23A;")
            self.right_buttons[right_idx].setStyleSheet("background-color: #67C23A;")
        self.selected_left = None
        self.update()
        if self.on_match_callback:
            self.on_match_callback(self.get_match_text_state())

    def on_left_click(self, idx):
        if idx in self.matches:
            right_idx = self.matches[idx]
            reply = QMessageBox.question(self, "取消配对", f"是否取消与“{self.right_items[right_idx]}”的配对？",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                del self.matches[idx]
                self.left_buttons[idx].setStyleSheet("")
                self.right_buttons[right_idx].setStyleSheet("")
                self.selected_left = None
                for btn in self.left_buttons:
                    btn.setStyleSheet("")
                self.update()
                if self.on_match_callback:
                    self.on_match_callback(self.get_match_text_state())
                main_win = self.window()
                if main_win is not None and hasattr(main_win, 'status_bar'):
                    main_win.status_bar.clearMessage()
        else:
            self.selected_left = idx
            for i, btn in enumerate(self.left_buttons):
                btn.setStyleSheet("background-color: #E6A23C;" if i == idx else "")
            for btn in self.right_buttons:
                btn.setStyleSheet("")

    def on_right_click(self, idx):
        if self.selected_left is None:
            for left_idx, right_idx in self.matches.items():
                if right_idx == idx:
                    reply = QMessageBox.question(self, "取消配对", f"是否取消与“{self.left_items[left_idx]}”的配对？",
                                                 QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        del self.matches[left_idx]
                        self.left_buttons[left_idx].setStyleSheet("")
                        self.right_buttons[idx].setStyleSheet("")
                        self.selected_left = None
                        self.update()
                        if self.on_match_callback:
                            self.on_match_callback(self.get_match_text_state())
                        main_win = self.window()
                        if main_win is not None and hasattr(main_win, 'status_bar'):
                            main_win.status_bar.clearMessage()
                    return
            QMessageBox.warning(self, "提示", "请先点击左侧选项")
            return

        left_idx = self.selected_left
        if left_idx in self.matches:
            QMessageBox.warning(self, "提示", "该左侧项已经配对，如需修改请先取消")
            self.selected_left = None
            self.left_buttons[left_idx].setStyleSheet("")
            return
        for l_idx, r_idx in self.matches.items():
            if r_idx == idx:
                QMessageBox.warning(self, "提示", "该右侧项已经与其他项配对")
                self.selected_left = None
                self.left_buttons[left_idx].setStyleSheet("")
                return

        correct_right = self.original_pairs[left_idx]["right"]
        if self.right_items[idx] == correct_right:
            self.matches[left_idx] = idx
            self.left_buttons[left_idx].setStyleSheet("background-color: #67C23A;")
            self.right_buttons[idx].setStyleSheet("background-color: #67C23A;")
            self.selected_left = None
            self.update()
            if len(self.matches) == len(self.original_pairs):
                main_win = self.window()
                if main_win is not None and hasattr(main_win, 'status_bar'):
                    main_win.status_bar.showMessage("连线全部正确！", 3000)
            if self.on_match_callback:
                self.on_match_callback(self.get_match_text_state())
        else:
            QMessageBox.warning(self, "错误", "配对错误，再试试看")
            self.right_buttons[idx].setStyleSheet("background-color: #F56C6C;")
            QTimer.singleShot(300, lambda: self.right_buttons[idx].setStyleSheet(""))

# ==================== 拖拽配对组件 ====================
class DraggableLabel(QLabel):
    def __init__(self, text, left_key, parent=None):
        super().__init__(text, parent)
        self.left_key = left_key
        self.setFixedSize(120, 40)
        self.setStyleSheet("background: #409EFF; border-radius: 8px; padding: 8px; color: white;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drag_start_pos = None
        self.paired = False

    def set_paired(self, paired: bool):
        self.paired = paired
        if paired:
            self.setStyleSheet("background: #A0C4FF; border-radius: 8px; padding: 8px; color: #666;")
            self.setEnabled(False)
        else:
            self.setStyleSheet("background: #409EFF; border-radius: 8px; padding: 8px; color: white;")
            self.setEnabled(True)

    def mousePressEvent(self, event):
        if self.paired or event.button() != Qt.MouseButton.LeftButton:
            return
        self.drag_start_pos = event.pos()

    def mouseDoubleClickEvent(self, event):
        if self.paired:
            parent_widget = self.parent()
            if parent_widget is not None and hasattr(parent_widget, 'cancel_pair'):
                parent_widget.cancel_pair(self.left_key) # type: ignore

    def mouseMoveEvent(self, event):
        if self.paired or not (event.buttons() == Qt.MouseButton.LeftButton and self.drag_start_pos):
            return
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.left_key)
        drag.setMimeData(mime_data)
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)
        drag.exec_(Qt.DropAction.MoveAction)

class DropZone(QLabel):
    def __init__(self, target_text, left_to_right, parent=None, on_match_callback=None):
        super().__init__(parent)
        self.target_text = target_text
        self.left_to_right = left_to_right
        self.on_match_callback = on_match_callback
        self.setFixedSize(120, 40)
        self.setStyleSheet("background: #F56C6C; border: 2px dashed #909399; border-radius: 8px;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText(target_text)
        self.setAcceptDrops(True)
        self.matched = False
        self.matched_left_key = None

    def dragEnterEvent(self, event: QDragEnterEvent):
        mime = event.mimeData()
        if mime is not None and mime.hasText() and not self.matched:
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if self.matched:
            event.ignore()
            return
        mime = event.mimeData()
        if mime is None:
            return
        dragged_key = mime.text()
        correct_right = self.left_to_right.get(dragged_key)
        if correct_right == self.target_text:
            self.matched = True
            self.matched_left_key = dragged_key
            self.setStyleSheet("background: #67C23A; border: 2px solid #529B2E; border-radius: 8px;")
            event.acceptProposedAction()
            if self.on_match_callback:
                self.on_match_callback(dragged_key, self.target_text)
        else:
            self.setText("错误匹配")
            QTimer.singleShot(500, lambda: self.setText(self.target_text))

    def reset(self):
        self.matched = False
        self.matched_left_key = None
        self.setStyleSheet("background: #F56C6C; border: 2px dashed #909399; border-radius: 8px;")
        self.setText(self.target_text)

class DragDropContainer(QWidget):
    def __init__(self, pairs, on_state_changed, parent=None):
        super().__init__(parent)
        self.pairs = pairs
        self.on_state_changed = on_state_changed
        self.left_to_right = {p["left"]: p["right"] for p in pairs}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        h_layout = QHBoxLayout()

        left_area = QWidget()
        right_area = QWidget()
        left_layout = QVBoxLayout(left_area)
        right_layout = QVBoxLayout(right_area)

        left_items = list(self.left_to_right.keys())
        random.shuffle(left_items)
        self.drag_labels = []
        for item in left_items:
            lbl = DraggableLabel(item, item, parent=self)
            left_layout.addWidget(lbl)
            self.drag_labels.append(lbl)

        self.drop_zones = []
        for p in self.pairs:
            zone = DropZone(p["right"], self.left_to_right, parent=self, on_match_callback=self.on_match)
            right_layout.addWidget(zone)
            self.drop_zones.append(zone)

        h_layout.addWidget(left_area)
        h_layout.addWidget(right_area)
        layout.addLayout(h_layout)

        reset_btn = QPushButton("重置本题配对")
        reset_btn.clicked.connect(lambda: self.reset_all(emit_signal=True))
        layout.addWidget(reset_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def on_match(self, left_key, right_text):
        for lbl in self.drag_labels:
            if lbl.left_key == left_key and not lbl.paired:
                lbl.set_paired(True)
                break
        self.save_state()
        if all(zone.matched for zone in self.drop_zones):
            main_win = self.window()
            if main_win is not None and hasattr(main_win, 'status_bar'):
                main_win.status_bar.showMessage("拖拽配对全部正确！", 3000)

    def cancel_pair(self, left_key):
        target_lbl = next((lbl for lbl in self.drag_labels if lbl.left_key == left_key and lbl.paired), None)
        if target_lbl is None:
            return
        target_zone = next((zone for zone in self.drop_zones if zone.matched_left_key == left_key), None)
        if target_zone is not None:
            target_zone.reset()
            target_lbl.set_paired(False)
            self.save_state()
            main_win = self.window()
            if main_win is not None and hasattr(main_win, 'status_bar'):
                main_win.status_bar.clearMessage()

    def reset_all(self, emit_signal=True):
        for lbl in self.drag_labels:
            lbl.set_paired(False)
        for zone in self.drop_zones:
            zone.reset()
        if emit_signal:
            self.save_state()
        main_win = self.window()
        if main_win is not None and hasattr(main_win, 'status_bar'):
            main_win.status_bar.showMessage("已重置所有配对", 2000)

    def save_state(self):
        matched_pairs = []
        for zone in self.drop_zones:
            if zone.matched and zone.matched_left_key:
                matched_pairs.append({"left": zone.matched_left_key, "right": zone.target_text})
        state = {
            "type": "drag",
            "matched_pairs": matched_pairs,
            "complete": len(matched_pairs) == len(self.drop_zones)
        }
        if self.on_state_changed:
            self.on_state_changed(state)

    def get_state(self):
        matched_pairs = []
        for zone in self.drop_zones:
            if zone.matched and zone.matched_left_key:
                matched_pairs.append({"left": zone.matched_left_key, "right": zone.target_text})
        return {
            "type": "drag",
            "matched_pairs": matched_pairs,
            "complete": len(matched_pairs) == len(self.drop_zones)
        }

    def set_state(self, state):
        if not isinstance(state, dict) or "matched_pairs" not in state:
            return
        self.reset_all(emit_signal=False)
        for pair in state["matched_pairs"]:
            left = pair["left"]
            right = pair["right"]
            for lbl in self.drag_labels:
                if lbl.left_key == left and not lbl.paired:
                    lbl.set_paired(True)
                    break
            for zone in self.drop_zones:
                if zone.target_text == right and not zone.matched:
                    zone.matched = True
                    zone.matched_left_key = left
                    zone.setStyleSheet("background: #67C23A; border: 2px solid #529B2E; border-radius: 8px;")
                    break
        self.save_state()

# ==================== 登录窗口 ====================
class LoginDialog(QDialog):
    def __init__(self, style_content: str) -> None:
        super().__init__()
        self.setWindowTitle("答题器 - 登录")
        self.setFixedSize(420, 380)
        self.setStyleSheet(style_content)
        self.users = load_users()
        self.lock = False
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40,40,40,40)
        title = QLabel("答题器登录")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.user = QLineEdit()
        self.user.setPlaceholderText("用户名")
        self.pwd = QLineEdit()
        self.pwd.setPlaceholderText("密码")
        self.pwd.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("用户名"))
        layout.addWidget(self.user)
        layout.addWidget(QLabel("密码"))
        layout.addWidget(self.pwd)

        btn_layout = QHBoxLayout()
        login = QPushButton("登录")
        add = QPushButton("添加账号")
        login.clicked.connect(self.do_login)
        add.clicked.connect(self.add_user)
        btn_layout.addWidget(login)
        btn_layout.addWidget(add)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def do_login(self) -> None:
        if self.lock:
            return
        self.lock = True
        QTimer.singleShot(1000, lambda: setattr(self, 'lock', False))
        u, p = self.user.text().strip(), self.pwd.text().strip()
        if self.users.get(u) == p:
            self.accept()
        else:
            QMessageBox.warning(self, "提示", "账号或密码错误")

    def add_user(self) -> None:
        u, ok = QInputDialog.getText(self, "添加", "用户名")
        if not ok or not u:
            return
        p, ok = QInputDialog.getText(self, "添加", "密码", QLineEdit.Password)
        if ok and len(p)>=6:
            if u in self.users:
                QMessageBox.warning(self, "提示", "用户已存在")
                return
            self.users[u] = p
            save_users(self.users)
            QMessageBox.information(self, "成功", "添加完成")

# ==================== 主窗口 ====================
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("答题器 - 主界面")
        self.setMinimumSize(1000, 700)

        self.original_bank = load_all_questions_from_folder(QUESTIONS_FOLDER)
        self.current_bank = copy.deepcopy(self.original_bank)
        self.idx = 0
        self.answers: Dict[int, Any] = {}
        self.widgets: List[Any] = []
        self.fun_mode = False

        self.init_ui()
        self.load_question()

    def init_ui(self) -> None:
        w = QWidget()
        self.setCentralWidget(w)
        lay = QVBoxLayout(w)
        lay.setSpacing(20)
        lay.setContentsMargins(30,30,30,30)

        title_layout = QHBoxLayout()
        self.title_label = QLabel("答题器")
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(self.title_label, 1)

        top = QHBoxLayout()
        self.progress = QLabel()
        top.addWidget(self.progress, 1)

        self.style_combo = QComboBox()
        self.style_combo.addItems(["Web 1.0", "Web 2.0", "Web 3.0"])
        self.style_combo.setCurrentText("Web 2.0")
        self.style_combo.currentTextChanged.connect(self.change_style)
        top.addWidget(QLabel("切换风格："))
        top.addWidget(self.style_combo)

        self.fun = QCheckBox("趣味模式")
        self.fun.setChecked(False)
        self.fun.stateChanged.connect(self.switch_fun)
        top.addWidget(self.fun)

        self.reset_progress_btn = QPushButton("重置所有答案")
        self.reset_progress_btn.clicked.connect(self.reset_all_answers)
        top.addWidget(self.reset_progress_btn)

        lay.addLayout(title_layout)
        lay.addLayout(top)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.q_frame = QWidget()
        self.q_lay = QVBoxLayout(self.q_frame)
        self.scroll.setWidget(self.q_frame)
        lay.addWidget(self.scroll, 1)

        btn_lay = QHBoxLayout()
        self.prev = QPushButton("上一题")
        self.next = QPushButton("下一题")
        self.submit = QPushButton("提交答案")
        self.prev.clicked.connect(self.to_prev)
        self.next.clicked.connect(self.to_next)
        self.submit.clicked.connect(self.do_submit)
        btn_lay.addWidget(self.prev)
        btn_lay.addWidget(self.next)
        btn_lay.addStretch()
        btn_lay.addWidget(self.submit)
        lay.addLayout(btn_lay)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.change_style("Web 2.0")

        scroll_bar = self.scroll.verticalScrollBar()
        if scroll_bar is not None:
            scroll_bar.valueChanged.connect(self.on_scroll)

    def on_scroll(self, value):
        if hasattr(self, 'matching_widget') and self.matching_widget and self.matching_widget.isVisible():
            self.matching_widget.update()

    def change_style(self, name: str) -> None:
        style_map = {"Web 1.0":"web10", "Web 2.0":"web20", "Web 3.0":"web30"}
        qss = load_style(style_map[name])
        self.setStyleSheet(qss)

    def switch_fun(self, state: int) -> None:
        self.save_ans()
        new_mode = (state == 2)
        if new_mode == self.fun_mode:
            return
        if new_mode:
            reply = QMessageBox.question(self, "趣味模式", "趣味模式将打乱题目顺序，并重置当前进度。是否继续？",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                self.fun.setChecked(False)
                return
            self.fun_mode = True
            shuffled = copy.deepcopy(self.original_bank)
            random.shuffle(shuffled['questions'])
            self.current_bank = shuffled
            self.answers = {}
            self.idx = 0
        else:
            self.fun_mode = False
            self.current_bank = copy.deepcopy(self.original_bank)
            self.answers = {}
            self.idx = 0
        self.load_question()

    def reset_all_answers(self):
        reply = QMessageBox.question(self, "重置进度", "确定要清空所有已答记录吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.answers = {}
            self.idx = 0
            self.load_question()
            self.status_bar.showMessage("已重置所有答案", 2000)

    def load_question(self) -> None:
        for i in reversed(range(self.q_lay.count())):
            item = self.q_lay.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
        self.widgets.clear()
        self.matching_widget = None

        total = len(self.current_bank['questions'])
        if total == 0:
            self.progress.setText("无题目，请将题库JSON文件放入 questions 文件夹")
            return
        self.idx = max(0, min(self.idx, total-1))
        self.progress.setText(f"第 {self.idx+1}/{total} 题")
        q = self.current_bank['questions'][self.idx]

        try:
            qtype = q.get('type', '简答题')
            if 'question' not in q:
                lab = QLabel(f"【错误】题目缺少 question 字段")
                lab.setWordWrap(True)
                lab.setStyleSheet("font-size:16px; font-weight:500; color:red;")
                self.q_lay.addWidget(lab)
                self.widgets.append(("error",))
                return

            lab = QLabel(f"【{qtype}】{q['question']}")
            lab.setWordWrap(True)
            lab.setStyleSheet("font-size:16px; font-weight:500;")
            self.q_lay.addWidget(lab)

            if qtype == "选择题":
                if 'options' not in q or not isinstance(q['options'], list):
                    err = QLabel("选择题缺少 options 字段")
                    self.q_lay.addWidget(err)
                    self.widgets.append(("error",))
                else:
                    self.make_choice(q['options'])
            elif qtype == "填空题":
                self.make_fill()
            elif qtype == "简答题":
                self.make_essay()
            elif qtype == "拖拽配对":
                if 'pairs' not in q or not isinstance(q['pairs'], list):
                    err = QLabel("拖拽配对题缺少 pairs 字段")
                    self.q_lay.addWidget(err)
                    self.widgets.append(("error",))
                else:
                    self.make_drag_drop(q['pairs'])
            elif qtype == "连线题":
                if 'pairs' not in q or not isinstance(q['pairs'], list):
                    err = QLabel("连线题缺少 pairs 字段")
                    self.q_lay.addWidget(err)
                    self.widgets.append(("error",))
                else:
                    self.make_matching(q['pairs'])
            else:
                self.make_essay()
            self.restore_ans()
        except Exception as e:
            if DEBUG_MODE:
                traceback.print_exc()
            err_label = QLabel(f"渲染题目时出错: {str(e)}")
            err_label.setStyleSheet("color:red;")
            self.q_lay.addWidget(err_label)
            self.widgets.append(("error",))

    def make_choice(self, opts: List[str]) -> None:
        g = QGroupBox("请选择")
        l = QVBoxLayout(g)
        grp = QButtonGroup(self)
        btns = []
        for o in opts:
            r = QRadioButton(o)
            r.setProperty("option_value", o.strip())
            l.addWidget(r)
            grp.addButton(r)
            btns.append(r)
        self.q_lay.addWidget(g)
        self.widgets.append(("c", grp, btns))

    def make_fill(self) -> None:
        e = QLineEdit()
        e.setPlaceholderText("答案")
        self.q_lay.addWidget(e)
        self.widgets.append(("f", e))

    def make_essay(self) -> None:
        e = QTextEdit()
        e.setPlaceholderText("输入回答")
        e.setMinimumHeight(220)
        self.q_lay.addWidget(e)
        self.widgets.append(("e", e))

    def make_drag_drop(self, pairs: List[Dict]) -> None:
        container = DragDropContainer(pairs, on_state_changed=self.save_current_drag_state, parent=self)
        self.q_lay.addWidget(container)
        self.widgets.append(("drag", container))

    def save_current_drag_state(self, state: dict):
        self.answers[self.idx] = state

    def make_matching(self, pairs: List[Dict]) -> None:
        self.matching_widget = VisibleMatchingWidget(pairs, on_match_callback=self.save_matching_state)
        self.q_lay.addWidget(self.matching_widget)
        self.widgets.append(("matching", self.matching_widget))

    def save_matching_state(self, text_state: Dict[str, str]):
        if self.matching_widget is not None:
            self.answers[self.idx] = {
                "type": "matching",
                "state": text_state,
                "complete": len(text_state) == len(self.matching_widget.original_pairs)
            }

    def save_ans(self) -> None:
        if not self.widgets:
            return
        t = self.widgets[0][0]
        try:
            if t == "c":
                grp = self.widgets[0][1]
                checked = grp.checkedButton()
                ans = checked.property("option_value") if checked else ""
                self.answers[self.idx] = ans
            elif t == "f":
                ans = self.widgets[0][1].text().strip()
                self.answers[self.idx] = ans
            elif t == "e":
                ans = self.widgets[0][1].toPlainText().strip()
                self.answers[self.idx] = ans
            elif t == "drag":
                container = self.widgets[0][1]
                state = container.get_state()
                self.answers[self.idx] = state
            elif t == "matching":
                if self.matching_widget is not None:
                    cur_state = self.matching_widget.get_match_text_state()
                    self.answers[self.idx] = {
                        "type": "matching",
                        "state": cur_state,
                        "complete": len(cur_state) == len(self.matching_widget.original_pairs)
                    }
        except Exception as e:
            if DEBUG_MODE:
                print(f"保存答案出错: {e}")

    def restore_ans(self) -> None:
        if self.idx not in self.answers:
            return
        ans = self.answers[self.idx]
        if not self.widgets:
            return
        t = self.widgets[0][0]
        try:
            if t == "c":
                for btn in self.widgets[0][2]:
                    if btn.property("option_value") == ans:
                        btn.setChecked(True)
                        break
            elif t == "f":
                self.widgets[0][1].setText(ans)
            elif t == "e":
                self.widgets[0][1].setPlainText(ans)
            elif t == "drag":
                container = self.widgets[0][1]
                container.set_state(ans)
            elif t == "matching":
                if self.matching_widget is not None and isinstance(ans, dict) and "state" in ans:
                    self.matching_widget.set_match_text_state(ans["state"])
        except Exception as e:
            if DEBUG_MODE:
                print(f"恢复答案出错: {e}")

    def to_prev(self) -> None:
        self.save_ans()
        self.idx -= 1
        self.load_question()

    def to_next(self) -> None:
        self.save_ans()
        self.idx += 1
        self.load_question()

    def normalize_answer(self, s: str) -> str:
        if not isinstance(s, str):
            return ""
        s = s.strip().lower()
        s = re.sub(r'[，,。？!；;]', '', s)
        return s

    def do_submit(self) -> None:
        self.save_ans()
        correct_count = 0
        total_obj = 0
        details = []
        for i, q in enumerate(self.current_bank['questions']):
            ans = self.answers.get(i, None)
            qtype = q.get('type', '简答题')
            if qtype == "选择题":
                std = q.get("answer", "")
                if ans is not None and isinstance(ans, str):
                    total_obj += 1
                    if ans.strip() == std.strip():
                        correct_count += 1
                        details.append(f"{i+1}. ✓ (答案: {ans})")
                    else:
                        details.append(f"{i+1}. ✗ (你的答案: {ans}, 标准: {std})")
                else:
                    details.append(f"{i+1}. ✗ (未作答)")
            elif qtype == "填空题":
                std = q.get("answer", "")
                if ans is not None and isinstance(ans, str):
                    total_obj += 1
                    if self.normalize_answer(ans) == self.normalize_answer(std):
                        correct_count += 1
                        details.append(f"{i+1}. ✓ (答案: {ans})")
                    else:
                        details.append(f"{i+1}. ✗ (你的答案: {ans}, 标准: {std})")
                else:
                    details.append(f"{i+1}. ✗ (未作答)")
            elif qtype in ["拖拽配对", "连线题"]:
                if ans is not None and isinstance(ans, dict) and ans.get("complete", False):
                    correct_count += 1
                    total_obj += 1
                    details.append(f"{i+1}. ✓ 趣味题正确")
                else:
                    details.append(f"{i+1}. ✗ 趣味题未完成或错误")
            else:
                user_ans = ans if isinstance(ans, str) else "未作答"
                details.append(f"{i+1}. 简答: {user_ans}")
        msg = f"客观及趣味题正确数: {correct_count}/{total_obj}\n\n"
        msg += "\n".join(details)
        dlg = ResultDialog("提交结果", msg, self)
        dlg.exec_()

# ==================== 入口 ====================
def main() -> None:
    try:
        init_style_folder()
        default_style_content = load_style(DEFAULT_STYLE)
        app = QApplication(sys.argv)
        login = LoginDialog(default_style_content)
        if login.exec_() == QDialog.DialogCode.Accepted:
            win = MainWindow()
            win.show()
            sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(None, "错误", f"答题器启动失败: {str(e)}\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()
