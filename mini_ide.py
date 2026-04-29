import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import os

# ========== ERROR EXPLAIN ENGINE ==========
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

# ========== RUN BUTTON FUNCTION ==========
def run_code():
    code = code_text.get("1.0", tk.END)

    with open("temp.py", "w", encoding="utf-8") as f:
        f.write(code)

    try:
        result = subprocess.run(
            [sys.executable, "temp.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10
        )
    except subprocess.TimeoutExpired:
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, "⚠️ Code execution timeout (10s)")
        assistant_text.delete("1.0", tk.END)
        assistant_text.insert(tk.END, "⏱️ Code එක වැඩි වෙලාවක් ගතවේ. සදාකාලික loop එකක්ද?")
        return
    except Exception as e:
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, f"Runtime error: {e}")
        assistant_text.delete("1.0", tk.END)
        assistant_text.insert(tk.END, f"💥 {e}")
        return

    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, result.stdout + result.stderr)

    assistant_text.delete("1.0", tk.END)
    assistant_text.insert(tk.END, explain_error(result.stderr))

# ========== MAIN WINDOW ==========
root = tk.Tk()
root.title("Netra 😎")
root.geometry("900x650")

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

editor_tab = tk.Frame(notebook)
notebook.add(editor_tab, text="Editor")

code_text = tk.Text(editor_tab, height=20, font=("Consolas", 10), wrap="none")
code_text.pack(fill="both", expand=True)

run_btn = tk.Button(editor_tab, text="▶ Run", command=run_code, bg="#4caf50", fg="white")
run_btn.pack(pady=5)

output_text = tk.Text(editor_tab, height=10, bg="black", fg="lime", font=("Consolas", 9), insertbackground="white")
output_text.pack(fill="both", expand=True)

assistant_tab = tk.Frame(notebook)
notebook.add(assistant_tab, text="Assistant")

assistant_text = tk.Text(
    assistant_tab,
    bg="#1e1e1e",
    fg="white",
    font=("Segoe UI", 11),
    wrap="word"
)
assistant_text.pack(fill="both", expand=True)

def on_closing():
    if os.path.exists("temp.py"):
        os.remove("temp.py")
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()
