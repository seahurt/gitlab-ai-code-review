import subprocess
import os
import tempfile

class CodexRunner:
    def __init__(self, codex_path="codex"):
        self.codex_path = codex_path

    def run_review(self, content):
        """
        Saves content to a temporary file and runs codex against it.
        """
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".diff") as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            return self.run_from_file(temp_file_path)
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def run_from_file(self, file_path):
        """
        Runs codex against an existing file.
        """
        try:
            # Run codex command
            # Assuming usage: codex exec <filename> --skip-git-repo-check
            result = subprocess.run(
                [self.codex_path, 'exec', file_path, '--skip-git-repo-check'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error running codex: {e.stderr}"
        except FileNotFoundError:
            return f"Error: '{self.codex_path}' command not found."
