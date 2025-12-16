import os
import json
from datetime import datetime
from .gitlab_client import GitLabClient
from .codex_runner import CodexRunner

class Reviewer:
    def __init__(self, gitlab_url, gitlab_token, codex_path="codex", log_dir="reviews"):
        self.gitlab = GitLabClient(gitlab_url, gitlab_token)
        self.codex = CodexRunner(codex_path)
        self.log_dir = log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # Load prompt
        prompt_path = os.path.join(os.path.dirname(__file__), "prompt.md")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.prompt_template = f.read()
        else:
            print(f"Warning: Prompt file not found at {prompt_path}. Using default.")
            self.prompt_template = "Review the following code changes:\n\n"

        # Load history
        self.history_file = os.path.join(self.log_dir, "history.json")
        self.history = {}
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except Exception as e:
                print(f"Error loading history file: {e}")

    def _is_processed(self, mr):
        key = f"{mr.project_id}:{mr.iid}"
        last_sha = self.history.get(key)
        current_sha = getattr(mr, 'sha', None)
        # If no sha found (unexpected), fall back to updated_at logic or False
        if not current_sha:
             return False
        return last_sha == current_sha

    def _mark_as_processed(self, mr):
        key = f"{mr.project_id}:{mr.iid}"
        current_sha = getattr(mr, 'sha', None)
        if current_sha:
            self.history[key] = current_sha
            try:
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump(self.history, f, indent=2)
            except Exception as e:
                print(f"Error saving history file: {e}")

    def run(self, project_id=None, mr_iid=None):
        if project_id and mr_iid:
            print(f"Processing single MR {mr_iid} in project {project_id}...")
            mr = self.gitlab.get_merge_request(project_id, mr_iid)
            # Force processing for manual single requests, but update history
            self._process_mr(mr)
        elif project_id:
            print(f"Fetching all open MRs for project {project_id}...")
            mrs = self.gitlab.get_open_merge_requests(project_id)
            self._process_batch(mrs)
        else:
            print("Fetching all pending reviews for current user...")
            user = self.gitlab.get_current_user()
            print(f"Authenticated as: {user.username}")
            mrs = self.gitlab.get_pending_reviews()
            self._process_batch(mrs)

    def _process_batch(self, mrs):
        if not mrs:
            print("No merge requests found.")
            return
        
        for mr in mrs:
            if self._is_processed(mr):
                # print(f"Skipping MR {mr.iid} (Project {mr.project_id}): No changes since last review.")
                continue

            print(f"Processing MR {mr.iid} (Project {mr.project_id}): {mr.title}...")
            self._process_mr(mr)

    def _process_mr(self, mr):
        print("Fetching diffs...")
        changes = self.gitlab.get_mr_diff(mr)
        
        if not changes:
            print(f"No changes found for MR {mr.iid}.")
            return

        # Prepare full context for review
        full_diff = ""
        for change in changes:
            full_diff += f"File: {change['new_path']}\n"
            full_diff += change['diff'] + "\n\n"

        # Combine Prompt + MR Info + Diff
        review_input = f"{self.prompt_template}\n\n"
        review_input += f"# Merge Request: {mr.title}\n"
        review_input += f"## Description\n{mr.description}\n\n"
        review_input += f"## Changes\n```diff\n{full_diff}\n```"

        # Generate timestamps and paths
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_filename = f"project_{mr.project_id}_mr_{mr.iid}_{timestamp}_input.md"
        input_filepath = os.path.join(self.log_dir, input_filename)
        abs_input_path = os.path.abspath(input_filepath)

        # Save input file
        try:
            with open(input_filepath, 'w', encoding='utf-8') as f:
                f.write(review_input)
            print(f"Review input saved to: {input_filepath}")
        except Exception as e:
            print(f"Failed to save review input: {e}")

        # Log command to cmd.sh
        cmd_sh_path = os.path.join(self.log_dir, "cmd.sh")
        codex_cmd = f"{self.codex.codex_path} exec {abs_input_path} --skip-git-repo-check"
        try:
            with open(cmd_sh_path, 'a', encoding='utf-8') as f:
                f.write(f"# {datetime.now()}\n")
                f.write(f"{codex_cmd}\n\n")
        except Exception as e:
            print(f"Failed to write to cmd.sh: {e}")

        print("Running Codex review...")
        review_result = self.codex.run_from_file(input_filepath)

        # Save result log locally
        result_filename = f"project_{mr.project_id}_mr_{mr.iid}_{timestamp}_result.md"
        result_filepath = os.path.join(self.log_dir, result_filename)
        try:
            with open(result_filepath, 'w', encoding='utf-8') as f:
                f.write(review_result)
            print(f"Review result saved to: {result_filepath}")
        except Exception as e:
            print(f"Failed to save review result: {e}")

        print("Posting comment to GitLab...")
        self.gitlab.post_comment(mr, f"## Automated Code Review (via Codex)\n\n{review_result}")
        
        self._mark_as_processed(mr)
        print(f"Done processing MR {mr.iid}.")

    def _save_log(self, mr, content):
        # Deprecated, logic moved to _process_mr
        pass