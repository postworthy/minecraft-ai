import argparse
import os
import yaml
import json

def find_action_paths(data, path=[]):
    paths = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'action':
                paths.append(path + [key])
            paths.extend(find_action_paths(value, path + [key]))
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            paths.extend(find_action_paths(item, path + [idx]))
    return paths

def get_from_path(data, path):
    for key in path:
        data = data[key]
    return data

def remove_from_path(data, path):
    key = path[0]
    if len(path) == 1:
        del data[key]
    else:
        remove_from_path(data[key], path[1:])

def process_yaml_file(file_path):
    with open(file_path, 'r') as f:
        data = f.read()

    # Parse the data using yaml.safe_load
    parsed_data = yaml.safe_load(data)

    # Find all action paths
    action_paths = find_action_paths(parsed_data)

    # If there are action paths, remove the last one
    if action_paths:
        last_action_path = action_paths[-1]
        last_action_data = get_from_path(parsed_data, last_action_path)
        remove_from_path(parsed_data, last_action_path)

        # Convert the modified data back to a YAML-formatted string
        human_value = yaml.dump(parsed_data, default_flow_style=False)
        gpt_value = yaml.dump({'action': last_action_data}, default_flow_style=False)
    else:
        # If no action is found, set gpt_value to an empty string
        human_value = yaml.dump(parsed_data, default_flow_style=False)
        gpt_value = ''

    # Create the output list
    output = [
        {
            "from": "human",
            "value": human_value.strip()
        },
        {
            "from": "gpt",
            "value": gpt_value.strip()
        }
    ]

    return output

def main():
    parser = argparse.ArgumentParser(description='Process YAML files to prepare them for LLM training.')
    parser.add_argument('--input-dir', type=str, default="./input", help='Path to the input directory containing YAML files.')
    parser.add_argument('--output-dir', type=str, default="./output", help='Path to the output directory to save combined files.')
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.input_dir

    # Ensure the input directory exists
    if not os.path.isdir(input_dir):
        print(f"Error: The directory '{input_dir}' does not exist.")
        return

    # Collect all YAML files in the input directory
    yaml_files = [
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if f.endswith(('.yaml', '.yml'))
    ]

    if not yaml_files:
        print(f"No YAML files found in directory '{input_dir}'.")
        return

    for file_path in yaml_files:
        try:
            output_filename, ext = os.path.splitext(os.path.basename(file_path))
            output = process_yaml_file(file_path)
            output_filename = f'{output_filename}.json'
            output_filepath = os.path.join(output_dir, output_filename)
            with open(output_filepath, 'w') as output_file:
                json.dump(output, output_file, indent=2)
        except Exception as e:
            print(f"Error processing file '{file_path}': {e}")

if __name__ == "__main__":
    main()
