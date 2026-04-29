import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import sys
import os
import threading

# ========== අමතර libraries ==========
try:
    import ttkbootstrap as tb
    from ttkbootstrap.constants import *
    USE_TTKBOOTSTRAP = True
except ImportError:
    USE_TTKBOOTSTRAP = False
    print("ttkbootstrap not installed. Using default tkinter theme.")

try:
    from pygments import highlight
    from pygments.lexers import PythonLexer
    from pygments.token import Token
    from pygments.styles import get_style_by_name
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# ========== ERROR DICT (Sinhala) ==========
ERROR_DICT = {
    "name 'x' is not defined": "👉 'x' නමින් variable එකක් හදලා නෑ. පළමුව x = ? ලෙස අගයක් දෙන්න.",
    "SyntaxError": "👉 වාග් රීති දෝෂයක් (Syntax Error). bracket, colon (:) හෝ quote ලකුණු පරීක්ෂා කරන්න.",
    "ZeroDivisionError": "👉 බිංදුවෙන් බෙදීමට තැත් කළ නිසා දෝෂයක් ආවා.",
    "IndentationError": "👉 ඉන්ඩෙන්ටේෂන් දෝෂයක්. spaces/tabs පෙළගැස්වීම පරීක්ෂා කරන්න.",
    "TypeError": "👉 දත්ත වර්ග නොගැළපේ (TypeError).",
}

def show_sinhala_error_popup(error_text):
    sinhala_msg = "මෙම දෝෂය සඳහා සිංහල පැහැදිලි කිරීමක් තවම නැත."
    for key, value in ERROR_DICT.items():
        if key in error_text:
            sinhala_msg = value
            break
    messagebox.showinfo("🟢 සිංහල දෝෂ විස්තරය",
                        f"🔴 මුල් දෝෂය:\n{error_text}\n\n🔵 සිංහල පැහැදිලි කිරීම:\n{sinhala_msg}")

def explain_error(error_text):
    if "SyntaxError" in error_text:
        return "🧠 SyntaxError: කේතයේ ව්‍යාකරණ දෝෂයක්."
    elif "NameError" in error_text:
        return "🧠 NameError: Variable එකක් define කරලා නැහැ."
    elif "TypeError" in error_text:
        return "🧠 TypeError: Data type mismatch."
    elif "IndentationError" in error_text:
        return "🧠 IndentationError: ඉන්ඩෙන්ටේෂන් වැරදියි."
    else:
        return "🧠 Unknown Error:\n" + error_text

# ========== LINE NUMBERS WIDGET ==========
class LineNumbers(tk.Canvas):
    def __init__(self, text_widget, *args, **kwargs):
        super().__init__(*args, **kwargs, highlightthickness=0)
        self.text_widget = text_widget
        self.text_widget.bind('<KeyRelease>', self.on_change)
        self.text_widget.bind('<ButtonRelease-1>', self.on_change)
        self.text_widget.bind('<MouseWheel>', self.on_change)
        self.bind('<Configure>', self.on_change)
        self.on_change()

    def on_change(self, event=None):
        self.delete('all')
        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            line_num = str(i).split('.')[0]
            self.create_text(5, y, anchor="nw", text=line_num, fill="gray")
            i = self.text_widget.index("%s+1line" % i)

# ========== SYNTAX HIGHLIGHTING ==========
def highlight_syntax(text_widget):
    if not PYGMENTS_AVAILABLE:
        return
    code = text_widget.get("1.0", "end-1c")
    text_widget.mark_set("range_start", "1.0")
    text_widget.tag_remove("pygments", "1.0", "end")
    try:
        from pygments.lexers import PythonLexer
        from pygments.token import Token
        lexer = PythonLexer()
        tokens = list(lexer.get_tokens(code))
        pos = 0
        for token_type, token_text in tokens:
            start = text_widget.index(f"1.0 + {pos} chars")
            pos += len(token_text)
            end = text_widget.index(f"1.0 + {pos} chars")
            tag = str(token_type).split('.')[-1].lower()
            if tag == "keyword":
                text_widget.tag_add("pygments_keyword", start, end)
            elif tag in ("name", "builtin"):
                text_widget.tag_add("pygments_builtin", start, end)
            elif tag == "string":
                text_widget.tag_add("pygments_string", start, end)
            elif tag == "comment":
                text_widget.tag_add("pygments_comment", start, end)
        text_widget.tag_config("pygments_keyword", foreground="#569CD6")
        text_widget.tag_config("pygments_builtin", foreground="#4EC9B0")
        text_widget.tag_config("pygments_string", foreground="#CE9178")
        text_widget.tag_config("pygments_comment", foreground="#6A9955")
    except:
        pass

# ========== TABBED EDITOR CLASS ==========
class EditorTab:
    def __init__(self, parent, tab_control, filename=None):
        self.parent = parent
        self.tab_control = tab_control
        self.filename = filename
        self.modified = False
        
        # Frame for editor + line numbers
        self.frame = tk.Frame(tab_control)
        self.text_frame = tk.Frame(self.frame)
        self.text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Line numbers canvas
        self.line_numbers = LineNumbers(None, self.text_frame, width=40, bg='#2d2d2d')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Text widget
        self.text = tk.Text(self.text_frame, undo=True, font=("Consolas", 10), wrap="none",
                            bg='#1e1e1e', fg='white', insertbackground='white')
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.text.bind('<KeyRelease>', self.on_text_change)
        
        # Link line numbers
        self.line_numbers.text_widget = self.text
        self.text.config(yscrollcommand=self.on_text_scroll)
        self.line_numbers.on_change()
        
        # Scrollbar
        scroll = tk.Scrollbar(self.text_frame, command=self.text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.config(yscrollcommand=self.on_yview)
        self.text_scroll = scroll
        
        if filename:
            self.load_file(filename)
            tab_title = os.path.basename(filename)
        else:
            tab_title = "Untitled"
        self.tab_control.add(self.frame, text=tab_title)
        self.tab_control.select(self.frame)
    
    def on_text_change(self, event=None):
        self.modified = True
        self.update_tab_title()
        if PYGMENTS_AVAILABLE:
            highlight_syntax(self.text)
    
    def on_text_scroll(self, *args):
        self.line_numbers.on_change()
        self.text.yview(*args)
    
    def on_yview(self, *args):
        self.text.yview(*args)
        self.line_numbers.on_change()
    
    def update_tab_title(self):
        title = os.path.basename(self.filename) if self.filename else "Untitled"
        if self.modified:
            title += " *"
        self.tab_control.tab(self.frame, text=title)
    
    def load_file(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", f.read())
        self.filename = filepath
        self.modified = False
        self.update_tab_title()
        if PYGMENTS_AVAILABLE:
            highlight_syntax(self.text)
    
    def save(self):
        if self.filename:
            with open(self.filename, "w", encoding="utf-8") as f:
                f.write(self.text.get("1.0", "end-1c"))
            self.modified = False
            self.update_tab_title()
            return True
        else:
            return self.save_as()
    
    def save_as(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python files", "*.py")])
        if filepath:
            self.filename = filepath
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self.text.get("1.0", "end-1c"))
            self.modified = False
            self.update_tab_title()
            return True
        return False
    
    def get_code(self):
        return self.text.get("1.0", "end-1c")

# ========== MAIN IDE CLASS ==========
class NetraIDE:
    def __init__(self, root):
        self.root = root
        self.current_process = None
        self.tabs = [] # list of EditorTab objects
        self.current_tab_index = 0
        
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
        self.setup_git_buttons()
        self.setup_bottom_panel()
        self.bind_shortcuts()
        
        # New initial tab
        self.new_tab()
    
    def setup_ui(self):
        if USE_TTKBOOTSTRAP:
            self.root.style = tb.Style()
            self.root.style.theme_use("darkly") # modern dark theme
        else:
            self.root.configure(bg='#2b2b2b')
        
        self.root.title("Netra IDE 😎")
        self.root.geometry("1200x700")
        
        # PanedWindow main vertical
        self.main_pane = tk.PanedWindow(self.root, orient=tk.VERTICAL, sashrelief=tk.RAISED)
        self.main_pane.pack(fill=tk.BOTH, expand=True)
        
        # Editor area (tabbed)
        self.editor_frame = tk.Frame(self.main_pane)
        self.main_pane.add(self.editor_frame, stretch="always", height=500)
        
        self.tab_control = ttk.Notebook(self.editor_frame)
        self.tab_control.pack(fill=tk.BOTH, expand=True)
        self.tab_control.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # Bottom area (output + assistant)
        self.bottom_notebook = ttk.Notebook(self.main_pane)
        self.main_pane.add(self.bottom_notebook, stretch="always", height=200)
    
    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", accelerator="Ctrl+N", command=self.new_tab)
        file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_current)
        file_menu.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=self.save_as_current)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo)
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=self.redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", accelerator="Ctrl+X", command=self.cut)
        edit_menu.add_command(label="Copy", accelerator="Ctrl+C", command=self.copy)
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V", command=self.paste)
        edit_menu.add_separator()
        edit_menu.add_command(label="Find...", accelerator="Ctrl+F", command=self.find)
        
        # Run menu
        run_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Run", menu=run_menu)
        run_menu.add_command(label="Run Script", accelerator="F5", command=self.run_code)
        run_menu.add_command(label="Stop", accelerator="F6", command=self.stop_code)
        
        # Theme menu
        if USE_TTKBOOTSTRAP:
            theme_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Theme", menu=theme_menu)
            theme_menu.add_command(label="Dark", command=lambda: self.change_theme("darkly"))
            theme_menu.add_command(label="Light", command=lambda: self.change_theme("flatly"))
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.about)
    
    def setup_toolbar(self):
        toolbar = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Icons if Pillow available
        def make_icon(name):
            if PILLOW_AVAILABLE:
                try:
                    img = Image.open(f"icons/{name}.png").resize((20,20), Image.LANCZOS)
                    return ImageTk.PhotoImage(img)
                except:
                    return None
            return None
        
        btn_new = tk.Button(toolbar, text="New", command=self.new_tab) # , image=make_icon("new"), compound=tk.LEFT)
        btn_new.pack(side=tk.LEFT, padx=2)
        btn_open = tk.Button(toolbar, text="Open", command=self.open_file)
        btn_open.pack(side=tk.LEFT, padx=2)
        btn_save = tk.Button(toolbar, text="Save", command=self.save_current)
        btn_save.pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        btn_run = tk.Button(toolbar, text="Run", bg="#4caf50", fg="white", command=self.run_code)
        btn_run.pack(side=tk.LEFT, padx=2)
        btn_stop = tk.Button(toolbar, text="Stop", bg="#f44336", fg="white", command=self.stop_code)
        btn_stop.pack(side=tk.LEFT, padx=2)
    
    def setup_statusbar(self):
        self.status_var = tk.StringVar()
        self.status_var.set("Ln 1, Col 1")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_statusbar()
    
    def update_statusbar(self, event=None):
        tab = self.get_current_tab()
        if tab:
            cursor_pos = tab.text.index(tk.INSERT)
            line, col = cursor_pos.split('.')
            self.status_var.set(f"Ln {line}, Col {int(col)+1}")
            self.root.after(200, self.update_statusbar)
    
    def setup_git_buttons(self):
        git_frame = tk.Frame(self.root)
        git_frame.pack(side=tk.BOTTOM, fill=tk.X, before=self.status_var)
        btn_commit = tk.Button(git_frame, text="Git Commit", command=self.git_commit)
        btn_commit.pack(side=tk.RIGHT, padx=2)
        btn_push = tk.Button(git_frame, text="Git Push", command=self.git_push)
        btn_push.pack(side=tk.RIGHT, padx=2)
    
    def setup_bottom_panel(self):
        self.shell_frame = tk.Frame(self.bottom_notebook)
        self.bottom_notebook.add(self.shell_frame, text="Shell")
        self.output_text = tk.Text(self.shell_frame, bg="black", fg="lime", font=("Consolas", 9))
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        self.assistant_frame = tk.Frame(self.bottom_notebook)
        self.bottom_notebook.add(self.assistant_frame, text="Assistant")
        self.assistant_text = tk.Text(self.assistant_frame, bg="#1e1e1e", fg="white", wrap="word")
        self.assistant_text.pack(fill=tk.BOTH, expand=True)
    
    def get_current_tab(self):
        if self.tabs:
            current = self.tab_control.select()
            for tab in self.tabs:
                if tab.frame == current:
                    return tab
        return None
    
    def on_tab_changed(self, event):
        self.update_statusbar()
    
    def new_tab(self, filename=None):
        tab = EditorTab(self.root, self.tab_control, filename)
        self.tabs.append(tab)
        return tab
    
    def open_file(self):
        file_path = filedialog.askopenfilename(defaultextension=".py", filetypes=[("Python files", "*.py")])
        if file_path:
            self.new_tab(file_path)
    
    def save_current(self):
        tab = self.get_current_tab()
        if tab:
            tab.save()
    
    def save_as_current(self):
        tab = self.get_current_tab()
        if tab:
            tab.save_as()
    
    def undo(self):
        tab = self.get_current_tab()
        if tab:
            try:
                tab.text.edit_undo()
            except: pass
    
    def redo(self):
        tab = self.get_current_tab()
        if tab:
            try:
                tab.text.edit_redo()
            except: pass
    
    def cut(self):
        tab = self.get_current_tab()
        if tab:
            tab.text.event_generate("<<Cut>>")
    
    def copy(self):
        tab = self.get_current_tab()
        if tab:
            tab.text.event_generate("<<Copy>>")
    
    def paste(self):
        tab = self.get_current_tab()
        if tab:
            tab.text.event_generate("<<Paste>>")
    
    def find(self):
        def find_next():
            search_term = entry.get()
            if search_term:
                tab = self.get_current_tab()
                if tab:
                    pos = tab.text.search(search_term, "1.0", stopindex=tk.END)
                    if pos:
                        tab.text.tag_remove("found", "1.0", tk.END)
                        tab.text.tag_add("found", pos, f"{pos}+{len(search_term)}c")
                        tab.text.tag_config("found", background="yellow")
                        tab.text.mark_set("insert", pos)
                        tab.text.see(pos)
                    else:
                        messagebox.showinfo("Find", "No more matches.")
        find_win = tk.Toplevel(self.root)
        find_win.title("Find")
        tk.Label(find_win, text="Find:").pack(side=tk.LEFT)
        entry = tk.Entry(find_win, width=30)
        entry.pack(side=tk.LEFT, padx=5)
        tk.Button(find_win, text="Find Next", command=find_next).pack(side=tk.LEFT)
    
    def run_code(self):
        tab = self.get_current_tab()
        if not tab:
            return
        code = tab.get_code()
        with open("temp.py", "w", encoding="utf-8") as f:
            f.write(code)
        
        self.output_text.delete("1.0", tk.END)
        self.assistant_text.delete("1.0", tk.END)
        
        try:
            self.current_process = subprocess.Popen(
                [sys.executable, "temp.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8"
            )
            self.read_output()
        except Exception as e:
            self.output_text.insert(tk.END, f"Failed: {e}\n")
    
    def read_output(self):
        if self.current_process is None:
            return
        stdout_line = self.current_process.stdout.readline()
        stderr_line = self.current_process.stderr.readline()
        
        if stdout_line:
            self.output_text.insert(tk.END, stdout_line)
            self.output_text.see(tk.END)
        if stderr_line:
            self.output_text.insert(tk.END, stderr_line)
            self.assistant_text.insert(tk.END, explain_error(stderr_line))
            show_sinhala_error_popup(stderr_line)
        
        if self.current_process.poll() is None:
            self.root.after(100, self.read_output)
        else:
            remaining_out, remaining_err = self.current_process.communicate()
            if remaining_out:
                self.output_text.insert(tk.END, remaining_out)
            if remaining_err:
                self.output_text.insert(tk.END, remaining_err)
                self.assistant_text.insert(tk.END, explain_error(remaining_err))
                show_sinhala_error_popup(remaining_err)
            self.current_process = None
    
    def stop_code(self):
        if self.current_process and self.current_process.poll() is None:
            self.current_process.terminate()
            self.output_text.insert(tk.END, "\n⚠️ Stopped by user.\n")
    
    def git_commit(self):
        subprocess.run(["git", "add", "."])
        result = subprocess.run(["git", "commit", "-m", "Netra IDE commit"], capture_output=True, text=True)
        messagebox.showinfo("Git Commit", result.stdout if result.returncode==0 else result.stderr)
    
    def git_push(self):
        result = subprocess.run(["git", "push"], capture_output=True, text=True)
        messagebox.showinfo("Git Push", result.stdout if result.returncode==0 else result.stderr)
    
    def change_theme(self, theme_name):
        if USE_TTKBOOTSTRAP:
            self.root.style.theme_use(theme_name)
    
    def about(self):
        messagebox.showinfo("About Netra", "Netra IDE 😎\nVersion 2.0\nThonny-style + Modern Features\nSinhala Error Assistant\nGit Integration")
    
    def bind_shortcuts(self):
        self.root.bind("<Control-n>", lambda e: self.new_tab())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_current())
        self.root.bind("<Control-Shift-S>", lambda e: self.save_as_current())
        self.root.bind("<F5>", lambda e: self.run_code())
        self.root.bind("<F6>", lambda e: self.stop_code())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-f>", lambda e: self.find())
    
    def on_closing(self):
        # Save all modified tabs? For simplicity, just ask
        for tab in self.tabs:
            if tab.modified:
                ans = messagebox.askyesno("Unsaved Changes", f"Save {tab.filename or 'Untitled'}?")
                if ans:
                    tab.save()
        if os.path.exists("temp.py"):
            os.remove("temp.py")
        if self.current_process:
            self.current_process.terminate()
        self.root.destroy()

def main():
    root = tk.Tk() if not USE_TTKBOOTSTRAP else tb.Window(themename="darkly")
    app = NetraIDE(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
