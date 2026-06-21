import os
import json
import sys
import traceback
import tkinter as tk
from tkinter import filedialog

def get_current_dir():
    """Gets the folder where the EXE or script is physically located"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        return os.path.dirname(os.path.abspath(__file__))

def select_folder_via_gui(initial_dir):
    """Brings up a Windows Folder Selection dialog if the tool looks in the wrong place"""
    print(" Launching folder selector... Please choose the folder containing your subtitles.")
    root = tk.Tk()
    root.withdraw() # Hide the main tiny tkinter window
    root.attributes('-topmost', True) # Bring the folder picker to the front
    
    selected_dir = filedialog.askdirectory(
        title="Select the folder containing your subtitle JSON files",
        initialdir=initial_dir
    )
    return selected_dir

def get_language_files(base_dir):
    """Scans the designated folder for actual game language files"""
    try:
        all_files = [f for f in os.listdir(base_dir) if f.endswith('.json')]
    except Exception as e:
        print(f"\n Failed to scan directory: {e}")
        return []
        
    lang_files = []
    # Exclude non-language assets
    exclude_files = ['sound.json', 'merged_subtitles.json', 'manifest.json', 'config.json', 'ctac.json', 'ecoscore_config.json']
    
    for f in all_files:
        f_lower = f.lower()
        if f_lower in exclude_files or f_lower.startswith('merged_'):
            continue
        # Only include actual language files (like zhCN.json, enGB.json, trTR.json)
        lang_files.append(f)
            
    return sorted(lang_files)

def merge_logic(dir_path, file1, file2, output_file):
    """Core merging logic"""
    path1 = os.path.join(dir_path, file1)
    path2 = os.path.join(dir_path, file2)
    path_out = os.path.join(dir_path, output_file)

    with open(path1, 'r', encoding='utf-8') as f1, open(path2, 'r', encoding='utf-8') as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)

    strings1 = data1.get("strings", data1)
    strings2 = data2.get("strings", data2)

    if not isinstance(strings1, dict) or not isinstance(strings2, dict):
        raise ValueError("JSON standard structure error. Expected a dictionary style container.")

    merged_data = {}
    all_keys = set(strings1.keys()).union(strings2.keys())

    for key in sorted(all_keys):
        item1 = strings1.get(key, {})
        item2 = strings2.get(key, {})

        text1 = item1.get("Text", item1) if isinstance(item1, dict) else item1
        text2 = item2.get("Text", item2) if isinstance(item2, dict) else item2
        
        text1 = str(text1).strip() if text1 is not None else ""
        text2 = str(text2).strip() if text2 is not None else ""

        offset = 0
        if isinstance(item1, dict):
            offset = item1.get("Offset", 0)
        elif isinstance(item2, dict):
            offset = item2.get("Offset", 0)

        if text1 and text2:
            if text1 != text2:
                merged_text = f"{text1}({text2})"
            else:
                merged_text = text1
        elif text1:
            merged_text = text1
        else:
            merged_text = text2

        merged_data[key] = {
            "Offset": offset,
            "Text": merged_text
        }

    output_data = {"strings": merged_data}
    
    with open(path_out, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    print(f"\n Success! Merged subtitles saved to: {path_out}")

def main():
    print("="*50)
    print("      Bilingual Subtitle JSON Merger (v1.5)")
    print("="*50)
    
    # 1. Try automatic detection first
    current_dir = get_current_dir()
    files = get_language_files(current_dir)
    
    # 2. If it scanned system telemetry files or nothing instead of your subtitles, force a manual pick
    if not files or "DefaultQuestions.json" in os.listdir(current_dir) or "ctac.json" in files:
        print(" Automatic path detection mismatched Windows environment.")
        current_dir = select_folder_via_gui(current_dir)
        if not current_dir:
            print(" No folder selected. Operation cancelled.")
            return
        files = get_language_files(current_dir)

    print(f"\nTarget Folder: {current_dir}")
    if not files:
        print(" No valid language JSON files found in the selected directory.")
        print(" Make sure the folder contains files like zhCN.json, enGB.json, etc.")
        return

    print("\nAvailable language files detected:")
    for idx, f in enumerate(files):
        print(f" [{idx + 1}] {f}")

    while True:
        try:
            choice1 = int(input("\nSelect [PRIMARY LANGUAGE] (displayed first) by number: "))
            if 1 <= choice1 <= len(files):
                file1 = files[choice1 - 1]
                break
            print(f"Invalid choice. Please enter a number between 1 and {len(files)}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

    while True:
        try:
            choice2 = int(input("Select [SECONDARY LANGUAGE] (inside parentheses) by number: "))
            if 1 <= choice2 <= len(files):
                if choice2 == choice1:
                    print(" Cannot select the same file. Please choose a different language.")
                    continue
                file2 = files[choice2 - 1]
                break
            print(f"Invalid choice. Please enter a number between 1 and {len(files)}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

    lang1_name = file1.split('.')[0]
    lang2_name = file2.split('.')[0]
    output_file = f"merged_{lang1_name}_{lang2_name}.json"

    print(f"\n Merging: {file1} + {file2} -> {output_file}...")
    merge_logic(current_dir, file1, file2, output_file)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\n [CRITICAL ERROR OCCURRED] ")
        traceback.print_exc() 
    finally:
        print("\n" + "="*50)
        input("Program finished. Press Enter to close this window...")