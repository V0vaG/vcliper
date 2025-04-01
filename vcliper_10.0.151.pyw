import json
import subprocess
import os
import re
import time
import pyperclip
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import platform


version = '1.0.15'
monitoring = False

alias = "vcliper"

if platform.system() == "Windows":
    from plyer import notification
    import sys

    dictionary_path = r"C:\vcliper\vcliper.json"
elif platform.system() == "Linux":  # Assume Linux or other Unix-like OS
    dictionary_path = os.path.expanduser("~/script_files/vcliper/vcliper.json")

os.makedirs(os.path.dirname(dictionary_path), exist_ok=True)

def add_to_env():
    if platform.system() == "Windows":
        path = os.path.abspath(sys.argv[0])  # Automatically get the script's path
        command = alias
        profile_path = os.path.join(os.getenv("USERPROFILE"), "Documents", "WindowsPowerShell", "Microsoft.PowerShell_profile.ps1")

        print(f"Writing to file {profile_path}")
        
        function_line = f'function {command} {{ & "{path}" }}'
        escaped_function_line = re.escape(function_line)  # Escape backslashes

        # Ensure the profile exists
        if not os.path.exists(profile_path):
            with open(profile_path, "w", encoding="utf-8") as f:
                pass  # Create an empty file
        
        # Read the profile contents
        with open(profile_path, "r", encoding="utf-8") as f:
            profile_content = f.read()
        
        # Check if the function already exists with a different path
        pattern = rf'function\s+{command}\s+\{{[^}}]+\}}'
        if re.search(pattern, profile_content):
            updated_content = re.sub(pattern, function_line, profile_content)
            print(f"Updating the value of {command} to the path {path} in Environment variables")
        else:
            updated_content = f"{profile_content}\n{function_line}"
            print(f"Adding the value of {command} to the path {path} in Environment variables")
        
        # Write the updated content back to the profile
        with open(profile_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        
        # Reload the profile correctly
        os.system(f'PowerShell -ExecutionPolicy Bypass -Command "& {{. \"{profile_path}\"}}"')

    elif platform.system() == "Linux":
        # Get the full path of the current script
        script_path = os.path.abspath(__file__)

        # Expand ~ to the full path of the user's home directory
        bashrc_path = os.path.expanduser("~/.bashrc")

        # Create the alias line
        alias_line = f"alias {alias}='python3 {script_path}'\n"

        # Check if the alias already exists
        with open(bashrc_path, "a+") as f:
            f.seek(0)
            contents = f.read()
            if alias_line.strip() not in contents:
                f.write(alias_line)
                print(f"Alias added to {bashrc_path}")
            else:
                print(f"Alias already exists in {bashrc_path}")


def show_notification(title, message, timeout=5):
    if platform.system().lower() == "windows":
        notification.notify(
            title=title,
            message=message,
            app_name="Python Notification",
            timeout=timeout
        )
    elif platform.system() == "Linux":
        miliseconds = int(timeout * 100)
        subprocess.run(["notify-send", title, message, "-t", str(miliseconds)])


def replace_words(sentence, word_dict, case_sensitive):
    sentence = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{1,5}\b', '1.2.3.4:5678', sentence)
    replacements = []

    def replace_word(match):
        word = match.group(0)
        base_word = re.sub(r'[^\w]', '', word)

        if not case_sensitive:
            base_word_key = base_word.lower()
        else:
            base_word_key = base_word

        replacement = word_dict.get(base_word_key, word)

        if replacement != word:
            replacements.append((word, replacement))

        return replacement

    modified = re.sub(r'\b\w+\b', replace_word, sentence)

    if replacements:
        print("Replacements made:", ", ".join(f"'{orig}' → '{new}'" for orig, new in replacements))
        show_notification("vcliper", "Replacements made:, ".join(f"'{orig}' → '{new}'" for orig, new in replacements), 5)

    return modified




def create_placeholder_dict(file_path):
    placeholder_dict = {
        "options": {
            "case_sensitive": True
        },
        "dictionary": {
            "hello": "hi",
            "vladimir": "vova"
        }
    }
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as file:
            json.dump(placeholder_dict, file, indent=4)
    except Exception as e:
        messagebox.showerror("Error", f"Error creating dictionary: {e}")


def load_dictionary(file_path):
    if not os.path.exists(file_path):
        create_placeholder_dict(file_path)
        show_notification("vcliper", "Dictionary file created. Edit dictionary.json and restart the script", 5)
        return {}, True
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            word_dict = data.get("dictionary", {})
            case_sensitive = data.get("options", {}).get("case_sensitive", True)
            return word_dict, case_sensitive
    except json.JSONDecodeError:
        messagebox.showerror("Error", "Failed to decode JSON dictionary.")
        return {}, True


def save_and_close():
    # Add auto_update to the settings
    try:
        data = {
            "options": {
            "case_sensitive": case_sensitive_var.get(),
                "auto_update": auto_update_var.get()
            },
            "dictionary": word_dict
        }
        with open(dictionary_path, 'w') as file:
            json.dump(data, file, indent=4)
        show_notification("vcliper", "Settings saved successfully.", 5)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save settings: {e}")
    settings_window.destroy()

    add_env_button = tk.Button(settings_window, text="Add Env", command=add_to_env)
    add_env_button.pack(pady=5)

    check_update_button = tk.Button(settings_window, text="Check Update", command=check_update)
    check_update_button.pack(pady=5)

    save_button = tk.Button(settings_window, text="Save & Close", command=save_and_close)
    save_button.pack(pady=5)


def open_settings():
    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("400x400")

    word_dict, case_sensitive = load_dictionary(dictionary_path)
    case_sensitive_var = tk.BooleanVar(value=case_sensitive)

    # Load auto update if available
    with open(dictionary_path, "r") as f:
        data = json.load(f)
    auto_update_var = tk.BooleanVar(value=data.get("options", {}).get("auto_update", False))

    def delete_word():
        selected_item = tree.selection()
        if selected_item:
            for item in selected_item:
                word = tree.item(item, "values")[0]
                del word_dict[word]
                tree.delete(item)
            save_settings(case_sensitive_var, word_dict)

    def add_word():
        original = original_entry.get().strip()
        replacement = replacement_entry.get().strip()
        if original and replacement:
            word_dict[original] = replacement
            tree.insert("", "end", values=(original, replacement))
            original_entry.delete(0, tk.END)
            replacement_entry.delete(0, tk.END)
            save_settings(case_sensitive_var, word_dict)

    def check_update():
        # Placeholder logic for update checking
        show_notification("vcliper", f"You're using version {version}. (Update check not implemented)", 5)
        messagebox.showinfo("Check Update", f"You're using version {version}.\nUpdate check not implemented.")

    case_sensitive_check = tk.Checkbutton(settings_window, text="Case Sensitive", variable=case_sensitive_var)
    case_sensitive_check.pack(pady=5)

    auto_update_check = tk.Checkbutton(settings_window, text="Auto Update", variable=auto_update_var)
    auto_update_check.pack(pady=5)

    table_frame = tk.Frame(settings_window)
    table_frame.pack(pady=5, fill="both", expand=True)

    tree = ttk.Treeview(table_frame, columns=("Original", "Replacement"), show="headings", height=5)
    tree.heading("Original", text="Original")
    tree.heading("Replacement", text="Replacement")

    for original, replacement in word_dict.items():
        tree.insert("", "end", values=(original, replacement))

    tree.pack(fill="both", expand=True)

    entry_frame = tk.Frame(settings_window)
    entry_frame.pack(pady=5)

    original_entry = tk.Entry(entry_frame, width=15)
    original_entry.grid(row=0, column=0, padx=5)

    replacement_entry = tk.Entry(entry_frame, width=15)
    replacement_entry.grid(row=0, column=1, padx=5)

    add_button = tk.Button(entry_frame, text="Add Word", command=add_word)
    add_button.grid(row=0, column=2, padx=5)

    delete_button = tk.Button(settings_window, text="Delete Selected", command=delete_word)
    delete_button.pack(pady=5)

    def save_and_close():
        # Add auto_update to the settings
        try:
            data = {
                "options": {
                    "case_sensitive": case_sensitive_var.get(),
                    "auto_update": auto_update_var.get()
                },
                "dictionary": word_dict
            }
            with open(dictionary_path, 'w') as file:
                json.dump(data, file, indent=4)
            show_notification("vcliper", "Settings saved successfully.", 5)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
        settings_window.destroy()

    add_env_button = tk.Button(settings_window, text="Add Env", command=add_to_env)
    add_env_button.pack(pady=5)

    check_update_button = tk.Button(settings_window, text="Check Update", command=check_update)
    check_update_button.pack(pady=5)

    save_button = tk.Button(settings_window, text="Save & Close", command=save_and_close)
    save_button.pack(pady=5)


def monitor_clipboard(dictionary_path):
    global monitoring
    word_dict, case_sensitive = load_dictionary(dictionary_path)
    last_clipboard = None

    while monitoring:
        try:
            clipboard_content = pyperclip.paste()
            if clipboard_content and clipboard_content != last_clipboard:
                last_clipboard = clipboard_content
                modified_content = replace_words(clipboard_content, word_dict, case_sensitive)
                pyperclip.copy(modified_content)

        except Exception as e:
            messagebox.showerror("Clipboard Error", f"Error accessing clipboard: {e}")
        time.sleep(0.5)



def toggle_monitoring():
    global monitoring
    if monitoring:
        monitoring = False
        start_button.config(text="Start", bg="red", fg="white")
        show_notification("vcliper", "Stopping monitoring", 5)
    else:
        monitoring = True
        start_button.config(text="Stop", bg="green", fg="white")
        threading.Thread(target=monitor_clipboard, args=(dictionary_path,), daemon=True).start()
        show_notification("vcliper", "Starting monitoring", 5)


root = tk.Tk()
root.title("Clipboard Monitor")
root.geometry("300x250")

title_label = tk.Label(root, text="vCliper-Clipboard Monitor", font=("Arial", 14))
title_label.pack(pady=10)

start_button = tk.Button(root, text="Start", font=("Arial", 12), command=toggle_monitoring, bg="red", fg="white")
start_button.pack(pady=5)

settings_button = tk.Button(root, text="Settings", font=("Arial", 12), command=open_settings)
settings_button.pack(pady=5)

exit_button = tk.Button(root, text="Exit", font=("Arial", 12), command=root.quit)
exit_button.pack(pady=5)

version_label = tk.Label(root, text=f"Version {version}", font=("Arial", 10))
version_label.pack(pady=5)

version_label = tk.Label(root, text=f"3^7@Matkam/ITFP/DevOps", font=("Arial", 10))
version_label.pack(pady=5)

root.mainloop()
