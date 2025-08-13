"""
NC1 File Processor - Bolt Slot Adjustment Tool

This script processes NC1 (Numerical Control) files to automatically adjust bolt slot cutting plans.
It searches for specific "BO" (Bolt Operation) blocks in the files and increments certain V parameter 
values, which is commonly used in CNC machining to adjust cutting depths or positions.

Features:
- Batch processing of all files in input folder
- Handles multiple BO blocks within each file
- Increments 4th parameter of V lines by specified amount
- Visual feedback through dialog boxes
- Error handling for individual files
"""

import os
import glob
import shutil
import tkinter as tk
from tkinter import messagebox, simpledialog


def cleanup_wip_folder():
    """
    Remove all files and subfolders in the wip folder to clean up after processing.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    wip_folder = os.path.join(script_dir, "wip")
    
    if not os.path.exists(wip_folder):
        return
    
    try:
        # Remove all contents of wip folder
        for item in os.listdir(wip_folder):
            item_path = os.path.join(wip_folder, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)  # Remove directory and all its contents
                print(f"Removed directory: {item}")
            else:
                os.remove(item_path)  # Remove file
                print(f"Removed file: {item}")
        
        print("WIP folder cleanup completed successfully.")
        
    except Exception as e:
        print(f"Error during WIP folder cleanup: {str(e)}")
        # Don't show error dialog for cleanup issues, just log it


def process_nc1_lines(lines, adjust_number):
    """
    Process individual NC1 file lines to adjust V parameters in BO blocks.
    
    Args:
        lines (list): List of file lines to process
        adjust_number (float): Amount to add to the 4th parameter of V lines
    
    Returns:
        list: Processed lines with adjusted V parameter values
    
    Processing Logic:
    - Searches for BO (Bolt Operation) blocks
    - Within BO blocks, finds V parameter lines with format: "v x y z value"
    - Increments the 4th parameter (value) by adjust_number
    - Handles multiple BO blocks in the same file
    - Preserves original formatting and spacing
    """
    processed_lines = []
    processing_bo_block = False  # Flag to track if we're inside a BO block

    for line in lines:
        # Check if we're entering a BO (Bolt Operation) block
        if line.strip() == "BO":
            processing_bo_block = True  # Start processing BO block
            processed_lines.append(line)
            continue

        # Process lines within BO blocks
        if processing_bo_block:
            # Check if we're exiting the BO block
            if line.strip() == "EN":
                processing_bo_block = False  # Stop processing BO block
                processed_lines.append(line)
                continue

            # Parse V parameter lines within BO blocks
            parts = line.strip().split()
            # Check if line has V parameter format: "v x y z value" (4 parts starting with 'v')
            if parts[0].lower() == "v":
                try:
                    # Extract the 4th parameter (cutting depth/position)
                    old_value = float(parts[3])
                    # Increment the value by the specified adjustment amount
                    parts[3] = f"{old_value + adjust_number:.2f}"
                    # Reconstruct the line with proper spacing
                    new_line = "  " + "  ".join(parts) + "\n"
                    processed_lines.append(new_line)
                except ValueError:
                    # If value can't be parsed as float, keep original line
                    processed_lines.append(line)
            else:
                # Non-V parameter lines within BO block, keep as-is
                processed_lines.append(line)
        else:
            # Lines outside BO blocks, keep as-is
            processed_lines.append(line)

    return processed_lines


def organize_files_by_thickness():
    """
    Organize files from input folder to wip subfolders based on thickness values from lines 13, 14, 15.
    Creates folders named "thk_{value}mm" in wip folder and copies files with matching thickness values.
    
    Returns:
        dict: Dictionary mapping thickness values to folder paths
    """
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        input_folder = os.path.join(script_dir, "input")
        wip_folder = os.path.join(script_dir, "wip")
        
        # Create wip folder if it doesn't exist
        os.makedirs(wip_folder, exist_ok=True)
        
        # Check if input folder exists
        if not os.path.exists(input_folder):
            messagebox.showerror(
                "Input Folder Missing", 
                f"Input folder not found at:\n{input_folder}\n\n"
                "Please create an 'input' folder in the same directory as this script."
            )
            return {}
        
        # Get all files in the input folder
        input_files = [f for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))]
        
        if not input_files:
            messagebox.showwarning(
                "No Files", 
                f"No files found in the input folder:\n{input_folder}\n\n"
                "Please place files in the input folder first."
            )
            return {}
        
        # Dictionary to track thickness values and their corresponding folders
        thickness_folders = {}
        files_organized = 0
        
        for filename in input_files:
            file_path = os.path.join(input_folder, filename)
            
            try:
                # Read lines 13, 14, 15 from the file
                with open(file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                
                # Check if file has at least 15 lines
                if len(lines) < 15:
                    print(f"Skipping {filename}: File has less than 15 lines")
                    continue
                
                # Extract thickness values from lines 13, 14, 15 (0-indexed: lines 12, 13, 14)
                thickness_values = []
                for line_idx in [12, 13, 14]:  # Lines 13, 14, 15 (0-indexed)
                    try:
                        thickness = float(lines[line_idx].strip())
                        thickness_values.append(thickness)
                    except (ValueError, IndexError):
                        print(f"Error reading thickness value from line {line_idx + 1} in {filename}")
                        thickness_values.append(None)
                        break
                
                # Check if all three thickness values are the same and valid
                if len(thickness_values) == 3 and thickness_values[0] is not None:
                    if thickness_values[0] == thickness_values[1] == thickness_values[2]:
                        thickness = thickness_values[0]
                        
                        # Create folder name
                        folder_name = f"thk_{thickness:.2f}mm"
                        thickness_folder = os.path.join(wip_folder, folder_name)
                        
                        # Create folder if it doesn't exist
                        os.makedirs(thickness_folder, exist_ok=True)
                        
                        # Copy file to the appropriate folder (don't move, keep original)
                        destination_path = os.path.join(thickness_folder, filename)
                        shutil.copy2(file_path, destination_path)
                        
                        # Track the folder
                        if thickness not in thickness_folders:
                            thickness_folders[thickness] = thickness_folder
                        
                        files_organized += 1
                        print(f"Copied {filename} to {folder_name} (thickness: {thickness:.2f})")
                    else:
                        print(f"Skipping {filename}: Thickness values don't match - {thickness_values}")
                else:
                    print(f"Skipping {filename}: Invalid thickness values - {thickness_values}")
                    
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
        
        # Show summary
        if files_organized > 0:
            summary_msg = f"File organization completed!\n\n"
            summary_msg += f"Files organized: {files_organized}\n"
            summary_msg += f"Thickness folders created: {len(thickness_folders)}\n\n"
            summary_msg += "Folders created in wip:\n"
            for thickness, folder in thickness_folders.items():
                folder_name = os.path.basename(folder)
                summary_msg += f"• {folder_name}\n"
            
            messagebox.showinfo("Organization Complete", summary_msg)
            print(f"\nTotal files organized: {files_organized}")
            print(f"Thickness folders: {list(thickness_folders.keys())}")
        else:
            messagebox.showwarning("No Files Organized", "No files were organized. Please check the file formats and thickness values.")
        
        return thickness_folders
        
    except Exception as e:
        # Clean up wip folder if organization fails
        cleanup_wip_folder()
        error_msg = f"Error during file organization: {str(e)}"
        print(error_msg)
        messagebox.showerror("Organization Error", error_msg)
        return {}


def process_files_by_thickness_folders():
    """
    Organize files from input folder to wip subfolders by thickness.
    This function only organizes files and doesn't process them.
    """
    try:
        # Organize files by thickness from input to wip
        thickness_folders = organize_files_by_thickness()
        
        if not thickness_folders:
            # Clean up wip folder if organization failed
            cleanup_wip_folder()
            return
        
        # Count files in each thickness folder
        folder_file_counts = {}
        total_files = 0
        for thickness, folder_path in thickness_folders.items():
            file_count = len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])
            folder_file_counts[thickness] = file_count
            total_files += file_count
        
        # Build detailed message with file counts
        detail_msg = f"Files have been organized into {len(thickness_folders)} thickness folders in 'wip' directory.\n\n"
        detail_msg += f"Total files organized: {total_files}\n\n"
        detail_msg += "Folder details:\n"
        for thickness in sorted(folder_file_counts.keys()):
            file_count = folder_file_counts[thickness]
            detail_msg += f"• thk_{thickness:.2f}mm: {file_count} file{'s' if file_count != 1 else ''}\n"
        detail_msg += "\nNext, the adjustment processing will begin automatically."
        
        # Show completion message
        messagebox.showinfo("Organization Complete", detail_msg)
        
        # Automatically run adjust_all_files after organization
        adjust_all_files()
        
    except Exception as e:
        # Clean up wip folder if any error occurs
        cleanup_wip_folder()
        error_msg = f"Error during thickness-based processing: {str(e)}"
        print(error_msg)
        messagebox.showerror("Processing Error", error_msg)
    finally:
        # Always clean up wip folder after processing (success or failure)
        cleanup_wip_folder()


def adjust_all_files():
    """
    Process all files in wip subfolders and save adjusted results to output subfolders.
    Processes each thickness folder separately.
    """
    try:
        # Get script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        wip_folder = os.path.join(script_dir, "wip")
        output_folder = os.path.join(script_dir, "output")
        
        # Check if wip folder exists
        if not os.path.exists(wip_folder):
            messagebox.showerror(
                "WIP Folder Missing", 
                f"WIP folder not found at:\n{wip_folder}\n\n"
                "Please run the thickness organization first."
            )
            return
        
        # Get all thickness subfolders in wip
        thickness_folders = {}
        for item in os.listdir(wip_folder):
            item_path = os.path.join(wip_folder, item)
            if os.path.isdir(item_path) and item.startswith("thk_") and item.endswith("mm"):
                try:
                    # Extract thickness value from folder name
                    thickness_str = item.replace("thk_", "").replace("mm", "")
                    thickness = float(thickness_str)
                    thickness_folders[thickness] = item_path
                except ValueError:
                    print(f"Skipping invalid thickness folder: {item}")
        
        if not thickness_folders:
            messagebox.showwarning(
                "No Thickness Folders", 
                f"No thickness folders found in wip directory:\n{wip_folder}\n\n"
                "Please run the thickness organization first."
            )
            return
        
        # Get adjustment numbers for each folder individually
        adjustment_values = get_adjustment_numbers_for_folders(thickness_folders)
        
        if adjustment_values is None:
            messagebox.showinfo("Cancelled", "Processing cancelled by user.")
            return
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        total_processed = 0
        
        # Process each thickness folder with its individual adjustment
        for thickness, folder_path in thickness_folders.items():
            adjust_number = adjustment_values[thickness]
            print(f"\nProcessing thickness folder: {thickness:.2f}mm with adjustment: {adjust_number:+.2f}")
            
            # Get all files in this thickness folder
            folder_files = glob.glob(os.path.join(folder_path, "*"))
            folder_processed = 0
            
            # Create output subfolder for this thickness
            thickness_output_folder = os.path.join(output_folder, f"thk_{thickness:.2f}mm")
            os.makedirs(thickness_output_folder, exist_ok=True)
            
            for file_path in folder_files:
                if os.path.isdir(file_path):
                    continue
                    
                try:
                    # Read the file
                    with open(file_path, 'r', encoding='utf-8') as file:
                        lines = file.readlines()
                    
                    # Process the lines using the adjustment for this specific folder
                    processed_lines = process_nc1_lines(lines, adjust_number)
                    
                    # Generate output file path
                    filename = os.path.basename(file_path)
                    name_without_ext, ext = os.path.splitext(filename)
                    adjusted_filename = f"{name_without_ext}_adjust_{adjust_number}mm{ext}"
                    output_path = os.path.join(thickness_output_folder, adjusted_filename)
                    
                    # Write the processed lines to output file
                    with open(output_path, 'w', encoding='utf-8') as output_file:
                        output_file.writelines(processed_lines)
                    
                    print(f"  Processed: {filename} -> {adjusted_filename}")
                    folder_processed += 1
                    total_processed += 1
                    
                except Exception as e:
                    error_msg = f"Error processing {os.path.basename(file_path)}: {str(e)}"
                    print(f"  {error_msg}")
            
            print(f"  Folder {thickness:.2f}mm: {folder_processed} files processed with adjustment {adjust_number:+.2f}")
        
        # Display final summary with individual adjustments
        summary_msg = f"Thickness-based processing completed!\n\n"
        summary_msg += f"Total files processed: {total_processed}\n"
        summary_msg += f"Thickness folders processed: {len(thickness_folders)}\n\n"
        summary_msg += "Adjustments applied:\n"
        for thickness in sorted(adjustment_values.keys()):
            adjustment = adjustment_values[thickness]
            summary_msg += f"• thk_{thickness:.2f}mm: {adjustment:+.2f}\n"
        summary_msg += f"\nOutput saved to:\n{output_folder}\n\n"
        summary_msg += "WIP folder will be cleaned up automatically."
        
        print(f"\nTotal files processed across all thickness folders: {total_processed}")
        messagebox.showinfo("Processing Complete", summary_msg)
        
    except Exception as e:
        error_msg = f"Error during file adjustment: {str(e)}"
        print(error_msg)
        messagebox.showerror("Adjustment Error", error_msg)


def get_adjustment_number():
    """
    Prompt user to enter the adjustment number for diameter modification.
    
    Returns:
        float: The adjustment number entered by user, or None if cancelled
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    # Show input dialog for adjustment number
    adjust_number = simpledialog.askfloat(
        "Adjustment Value",
        "Enter the adjustment amount to add to V parameters:\n\n"
        "Example:\n"
        "• Enter 1.0 to increase by 1.0\n"
        "• Enter -0.5 to decrease by 0.5\n"
        "• Enter 2.5 to increase by 2.5",
        initialvalue=1.0,
        minvalue=-100.0,
        maxvalue=100.0
    )
    
    root.destroy()
    return adjust_number


def get_adjustment_numbers_for_folders(thickness_folders):
    """
    Prompt user to enter adjustment amounts for all thickness folders in one multi-line dialog.
    
    Args:
        thickness_folders (dict): Dictionary mapping thickness values to folder paths
    
    Returns:
        dict: Dictionary mapping thickness values to adjustment amounts, or None if cancelled
    """
    if not thickness_folders:
        return None
    
    # Sort thickness folders for consistent order
    sorted_thicknesses = sorted(thickness_folders.keys())
    
    # Build initial text with folder information and default values
    initial_text = ""
    folder_info = "Thickness Folders Found:\n\n"
    
    for thickness in sorted_thicknesses:
        folder_name = f"thk_{thickness:.2f}mm"
        folder_path = thickness_folders[thickness]
        file_count = len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])
        
        folder_info += f"• {folder_name}: {file_count} file{'s' if file_count != 1 else ''}\n"
        initial_text += f"{thickness:.2f}=1.0\n"
    
    # Create a custom dialog for multi-line input
    root = tk.Tk()
    root.title("Adjustment Values for All Folders")
    root.geometry("600x500")
    root.resizable(True, True)
    
    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (600 // 2)
    y = (root.winfo_screenheight() // 2) - (500 // 2)
    root.geometry(f"600x500+{x}+{y}")
    
    result = None
    
    # Main frame
    main_frame = tk.Frame(root, padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    title_label = tk.Label(main_frame, text="Enter Adjustment Values", font=("Arial", 14, "bold"))
    title_label.pack(pady=(0, 10))
    
    # Information section
    info_frame = tk.Frame(main_frame)
    info_frame.pack(fill=tk.X, pady=(0, 15))
    
    info_label = tk.Label(info_frame, text=folder_info, justify=tk.LEFT, font=("Consolas", 9))
    info_label.pack(anchor=tk.W)
    
    # Instructions
    instructions = tk.Label(
        main_frame, 
        text="Enter adjustment values in format: thickness=adjustment\n"
             "Examples: 6.00=1.5, 8.00=-0.5, 10.00=2.0\n"
             "Use positive values to increase, negative to decrease\n"
             "Click 'Enter/Process' button or press Enter key to proceed:",
        justify=tk.LEFT,
        font=("Arial", 10)
    )
    instructions.pack(pady=(0, 10), anchor=tk.W)
    
    # Text input area
    text_frame = tk.Frame(main_frame)
    text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
    
    # Scrollbar for text area
    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    text_area = tk.Text(text_frame, height=8, font=("Consolas", 11), yscrollcommand=scrollbar.set)
    text_area.pack(fill=tk.BOTH, expand=True)
    text_area.insert(tk.END, initial_text)
    
    scrollbar.config(command=text_area.yview)
    
    # Button frame
    button_frame = tk.Frame(main_frame)
    button_frame.pack(fill=tk.X)
    
    def on_ok():
        nonlocal result
        try:
            text_content = text_area.get(1.0, tk.END).strip()
            lines = text_content.split('\n')
            
            adjustment_values = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if '=' not in line:
                    messagebox.showerror("Format Error", f"Invalid format in line: '{line}'\nExpected format: thickness=adjustment")
                    return
                
                parts = line.split('=', 1)
                if len(parts) != 2:
                    messagebox.showerror("Format Error", f"Invalid format in line: '{line}'\nExpected format: thickness=adjustment")
                    return
                
                try:
                    thickness = float(parts[0].strip())
                    adjustment = float(parts[1].strip())
                    
                    if thickness not in thickness_folders:
                        messagebox.showerror("Thickness Error", f"Thickness {thickness:.2f} not found in folders.\nAvailable thicknesses: {', '.join([f'{t:.2f}' for t in sorted_thicknesses])}")
                        return
                    
                    adjustment_values[thickness] = adjustment
                    
                except ValueError:
                    messagebox.showerror("Value Error", f"Invalid number format in line: '{line}'\nBoth thickness and adjustment must be numbers")
                    return
            
            # Check if all thicknesses have values
            missing_thicknesses = []
            for thickness in sorted_thicknesses:
                if thickness not in adjustment_values:
                    missing_thicknesses.append(f"{thickness:.2f}")
            
            if missing_thicknesses:
                messagebox.showerror("Missing Values", f"Missing adjustment values for thicknesses: {', '.join(missing_thicknesses)}")
                return
            
            # Show confirmation
            summary_msg = "Adjustment Summary:\n\n"
            for thickness in sorted_thicknesses:
                folder_name = f"thk_{thickness:.2f}mm"
                adjustment = adjustment_values[thickness]
                summary_msg += f"• {folder_name}: {adjustment:+.2f}\n"
            summary_msg += "\nDo you want to proceed with these adjustments?"
            
            if messagebox.askyesno("Confirm All Adjustments", summary_msg):
                result = adjustment_values
                root.destroy()
                
        except Exception as e:
            messagebox.showerror("Error", f"Error processing input: {str(e)}")
    
    def on_cancel():
        nonlocal result
        result = None
        root.destroy()
    
    def on_key_press(event):
        # Handle Enter key to trigger OK (without Ctrl)
        if event.keysym == 'Return':
            # Only process if not in text area, or if Ctrl is pressed
            if event.widget != text_area or (event.state & 0x4):
                on_ok()
        # Handle Escape key to cancel
        elif event.keysym == 'Escape':
            on_cancel()
    
    # Buttons
    ok_button = tk.Button(button_frame, text="OK", command=on_ok, width=10, font=("Arial", 10))
    ok_button.pack(side=tk.RIGHT, padx=(5, 0))
    
    cancel_button = tk.Button(button_frame, text="Cancel", command=on_cancel, width=10, font=("Arial", 10))
    cancel_button.pack(side=tk.RIGHT)
    
    # Add Enter button for processing
    enter_button = tk.Button(button_frame, text="Enter/Process", command=on_ok, width=12, font=("Arial", 10, "bold"), bg="#4CAF50", fg="white", relief="raised")
    enter_button.pack(side=tk.LEFT)
    
    # Bind keyboard events
    root.bind('<Return>', on_key_press)
    root.bind('<Control-Return>', on_key_press)
    root.bind('<Escape>', on_key_press)
    # Don't bind Return to text area to allow normal text input
    
    # Focus on text area and select all
    text_area.focus_set()
    text_area.tag_add(tk.SEL, "1.0", tk.END)
    text_area.mark_set(tk.INSERT, "1.0")
    text_area.see(tk.INSERT)
    
    # Handle window close
    root.protocol("WM_DELETE_WINDOW", on_cancel)
    
    # Run the dialog
    root.mainloop()
    
    if result:
        print("Adjustment values entered:")
        for thickness in sorted_thicknesses:
            adjustment = result[thickness]
            print(f"  thk_{thickness:.2f}mm: {adjustment:+.2f}")
    
    return result


def process_input_to_output_directly():
    """
    Process all files in the input folder directly to output folder (original method).
    
    Workflow:
    1. Prompts user for adjustment amount
    2. Scans input folder for files
    3. Creates output folder if it doesn't exist
    4. Processes each file individually
    5. Shows dialog boxes for progress feedback
    6. Handles errors gracefully without stopping batch processing
    """
    # Get adjustment number from user input
    adjust_number = get_adjustment_number()
    
    # Check if user cancelled the input dialog
    if adjust_number is None:
        messagebox.showinfo("Cancelled", "Processing cancelled by user.")
        return
    
    # Show confirmation dialog with the entered value
    root = tk.Tk()
    root.withdraw()
    confirm = messagebox.askyesno(
        "Confirm Adjustment", 
        f"You entered: {adjust_number}\n\n"
        f"This will {'increase' if adjust_number >= 0 else 'decrease'} all V parameter values "
        f"by {abs(adjust_number):.2f}\n\n"
        "Do you want to proceed?"
    )
    root.destroy()
    
    if not confirm:
        messagebox.showinfo("Cancelled", "Processing cancelled by user.")
        return
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define input and output folder paths relative to script location
    input_folder = os.path.join(script_dir, "input")
    output_folder = os.path.join(script_dir, "output")
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Check if input folder exists
    if not os.path.exists(input_folder):
        messagebox.showerror(
            "Input Folder Missing", 
            f"Input folder not found at:\n{input_folder}\n\n"
            "Please create an 'input' folder in the same directory as this script."
        )
        return
    
    # Get all files in the input folder using glob pattern
    input_files = glob.glob(os.path.join(input_folder, "*"))
    
    # Check if any files were found
    if not input_files:
        messagebox.showwarning(
            "No Files", 
            f"No files found in the input folder:\n{input_folder}\n\n"
            "Please place NC1 files in the input folder."
        )
        return
    
    # Initialize counter for successfully processed files
    processed_count = 0
    
    # Process each file in the input folder
    for file_path in input_files:
        # Skip directories, only process files
        if os.path.isdir(file_path):
            continue
            
        try:
            # Read the input file with UTF-8 encoding
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            # Process the lines using the NC1 processing function with user-specified adjustment
            processed_lines = process_nc1_lines(lines, adjust_number)
            
            # Generate output file path with adjustment suffix
            filename = os.path.basename(file_path)
            name_without_ext, ext = os.path.splitext(filename)
            adjusted_filename = f"{name_without_ext}_adjust_{adjust_number}mm{ext}"
            output_path = os.path.join(output_folder, adjusted_filename)
            
            # Write the processed lines to output file
            with open(output_path, 'w', encoding='utf-8') as output_file:
                output_file.writelines(processed_lines)
            
            # Log the processing result to console
            print(f"Processed: {filename} -> {output_path}")
            
            # Increment the successfully processed files counter
            processed_count += 1
            
        except Exception as e:
            # Handle file processing errors without stopping the batch
            error_msg = f"Error processing {os.path.basename(file_path)}:\n{str(e)}"
            print(error_msg)
            messagebox.showerror("Processing Error", error_msg)
    
    # Display final summary
    summary_msg = f"Processing completed!\n\nTotal files processed: {processed_count}\nAdjustment applied: {adjust_number:+.2f}\n\nFiles saved to:\n{output_folder}"
    print(f"\nTotal files processed: {processed_count}")
    messagebox.showinfo("Processing Complete", summary_msg)


def main_menu():
    """
    Display main menu for user to choose processing method.
    """
    root = tk.Tk()
    root.withdraw()
    
    choice = messagebox.askyesno(
        "Processing Method",
        "Choose processing method:\n\n"
        "YES: Process files by thickness (organize input to wip by thickness, then adjust wip to output)\n"
        "NO: Process all files directly (input to output, original method)\n\n"
        "Click YES for thickness-based processing or NO for direct processing."
    )
    
    root.destroy()
    
    if choice:
        # Process files by thickness folders (input->wip->output)
        process_files_by_thickness_folders()
    else:
        # Process all files directly (input->output)
        process_input_to_output_directly()


# Main execution block - only runs when script is executed directly
if __name__ == "__main__":
    main_menu()
