import os
import re
import argparse
from datetime import datetime

# Define a function to extract the timestamp from the filename
def extract_timestamp(filename):
    # Regex to match the timestamp in the filename
    match = re.search(r'data_(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.\d+)\.yaml', filename)
    if match:
        timestamp_str = match.group(1)
        # Split the timestamp into the datetime part and microseconds
        dt_part, microseconds = timestamp_str.split('.')
        # Truncate microseconds to 6 digits if it's longer
        microseconds = microseconds[:6]
        # Reconstruct the timestamp string with the truncated microseconds
        truncated_timestamp_str = f"{dt_part}.{microseconds}"
        # Convert the string to a datetime object
        return datetime.strptime(truncated_timestamp_str, '%Y-%m-%dT%H-%M-%S.%f')
    return None


# Define a function to read the content of a file
def read_file_content(filepath):
    with open(filepath, 'r') as file:
        return file.read()

def process_files(input_directory, sliding_window_size=3, return_intermediates=False):
    
    if sliding_window_size < 1:
        raise Exception(f"Invalind sliding_window_size={sliding_window_size}")
    
    # Get all the .yaml files in the input directory
    files = [f for f in os.listdir(input_directory) if f.endswith('.yaml')]
    
    # Sort the files based on their extracted timestamp
    sorted_files = sorted(files, key=lambda f: extract_timestamp(f))
    
    # Apply a sliding window of size 3
    for i in range(len(sorted_files) - (sliding_window_size-1)):
        # Get the filenames in the current sliding window
        window_files = sorted_files[i:i+sliding_window_size]
        
        # Read and concatenate the contents of the three files
        combined_content = ""
        for file in window_files:
            intermediate = read_file_content(os.path.join(input_directory, file))
            combined_content += intermediate + "\n"
            if return_intermediates:
                yield intermediate
        
        yield combined_content
        

# Define the main function to process the files
def process_and_save_files(input_directory, output_directory, sliding_window_size=3):

    if sliding_window_size < 1:
        raise Exception(f"Invalind sliding_window_size={sliding_window_size}")
    
    # Get all the .yaml files in the input directory
    files = [f for f in os.listdir(input_directory) if f.endswith('.yaml')]
    
    # Sort the files based on their extracted timestamp
    sorted_files = sorted(files, key=lambda f: extract_timestamp(f))
    
    # Apply a sliding window of size 3
    for i in range(len(sorted_files) - (sliding_window_size-1)):
        # Get the filenames in the current sliding window
        window_files = sorted_files[i:i+sliding_window_size]
        
        # Create a new filename for the concatenated result
        output_filename = f'combined_{window_files[0][5:-5]}_to_{window_files[2][5:-5]}.yaml'
        output_filepath = os.path.join(output_directory, output_filename)
        
        # Read and concatenate the contents of the three files
        combined_content = ""
        for file in window_files:
            combined_content += read_file_content(os.path.join(input_directory, file)) + "\n"
        
        # Write the combined content to a new file in the output directory
        with open(output_filepath, 'w') as output_file:
            output_file.write(combined_content)
        
        print(f'Created: {output_filename}')

# Define the argument parser
def main():
    parser = argparse.ArgumentParser(description='Process YAML files using a sliding window approach.')
    parser.add_argument('--input-dir', type=str, default="./input", help='Path to the input directory containing YAML files.')
    parser.add_argument('--output-dir', type=str, default="./output", help='Path to the output directory to save combined files.')
    args = parser.parse_args()

    # Process files using the provided input and output directories
    process_and_save_files(args.input_dir, args.output_dir)

if __name__ == '__main__':
    main()
