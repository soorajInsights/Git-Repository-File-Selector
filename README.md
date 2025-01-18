# Git Repository File Selector

## Project Description
The **Git Repository File Selector** is a Streamlit-based web application designed to interact with Git repositories. This tool allows users to:

- Clone or pull updates from a remote Git repository.
- Dynamically browse files within the repository, organized by subdirectories.
- Filter files by subdirectory or date range.
- Select files for download and save them locally in a structured format.

The app is ideal for users who need an intuitive way to explore and retrieve files from Git repositories without using command-line tools.

## Features
- **Clone Git Repositories**: Clone or update a remote Git repository with ease.
- **Subdirectory Filtering**: View files by folder structure, with an option to filter by specific subdirectories.
- **Date Range Filtering**: Narrow down file selection by last modified date.
- **File Selection and Download**: Select files using a user-friendly interface and download them to a local directory.
- **Parallel File Copying**: Speed up file downloads with parallel processing.

## Requirements
- Python 3.8+
- Dependencies (install via `requirements.txt`):
  - `streamlit`
  - `gitpython`
  - `pandas`

## Setup and Installation

1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd <repository_name>
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   streamlit run git_file_selector.py
   ```

4. Open the provided URL in your web browser to access the app.

## Usage

1. Enter the URL of a Git repository in the input field.
2. Click **"Clone Repository"** to fetch the repository content.
3. Use the dropdown to filter files by folder or leave it on "All" to view all files.
4. (Optional) Select a date range to filter files by their last modified date.
5. Check the files you wish to download and click **"Download Selected Files"**.
6. The selected files will be saved to your `Downloads/git_files` directory.

## File Structure
- **`git_file_selector.py`**: Main Streamlit app script.
- **`requirements.txt`**: List of dependencies required to run the app.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

## Author
- Sooraj K K - Developer of the Git Repository File Selector.
