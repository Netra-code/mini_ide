import tkinter as tk
from tkinter import messagebox

# 1. පරිවර්තන නිඝණ්ඩුව (තවත් Error වර්ග අවශ්‍ය පරිදි එකතු කරන්න)
ERROR_DICT = {
    "name 'x' is not defined": "👉 'x' නමින් variable එකක් හදලා නෑ. පළමුව x = ? ලෙස අගයක් දෙන්න.",
    "SyntaxError": "👉 වාග් රීති දෝෂයක් (Syntax Error). bracket, colon (:) හෝ quote ලකුණු පරීක්ෂා කරන්න.",
    "ZeroDivisionError": "👉 බිංදුවෙන් බෙදීමට තැත් කළ නිසා දෝෂයක් ආවා.",
}

def show_sinhala_error_popup(error_text):
    """
    මෙම ශ්‍රිතය Python Error Message එකක් ගෙන,
    ඊට අදාළ සිංහල පැහැදිලි කිරීම Popup එකකින් පෙන්වයි.
    """
    # Default පණිවිඩය
    sinhala_msg = "මෙම දෝෂය සඳහා සිංහල පැහැදිලි කිරීමක් තවම නැත."

    # Error Text එක ඇතුළේ Key Word එකක් හොයනවා
    for key, value in ERROR_DICT.items():
        if key in error_text:
            sinhala_msg = value
            break # මුලින්ම ගැලපෙන පරිවර්තනය ගන්න

    # Tkinter Popup එක හදන්න
    root = tk.Tk()
    root.withdraw() # Main Tkinter window එක හංගන්න
    messagebox.showinfo(
        "🟢 සිංහල දෝෂ විස්තරය",
        f"🔴 මුල් දෝෂය:\n{error_text}\n\n🔵 සිංහල පැහැදිලි කිරීම:\n{sinhala_msg}"
    )
    root.destroy()