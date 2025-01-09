from pathlib import Path

import ruamel.yaml

yaml = ruamel.yaml.YAML()


def load_yaml_files(directory_path):
    """
    Load all YAML (.yaml or .yml) files from a directory and merge them into a single dictionary.

    Args:
        directory_path (str): The path to the directory containing YAML files.

    Returns:
        dict: A merged dictionary containing data from all YAML files.
    """
    merged_data = {}

    # Use pathlib for better path handling
    template_path = Path(directory_path)
    if not template_path.is_dir():
        raise ValueError(f"{directory_path} is not a valid directory")

    # Iterate through all .yaml and .yml files in the directory
    for yaml_file in template_path.glob("*.yaml"):
        try:
            with yaml_file.open("r", encoding="utf-8") as file:
                data = yaml.load(file)
                if data:
                    merged_data.update(data)
        except Exception as e:
            print(f"Failed to load {yaml_file}: {e}")

    return merged_data


# Usage
directory = "templates"  # Replace with your directory path
merged_templates = load_yaml_files(directory)
print(merged_templates)
