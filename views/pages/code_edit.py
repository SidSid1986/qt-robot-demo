from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QPushButton, QPlainTextEdit, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor, QPainter
import re


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return self.code_editor.line_number_area_width(), 0

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)


class MultiLanguageHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # ========== 通用规则 ==========

        # 注释格式
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(0, 128, 0))  # 绿色

        # 字符串格式
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(163, 21, 21))  # 红色

        # 数字格式
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(128, 0, 128))  # 紫色

        # 函数格式
        function_format = QTextCharFormat()
        function_format.setForeground(QColor(0, 100, 0))  # 深绿色
        function_format.setFontItalic(True)

        # ========== Python 高亮规则 ==========
        python_keyword_format = QTextCharFormat()
        python_keyword_format.setForeground(QColor(0, 0, 255))  # 蓝色
        python_keyword_format.setFontWeight(QFont.Bold)

        python_keywords = [
            'def', 'class', 'if', 'elif', 'else', 'for', 'while', 'import', 'from',
            'as', 'return', 'try', 'except', 'finally', 'with', 'lambda', 'yield',
            'global', 'nonlocal', 'assert', 'pass', 'break', 'continue', 'del',
            'and', 'or', 'not', 'is', 'in', 'None', 'True', 'False'
        ]

        for word in python_keywords:
            pattern = r'\b' + word + r'\b'
            self.highlighting_rules.append((re.compile(pattern), python_keyword_format))

        # Python 注释
        self.highlighting_rules.append((re.compile(r'#[^\n]*'), comment_format))

        # Python 字符串 (单引号、双引号、三引号)
        self.highlighting_rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))
        self.highlighting_rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        self.highlighting_rules.append((re.compile(r"'''[^'\\]*(\\.[^'\\]*)*'''"), string_format))
        self.highlighting_rules.append((re.compile(r'"""[^"\\]*(\\.[^"\\]*)*"""'), string_format))

        # Python 函数定义
        self.highlighting_rules.append((re.compile(r'\bdef\s+(\w+)'), function_format))

        # Python 数字
        self.highlighting_rules.append((re.compile(r'\b[0-9]+\b'), number_format))
        self.highlighting_rules.append((re.compile(r'\b[0-9]*\.[0-9]+\b'), number_format))

        # ========== JavaScript 高亮规则 ==========
        js_keyword_format = QTextCharFormat()
        js_keyword_format.setForeground(QColor(155, 0, 155))  # 紫色
        js_keyword_format.setFontWeight(QFont.Bold)

        js_keywords = [
            'function', 'var', 'let', 'const', 'if', 'else', 'for', 'while', 'do',
            'switch', 'case', 'break', 'continue', 'return', 'try', 'catch', 'finally',
            'throw', 'new', 'delete', 'typeof', 'instanceof', 'void', 'this', 'super',
            'class', 'extends', 'import', 'export', 'default', 'async', 'await',
            'true', 'false', 'null', 'undefined', 'NaN', 'Infinity'
        ]

        for word in js_keywords:
            pattern = r'\b' + word + r'\b'
            self.highlighting_rules.append((re.compile(pattern), js_keyword_format))

        # JavaScript 注释
        self.highlighting_rules.append((re.compile(r'//[^\n]*'), comment_format))
        self.highlighting_rules.append((re.compile(r'/\*.*?\*/', re.DOTALL), comment_format))

        # JavaScript 字符串
        self.highlighting_rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))
        self.highlighting_rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        self.highlighting_rules.append((re.compile(r'`[^`\\]*(\\.[^`\\]*)*`'), string_format))

        # JavaScript 函数
        self.highlighting_rules.append((re.compile(r'\bfunction\s+(\w+)'), function_format))

        # JavaScript 数字
        self.highlighting_rules.append((re.compile(r'\b[0-9]+\b'), number_format))
        self.highlighting_rules.append((re.compile(r'\b[0-9]*\.[0-9]+\b'), number_format))

        # ========== Java 高亮规则 ==========
        java_keyword_format = QTextCharFormat()
        java_keyword_format.setForeground(QColor(0, 100, 200))  # 蓝色
        java_keyword_format.setFontWeight(QFont.Bold)

        java_keywords = [
            'public', 'private', 'protected', 'class', 'interface', 'enum', 'void',
            'static', 'final', 'abstract', 'extends', 'implements', 'new', 'this',
            'super', 'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'break',
            'continue', 'return', 'try', 'catch', 'finally', 'throw', 'throws',
            'import', 'package', 'native', 'synchronized', 'volatile', 'transient',
            'instanceof', 'assert', 'const', 'goto', 'byte', 'short', 'int', 'long',
            'float', 'double', 'char', 'boolean', 'true', 'false', 'null'
        ]

        for word in java_keywords:
            pattern = r'\b' + word + r'\b'
            self.highlighting_rules.append((re.compile(pattern), java_keyword_format))

        # Java 注释
        self.highlighting_rules.append((re.compile(r'//[^\n]*'), comment_format))
        self.highlighting_rules.append((re.compile(r'/\*.*?\*/', re.DOTALL), comment_format))

        # Java 字符串
        self.highlighting_rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))

        # Java 函数
        self.highlighting_rules.append(
            (re.compile(r'\b(public|private|protected)\s+(\w+\s+)*(\w+)\s*\('), function_format))

        # Java 数字
        self.highlighting_rules.append((re.compile(r'\b[0-9]+\b'), number_format))
        self.highlighting_rules.append((re.compile(r'\b[0-9]*\.[0-9]+\b'), number_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            # 处理多行注释
            if '/*' in pattern.pattern:
                start_index = 0
                while start_index >= 0:
                    comment_match = pattern.search(text, start_index)
                    if comment_match:
                        start, end = comment_match.span()
                        self.setFormat(start, end - start, format)
                        start_index = end
                    else:
                        break
            else:
                # 单行匹配
                for match in pattern.finditer(text):
                    start, end = match.span()
                    # 对于函数匹配，只高亮函数名部分
                    if 'function' in pattern.pattern or 'def' in pattern.pattern:
                        if len(match.groups()) > 0:
                            func_name_start = match.start(1)
                            func_name_end = match.end(1)
                            self.setFormat(func_name_start, func_name_end - func_name_start, format)
                    else:
                        self.setFormat(start, end - start, format)


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)

        self.update_line_number_area_width(0)

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(cr.left(), cr.top(), self.line_number_area_width(), cr.height())

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(240, 240, 240))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(100, 100, 100))
                painter.drawText(0, int(top), self.line_number_area.width() - 5,
                                 self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1


class CodeEditPage(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        """设置UI界面 - 使用固定宽度"""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # ===================== 第 1 列：代码编辑器（弹性拉伸）=====================
        editor_frame = QFrame()
        editor_frame.setStyleSheet("background-color: lightskyblue; border: 1px solid #ccc;")
        editor_layout = QVBoxLayout(editor_frame)
        editor_layout.setContentsMargins(1, 1, 1, 1)

        # 使用带行号的代码编辑器
        self.code_editor = CodeEditor()
        self.setup_editor()
        editor_layout.addWidget(self.code_editor)

        # ===================== 第 2 列：操作按钮（固定宽度）=====================
        buttons_frame = self.create_buttons_column()

        # ===================== 第 3 列：右侧面板（固定宽度）=====================
        right_frame = self.create_right_panel()

        # 添加到主布局
        main_layout.addWidget(editor_frame)
        main_layout.addWidget(buttons_frame)
        main_layout.addWidget(right_frame)

    def setup_editor(self):
        """设置代码编辑器"""
        # 设置等宽字体
        font = QFont("Cascadia Code, Consolas, Menlo, Monospace", 12)
        self.code_editor.setFont(font)

        # 设置初始代码 (Python 示例)
        initial_code = """# Python 示例
def calculate_sum(numbers):
    \"\"\"计算列表中所有数字的和\"\"\"
    total = 0
    for num in numbers:
        total += num
    return total

# JavaScript 示例
function greet(name) {
    return `Hello, ${name}!`;
}

// Java 示例
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello World");
        int result = add(5, 3);
    }

    private static int add(int a, int b) {
        return a + b;
    }
}"""
        self.code_editor.setPlainText(initial_code)

        # 启用多语言语法高亮
        self.highlighter = MultiLanguageHighlighter(self.code_editor.document())

        # 编辑器设置
        self.code_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.code_editor.setUndoRedoEnabled(True)

        # 设置样式
        self.code_editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: white;
                color: black;
                border: 1px solid #ccc;
                selection-background-color: #add8e6;
            }
        """)

    # 其他方法保持不变 (create_buttons_column, create_right_panel, 按钮事件等)
    def create_buttons_column(self):
        """创建操作按钮列 - 使用固定宽度"""
        frame = QFrame()
        frame.setFixedWidth(60)
        frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 0px solid #ccc;
            }
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        buttons = [
            ("复制", self.copy_code),
            ("剪切", self.cut_code),
            ("粘贴", self.paste_code),
            ("删除", self.delete_code),
            ("撤销", self.undo_code),
            ("重做", self.redo_code)
        ]

        for i, (text, slot) in enumerate(buttons):
            btn = QPushButton(text)
            btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

            btn.setStyleSheet("""
                QPushButton {
                    font-size: 10px;
                    background-color: blue;
                    color:#FFFFFF;
                    border: none;
                    border-bottom: 1px solid transparent;
                    margin: 0px;
                    padding: 0px;
                    min-height: 30px;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: pink;
                    color:#FFFFFF;
                }
                QPushButton:pressed {
                    background-color: #d4d4d4;
                }
                QPushButton:last-child {
                    border-bottom: none;
                }
            """)
            btn.clicked.connect(slot)
            layout.addWidget(btn)

        for i in range(6):
            layout.setStretch(i, 1)

        return frame

    def create_right_panel(self):
        """创建右侧面板 - 使用固定宽度"""
        frame = QFrame()
        frame.setFixedWidth(60)
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f8f8;
                border: 1px solid #ccc;
            }
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        panels = [
            ("3-1", "lightpink"),
            ("3-2", "khaki"),
            ("3-3", "plum"),
            ("3-4", "tan"),
            ("3-5", "lightgoldenrodyellow")
        ]

        for i, (text, color) in enumerate(panels):
            panel = QFrame()
            panel.setStyleSheet(f"""
                QFrame {{
                    background-color: {color};
                    border: none;
                    border-bottom: 1px solid #999;
                    margin: 0px;
                }}
                QFrame:last-child {{
                    border-bottom: none;
                }}
            """)

            label = QPushButton(text)
            label.setStyleSheet("""
                QPushButton {
                    font-size: 8px;
                    border: none;
                    background: transparent;
                    padding: 0px;
                    margin: 0px;
                }
                QPushButton:hover {
                    background-color: rgba(255,255,255,0.3);
                }
            """)

            panel_layout = QVBoxLayout(panel)
            panel_layout.setSpacing(0)
            panel_layout.setContentsMargins(0, 0, 0, 0)
            panel_layout.addWidget(label)
            panel_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            layout.addWidget(panel)

        for i in range(5):
            if i == 4:
                layout.setStretch(i, 2)
            else:
                layout.setStretch(i, 1)

        return frame

    def copy_code(self):
        self.code_editor.copy()

    def cut_code(self):
        self.code_editor.cut()

    def paste_code(self):
        self.code_editor.paste()

    def delete_code(self):
        cursor = self.code_editor.textCursor()
        if cursor.hasSelection():
            cursor.removeSelectedText()

    def undo_code(self):
        self.code_editor.undo()

    def redo_code(self):
        self.code_editor.redo()

    def back_to_home(self):
        """返回主页按钮点击事件"""
        print("返回主页")
        if self.main_window:
            self.main_window.home_click()