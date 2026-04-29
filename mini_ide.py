import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import sys
import os

# ========== දෙවන file එකේ popup function (integrate) ==========
ERROR_DICT = {
    "name 'x' is not defined": "👉 'x' නමින් variable එකක් හදලා නෑ. පළමුව x = ? ලෙස අගයක් දෙන්න.",
    "SyntaxError": "👉 වාග් රීති දෝෂයක් (Syntax Error). bracket, colon (:) හෝ quote ලකුණු පරීක්ෂා කරන්න.",
    "ZeroDivisionError": "👉 බිංදුවෙන් බෙදීමට තැත් කළ නිසා දෝෂයක් ආවා.",
}

def show_sinhala_error_popup(error_text):
    """Popup එකකින් සිංහල දෝෂ පැහැදිලි කිරීම පෙන්වයි"""
    sinhala_msg = "මෙම දෝෂය සඳහා සිංහල පැහැදිලි කිරීමක් තවම නැත."
    for key, value in ERROR_DICT.items():
        if key in error_text:
            sinhala_msg = value
            break
    popup_root = tk.Tk()
    popup_root.withdraw()
    messagebox.showinfo(
        "🟢 සිංහල දෝෂ විස්තරය",
        f"🔴 මුල් දෝෂය:\n{error_text}\n\n🔵 සිංහල පැහැදිලි කිරීම:\n{sinhala_msg}"
    )
    popup_root.destroy()

# ========== ERROR EXPLAIN ENGINE (Assistant Tab සඳහා) ==========
def explain_error(error_text):
    if "SyntaxError" in error_text:
        return "🧠 SyntaxError:\nකේතයේ ව්‍යාකරණ දෝෂයක් තියෙනවා.\nColon :, brackets (), indentation check කරන්න."
    elif "NameError" in error_text:
        return "🧠 NameError:\nVariable එකක් හෝ function එකක් define කරලා නැහැ."
    elif "TypeError" in error_text:
        return "🧠 TypeError:\nData type mismatch එකක් තියෙනවා."
    elif "IndentationError" in error_text:
        return "🧠 IndentationError:\nSpaces / Tabs alignment වැරදියි."
    elif error_text == "":
        return "🎉 Error එකක් නෑ! Code එක හරි."
    else:
        return "🧠 Unknown Error:\n" + error_text

# ========== GLOBALS ==========
current_process = None
current_file = None
root = None
code_text = None
output_text = None
assistant_text = None

# ========== FILE OPERATIONS ==========
def new_file():
    global current_file
    code_text.delete("1.0", tk.END)
    current_file = None
    root.title("Netra 😎 - New File")

def open_file():
    global current_file
    file_path = filedialog.askopenfilename(defaultextension=".py", filetypes=[("Python files", "*.py"), ("All files", "*.*")])
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            code_text.delete("1.0", tk.END)
            code_text.insert("1.0", f.read())
        current_file = file_path
        root.title(f"Netra 😎 - {os.path.basename(current_file)}")

def save_file():
    global current_file
    if current_file:
        with open(current_file, "w", encoding="utf-8") as f:
            f.write(code_text.get("1.0", tk.END))
    else:
        save_as_file()

def save_as_file():
    global current_file
    file_path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python files", "*.py"), ("All files", "*.*")])
    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code_text.get("1.0", tk.END))
        current_file = file_path
        root.title(f"Netra 😎 - {os.path.basename(current_file)}")

# ========== RUN & STOP ==========
def run_code():
    global current_process
    code = code_text.get("1.0", tk.END)
    
    with open("temp.py", "w", encoding="utf-8") as f:
        f.write(code)
    
    output_text.delete("1.0", tk.END)
    assistant_text.delete("1.0", tk.END)
    
    try:
        current_process = subprocess.Popen(
            [sys.executable, "temp.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )
        read_output()
    except Exception as e:
        output_text.insert(tk.END, f"Failed to start: {e}\n")
        assistant_text.insert(tk.END, f"💥 {e}")

def read_output():
    global current_process
    if current_process is None:
        return
    
    stdout_line = current_process.stdout.readline()
    stderr_line = current_process.stderr.readline()
    
    if stdout_line:
        output_text.insert(tk.END, stdout_line)
        output_text.see(tk.END)
    if stderr_line:
        output_text.insert(tk.END, stderr_line)
        output_text.see(tk.END)
        assistant_text.insert(tk.END, explain_error(stderr_line))
        show_sinhala_error_popup(stderr_line)
    
    if current_process.poll() is None:
        root.after(100, read_output)
    else:
        remaining_out, remaining_err = current_process.communicate()
        if remaining_out:
            output_text.insert(tk.END, remaining_out)
        if remaining_err:
            output_text.insert(tk.END, remaining_err)
            assistant_text.insert(tk.END, explain_error(remaining_err))
            show_sinhala_error_popup(remaining_err)
        current_process = None

def stop_code():
    global current_process
    if current_process and current_process.poll() is None:
        current_process.terminate()
        output_text.insert(tk.END, "\n⚠️ Process terminated by user.\n")
        assistant_text.insert(tk.END, "⏹️ Code execution stopped.")

# ========== EDIT MENU FUNCTIONS ==========
def undo():
    try:
        code_text.edit_undo()
    except tk.TclError:
        pass

def redo():
    try:
        code_text.edit_redo()
    except tk.TclError:
        pass

def cut():
    code_text.event_generate("<<Cut>>")

def copy():
    code_text.event_generate("<<Copy>>")

def paste():
    code_text.event_generate("<<Paste>>")

def find():
    def find_next():
        search_term = entry.get()
        if search_term:
            pos = code_text.search(search_term, "1.0", stopindex=tk.END)
            if pos:
                code_text.tag_remove("found", "1.0", tk.END)
                code_text.tag_add("found", pos, f"{pos}+{len(search_term)}c")
                code_text.tag_config("found", background="yellow")
                code_text.mark_set("insert", pos)
                code_text.see(pos)
            else:
                messagebox.showinfo("Find", "No more matches.")
    find_win = tk.Toplevel(root)
    find_win.title("Find")
    tk.Label(find_win, text="Find:").pack(side=tk.LEFT)
    entry = tk.Entry(find_win, width=30)
    entry.pack(side=tk.LEFT, padx=5)
    tk.Button(find_win, text="Find Next", command=find_next).pack(side=tk.LEFT)

# ========== MAIN WINDOW ==========
def main():
    global root, code_text, output_text, assistant_text, current_file, current_process
    
    root = tk.Tk()
    root.title("Netra 😎")
    root.geometry("1000x700")
    
    # ========== MENU BAR ==========
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="New", accelerator="Ctrl+N", command=new_file)
    file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=open_file)
    file_menu.add_command(label="Save", accelerator="Ctrl+S", command=save_file)
    file_menu.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=save_as_file)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)
    
    edit_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Edit", menu=edit_menu)
    edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=undo)
    edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=redo)
    edit_menu.add_separator()
    edit_menu.add_command(label="Cut", accelerator="Ctrl+X", command=cut)
    edit_menu.add_command(label="Copy", accelerator="Ctrl+C", command=copy)
    edit_menu.add_command(label="Paste", accelerator="Ctrl+V", command=paste)
    edit_menu.add_separator()
    edit_menu.add_command(label="Find...", accelerator="Ctrl+F", command=find)
    
    run_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Run", menu=run_menu)
    run_menu.add_command(label="Run Script", accelerator="F5", command=run_code)
    run_menu.add_command(label="Stop", accelerator="F6", command=stop_code)
    
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", "Netra IDE\nThonny Style + Sinhala Error Assistant"))
    
    # ========== TOOLBAR ==========
    toolbar = tk.Frame(root, bd=1, relief=tk.RAISED)
    toolbar.pack(side=tk.TOP, fill=tk.X)
    
    btn_new = tk.Button(toolbar, text="New", command=new_file)
    btn_new.pack(side=tk.LEFT, padx=2, pady=2)
    btn_open = tk.Button(toolbar, text="Open", command=open_file)
    btn_open.pack(side=tk.LEFT, padx=2, pady=2)
    btn_save = tk.Button(toolbar, text="Save", command=save_file)
    btn_save.pack(side=tk.LEFT, padx=2, pady=2)
    
    # FIXED: ttk.Separator instead of tk.Separator
    ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=2)
    
    btn_run = tk.Button(toolbar, text="Run", bg="#4caf50", fg="white", command=run_code)
    btn_run.pack(side=tk.LEFT, padx=2, pady=2)
    btn_stop = tk.Button(toolbar, text="Stop", bg="#f44336", fg="white", command=stop_code)
    btn_stop.pack(side=tk.LEFT, padx=2, pady=2)
    
    # ========== PANED WINDOW ==========
    main_pane = tk.PanedWindow(root, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=5)
    main_pane.pack(fill=tk.BOTH, expand=True)
    
    editor_frame = tk.Frame(main_pane)
    main_pane.add(editor_frame, stretch="always", height=400)
    
    code_scroll = tk.Scrollbar(editor_frame)
    code_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    code_text = tk.Text(editor_frame, height=20, font=("Consolas", 10), wrap="none", undo=True, autoseparators=True, maxundo=-1)
    code_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    code_scroll.config(command=code_text.yview)
    code_text.config(yscrollcommand=code_scroll.set)
    
    bottom_notebook = ttk.Notebook(main_pane)
    main_pane.add(bottom_notebook, stretch="always", height=250)
    
    shell_frame = tk.Frame(bottom_notebook)
    bottom_notebook.add(shell_frame, text="Shell")
    output_text = tk.Text(shell_frame, bg="black", fg="lime", font=("Consolas", 9), insertbackground="white")
    output_text.pack(fill=tk.BOTH, expand=True)
    
    assistant_frame = tk.Frame(bottom_notebook)
    bottom_notebook.add(assistant_frame, text="Assistant")
    assistant_text = tk.Text(assistant_frame, bg="#1e1e1e", fg="white", font=("Segoe UI", 11), wrap="word")
    assistant_text.pack(fill=tk.BOTH, expand=True)
    
    # ========== KEYBOARD SHORTCUTS ==========
    root.bind("<Control-n>", lambda e: new_file())
    root.bind("<Control-o>", lambda e: open_file())
    root.bind("<Control-s>", lambda e: save_file())
    root.bind("<Control-Shift-S>", lambda e: save_as_file())
    root.bind("<F5>", lambda e: run_code())
    root.bind("<F6>", lambda e: stop_code())
    root.bind("<Control-z>", lambda e: undo())
    root.bind("<Control-y>", lambda e: redo())
    root.bind("<Control-x>", lambda e: cut())
    root.bind("<Control-c>", lambda e: copy())
    root.bind("<Control-v>", lambda e: paste())
    root.bind("<Control-f>", lambda e: find())
    
    def on_closing():
        if os.path.exists("temp.py"):
            os.remove("temp.py")
        if current_process and current_process.poll() is None:
            current_process.terminate()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    root.mainloop()

if __name__ == "__main__":
    main()
