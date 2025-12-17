import gitlab
import os

import subprocess
import json
import urllib.parse

class GitLabClient:
    def __init__(self, url, token):
        self.url = url.rstrip('/')
        self.token = token

    def _curl(self, method, path, data=None):
        api_url = f"{self.url}/api/v4{path}"
        cmd = [
            "curl", "-s", "-X", method,
            "-H", f"PRIVATE-TOKEN: {self.token}",
            "-H", "Content-Type: application/json",
            api_url
        ]
        
        if data:
            cmd.extend(["-d", json.dumps(data)])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if not result.stdout:
                return None
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error calling GitLab API: {e}")
            print(f"Stdout: {e.stdout}")
            print(f"Stderr: {e.stderr}")
            raise
        except json.JSONDecodeError:
            print(f"Failed to decode JSON from {api_url}")
            print(f"Response: {result.stdout}")
            raise

    def _curl_text(self, method, path):
        api_url = f"{self.url}/api/v4{path}"
        cmd = [
            "curl", "-s", "-X", method,
            "-H", f"PRIVATE-TOKEN: {self.token}",
            api_url
        ]
        
        try:
            # Use text=False to get bytes, preventing crash on binary data
            result = subprocess.run(cmd, capture_output=True, text=False, check=True)
            try:
                return result.stdout.decode('utf-8')
            except UnicodeDecodeError:
                print(f"Warning: Failed to decode content from {path}. Treating as binary.")
                return None
        except subprocess.CalledProcessError as e:
            print(f"Error calling GitLab API (Raw): {e}")
            return None

    def get_current_user(self):
        user_data = self._curl("GET", "/user")
        # Return a simple object or dict that mimics what we need
        return type('User', (object,), user_data)()

    def get_merge_request(self, project_id, mr_iid):
        mr_data = self._curl("GET", f"/projects/{project_id}/merge_requests/{mr_iid}")
        return self._wrap_mr(mr_data)

    def get_open_merge_requests(self, project_id):
        mrs_data = self._curl("GET", f"/projects/{project_id}/merge_requests?state=opened")
        if not isinstance(mrs_data, list):
            print(f"Error fetching MRs for project {project_id}: {mrs_data}")
            return []
        return [self._wrap_mr(mr) for mr in mrs_data]

    def get_pending_reviews(self):
        user = self.get_current_user()
        # scope=all, state=opened, reviewer_id=user.id
        path = f"/merge_requests?scope=all&state=opened&reviewer_id={user.id}"
        mrs_data = self._curl("GET", path)
        if not isinstance(mrs_data, list):
            print(f"Error fetching pending reviews: {mrs_data}")
            return []
        return [self._wrap_mr(mr) for mr in mrs_data]

    def get_raw_file(self, project_id, file_path, ref):
        encoded_path = urllib.parse.quote(file_path, safe='')
        path = f"/projects/{project_id}/repository/files/{encoded_path}/raw?ref={ref}"
        return self._curl_text("GET", path)

    def get_mr_diff(self, mr):
        # mr is the object returned by _wrap_mr
        path = f"/projects/{mr.project_id}/merge_requests/{mr.iid}/changes"
        data = self._curl("GET", path)
        changes = data.get('changes', [])
        
        for change in changes:
            # If new file and diff is empty, fetch raw content
            # Ensure it's not marked as binary by GitLab
            if change.get('new_file') and not change.get('diff') and not change.get('binary'):
                source_project_id = getattr(mr, 'source_project_id', mr.project_id)
                sha = getattr(mr, 'sha', None)
                if not sha:
                    # Try getting sha from diff_refs if available
                    pass
                
                if source_project_id and sha:
                    print(f"Fetching raw content for new file: {change['new_path']}")
                    content = self.get_raw_file(source_project_id, change['new_path'], sha)
                    if content:
                        # Construct a pseudo-diff
                        lines = content.splitlines()
                        diff_lines = [f"+{line}" for line in lines]
                        change['diff'] = "\n".join(diff_lines)
                    else:
                        print(f"Skipping binary or undecodable content for: {change['new_path']}")
        
        return changes

    def post_comment(self, mr, body):
        path = f"/projects/{mr.project_id}/merge_requests/{mr.iid}/notes"
        self._curl("POST", path, {"body": body})

    def _wrap_mr(self, data):
        # Create a simple object to allow dot notation access (mr.iid, mr.project_id, mr.title)
        class MR:
            def __init__(self, d):
                self.__dict__.update(d)
        return MR(data)

