import os
import streamlit as st
from git import Repo, InvalidGitRepositoryError
from datetime import datetime
import shutil
import pandas as pd
import concurrent.futures

def remove_directory(path):
    """Remove a directory and its contents, adjusting permissions if necessary."""
    def onerror(func, path, exc_info):
        os.chmod(path, 0o777)  # Adjust permissions
        func(path)

    if os.path.exists(path):
        shutil.rmtree(path, onerror=onerror)

def clone_or_update_repository(repo_url, clone_dir):
    """Clone the repository if it doesn't exist or fetch the latest changes."""
    if os.path.exists(clone_dir):
        try:
            repo = Repo(clone_dir)
            origin = repo.remotes.origin
            origin.pull()
        except Exception:
            remove_directory(clone_dir)
            repo = Repo.clone_from(repo_url, clone_dir)
    else:
        repo = Repo.clone_from(repo_url, clone_dir)
    return repo

def list_files_with_git_dates_lazy(repo, clone_dir, subdirectory_filter=None):
    """Dynamically fetch files only for the specified subdirectory."""
    for blob in repo.tree().traverse():
        if blob.type == "blob":
            subdirectory = os.path.dirname(blob.path)
            if subdirectory_filter and subdirectory_filter not in subdirectory:
                continue
            try:
                commit = next(repo.iter_commits(paths=blob.path, max_count=1))
                last_modified = datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d %H:%M:%S')
            except StopIteration:
                last_modified = "Unknown"
            yield {
                "Subdirectory": subdirectory,
                "File": os.path.basename(blob.path),
                "Last Modified": last_modified
            }

def filter_files_on_load(repo, clone_dir, subdirectory_filter=None, date_range=None):
    """Filter files as they are loaded to reduce memory usage."""
    files = list_files_with_git_dates_lazy(repo, clone_dir, subdirectory_filter)
    for file_data in files:
        if date_range:
            try:
                file_date = datetime.strptime(file_data["Last Modified"], '%Y-%m-%d %H:%M:%S').date()
                if not (date_range[0] <= file_date <= date_range[1]):
                    continue
            except ValueError:
                continue
        yield file_data

@st.cache_data
def get_filtered_files(repo_url, clone_dir, subdirectory_filter=None, date_range=None):
    """Cache the result of file filtering to improve performance."""
    repo = clone_or_update_repository(repo_url, clone_dir)
    return pd.DataFrame(filter_files_on_load(repo, clone_dir, subdirectory_filter, date_range))

def copy_files_in_parallel(selected_files, clone_dir, download_dir):
    """Copy selected files to the download directory in parallel."""
    os.makedirs(download_dir, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for _, row in selected_files.iterrows():
            relative_path = os.path.join(row["Subdirectory"], row["File"])
            source_path = os.path.join(clone_dir, relative_path)
            dest_path = os.path.join(download_dir, relative_path)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            futures.append(executor.submit(shutil.copy2, source_path, dest_path))
        concurrent.futures.wait(futures)

def main():
    st.title("Git Repository File Selector")

    # Step 1: User input for Git repository URL
    repo_url = st.text_input("Enter Git Repository URL:")

    # Step 2: Define temporary clone directory
    clone_dir = os.path.join(os.getcwd(), "temp_repo")

    if "last_repo_url" not in st.session_state:
        st.session_state.last_repo_url = ""

    if "files_loaded" not in st.session_state:
        st.session_state.files_loaded = False

    if repo_url != st.session_state.last_repo_url:
        st.session_state.last_repo_url = repo_url
        st.session_state.files_loaded = False
        if os.path.exists(clone_dir):
            remove_directory(clone_dir)

    if st.button("Clone Repository"):
        if not repo_url:
            st.error("Please provide a valid Git repository URL.")
        else:
            with st.spinner("Cloning the repository..."):
                try:
                    repo = clone_or_update_repository(repo_url, clone_dir)
                    st.success("Repository cloned successfully!")
                    st.session_state.files_loaded = True
                except Exception as e:
                    st.error("Failed to clone repository. Please check the URL or try again later.")
                    return

    # Step 3: Display files in a table with checkboxes
    if st.session_state.files_loaded:
        try:
            repo = Repo(clone_dir)

            # Extract only unique folders from the repository tree
            unique_dirs = set()
            for blob in repo.tree().traverse():
                if blob.type == "tree":  # Only include directories
                    unique_dirs.add(blob.path)

            unique_dirs = ["All"] + sorted(unique_dirs)
            subdir_filter = st.selectbox("Select Subdirectory to Filter By", unique_dirs)

            if subdir_filter == "All":
                subdir_filter = None

            unique_dates = None
            with st.spinner("Loading files..."):
                filtered_files = get_filtered_files(repo_url, clone_dir, subdir_filter)

                if not filtered_files.empty:
                    filtered_files['Last Modified'] = pd.to_datetime(filtered_files['Last Modified'], errors='coerce').dt.date
                    unique_dates = sorted(filtered_files['Last Modified'].dropna().unique())

            if unique_dates:
                start_date = st.date_input("Select Start Date", min_value=min(unique_dates), max_value=max(unique_dates), value=min(unique_dates))
                end_date = st.date_input("Select End Date", min_value=start_date, max_value=max(unique_dates), value=max(unique_dates))
                date_range = (start_date, end_date)
                filtered_files = get_filtered_files(repo_url, clone_dir, subdir_filter, date_range)

            if not filtered_files.empty:
                filtered_files["Select"] = False
                edited_df = st.data_editor(
                    filtered_files,
                    column_config={"Select": st.column_config.CheckboxColumn()},
                    use_container_width=True
                )

                selected_files = edited_df[edited_df["Select"]]

                if st.button("Download Selected Files"):
                    if selected_files.empty:
                        st.error("No files selected for download.")
                    else:
                        download_dir = os.path.expanduser("~/Downloads/git_files")
                        try:
                            copy_files_in_parallel(selected_files, clone_dir, download_dir)
                            st.success(f"Selected files downloaded to {download_dir}.")
                        except Exception:
                            st.error("Failed to download files. Please try again.")

        except InvalidGitRepositoryError:
            st.error("Failed to load repository. Please try cloning the repository again.")

if __name__ == "__main__":
    main()
