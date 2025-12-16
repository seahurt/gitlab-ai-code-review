import os
import argparse
import time
from dotenv import load_dotenv
from src.reviewer import Reviewer

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Auto Code Review for GitLab using Codex CLI")
    parser.add_argument("--project-id", help="GitLab Project ID (Optional)")
    parser.add_argument("--mr-iid", help="Merge Request IID (Optional. Requires --project-id)")
    parser.add_argument("--gitlab-url", default=os.getenv("GITLAB_URL"), help="GitLab URL")
    parser.add_argument("--gitlab-token", default=os.getenv("GITLAB_TOKEN"), help="GitLab Private Token")
    parser.add_argument("--codex-path", default="codex", help="Path to codex executable")
    parser.add_argument("--log-dir", default="reviews", help="Directory to save review logs")
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode (continuously)")
    parser.add_argument("--interval", type=int, default=600, help="Check interval in seconds for daemon mode (default: 600)")
    
    args = parser.parse_args()

    if not args.gitlab_url or not args.gitlab_token:
        print("Error: GITLAB_URL and GITLAB_TOKEN must be set via env vars or arguments.")
        return

    reviewer = Reviewer(args.gitlab_url, args.gitlab_token, args.codex_path, args.log_dir)

    if args.daemon:
        print(f"Starting in Daemon mode. Checking every {args.interval} seconds...")
        try:
            while True:
                print(f"\n--- Checking for reviews at {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
                reviewer.run(args.project_id, args.mr_iid)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nDaemon stopped by user.")
    else:
        reviewer.run(args.project_id, args.mr_iid)

if __name__ == "__main__":
    main()