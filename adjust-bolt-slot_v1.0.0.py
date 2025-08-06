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
import tkinter as tk
from tkinter import messagebox, simpledialog


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


def process_all_files():
    """
    Process all files in the input folder using process_nc1_lines function
    and save the results to the output folder.
    
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


# Main execution block - only runs when script is executed directly
if __name__ == "__main__":
    process_all_files()
