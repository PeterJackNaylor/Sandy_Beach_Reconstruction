import os
import shutil
import pandas as pd
from pathlib import Path

def find_best_model_from_csv(csv_path, multiple_folder_path):
    """
    Find the best model from the CSV file that minimizes the score.
    Returns the path to the best model folder.
    """
    
    try:
        # Read the CSV file
        df = pd.read_csv(csv_path)
        
        # Assuming the CSV has columns like 'model' and 'score'
        # Find the row with the minimum score
        if 'value' in df.columns:
            min_score_idx = df['value'].idxmin()
            best_model_name = df.iloc[min_score_idx]['number']
        else:
            # If no 'score' column, try to find common metric columns
            possible_score_cols = ['loss', 'error', 'val_loss', 'mse', 'mae']
            for col in possible_score_cols:
                if col in df.columns:
                    min_score_idx = df[col].idxmin()
                    best_model_name = df.iloc[min_score_idx]['model']
                    break
            else:
                # If no common score columns found, use the first model
                print(f"Warning: No score column found in {csv_path}, using first model")
                best_model_name = df.iloc[0]['model']
        
        # Construct the full path to the best model
        best_model_path = multiple_folder_path / f"optuna_{int(best_model_name)}"
        return best_model_path
        
    except Exception as e:
        print(f"Error reading CSV {csv_path}: {e}")
        return None

def copy_model_structure(source_path, dest_path):
    """
    Copy the model structure, handling symlinks and 'multiple' folders specially.
    """
    source_path = Path(source_path)
    dest_path = Path(dest_path)
    
    # Create destination directory
    dest_path.mkdir(parents=True, exist_ok=True)
    
    for item in source_path.iterdir():
        dest_item = dest_path / item.name
        
        if item.name == 'multiple':
            # Handle multiple folder specially
            copy_multiple_folder(item, dest_item, source_path)
        elif item.is_symlink():
            # Handle symlinks by copying the actual content
            actual_path = Path(os.readlink(item))
            if not actual_path.is_absolute():
                actual_path = source_path / actual_path
            
            if actual_path.exists():
                if actual_path.is_dir():
                    shutil.copytree(actual_path, dest_item, dirs_exist_ok=True)
                else:
                    shutil.copy2(actual_path, dest_item)
            else:
                print(f"Warning: Symlink target {actual_path} does not exist")
        elif item.is_dir():
            # Recursively copy other directories
            shutil.copytree(item, dest_item, dirs_exist_ok=True)
        else:
            # Copy files
            shutil.copy2(item, dest_item)

def copy_multiple_folder(multiple_source, multiple_dest, parent_folder):
    """
    Copy only the best model from the multiple folder.
    """
    # Look for CSV file in the parent folder
    csv_files = list(parent_folder.readlink().parents[0].glob('*__trial_scores.csv'))
    if not csv_files:
        print(f"No CSV file found in {parent_folder}, copying entire multiple folder")
        shutil.copytree(multiple_source, multiple_dest, dirs_exist_ok=True)
        return
    best_params = list(parent_folder.readlink().parents[0].glob('*__best_params.csv'))[0]
    shutil.copy2(best_params, multiple_dest.parents[0])
    
    # Use the first CSV file found (you might want to adjust this logic)
    csv_file = csv_files[0]
    print(f"Using CSV file: {csv_file}")
    

    # Find the best model
    best_model_path = find_best_model_from_csv(csv_file, multiple_source)
    if best_model_path and best_model_path.exists():
        print(f"Copying best model: {best_model_path.name}")
        
        # Create the multiple folder in destination
        multiple_dest.mkdir(parents=True, exist_ok=True)
        
        # Copy the best model
        for ext in ["", ".pth", ".npz"]:
            dest_best_model = multiple_dest / (best_model_path.name + ext)
            path_to_copy = best_model_path.with_suffix(ext)
            if path_to_copy.is_dir():
                shutil.copytree(path_to_copy, dest_best_model, dirs_exist_ok=True)
            else:
                shutil.copy2(path_to_copy, dest_best_model)
    else:
        print(f"Could not find best model, copying entire multiple folder")
        shutil.copytree(multiple_source, multiple_dest, dirs_exist_ok=True)

def main():
    # Configuration
    source_folder = Path('outputs')
    destination_folder = Path('outputs_copy')  # Change this to your desired destination
    
    if not source_folder.exists():
        print(f"Source folder {source_folder} does not exist!")
        return
    
    # Find all model subfolders
    model_folders = []
    for item in source_folder.iterdir():
        if item.is_dir():
            model_folders.append(item)
    
    print(f"Found {len(model_folders)} model folders to copy")
    
    # Copy each model folder
    for model_folder in model_folders:
        print(f"\nProcessing: {model_folder.name}")
        dest_model_folder = destination_folder / model_folder.name
        copy_model_structure(model_folder, dest_model_folder)
    
    print(f"\nCopy completed! All models copied to: {destination_folder}")

if __name__ == "__main__":
    main()