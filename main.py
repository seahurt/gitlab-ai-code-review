import os
import argparse
import time
import json
import sys
from dotenv import load_dotenv
from src.reviewer import Reviewer

def load_agents_config():
    config_path = os.path.join(os.path.dirname(__file__), 'agents.json')
    if not os.path.exists(config_path):
        # Default config if file missing
        return {
            "codex": {
                "name": "Codex",
                "enabled": True,
                "command": "codex exec {file_path} --skip-git-repo-check"
            }
        }
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading agents.json: {e}")
        sys.exit(1)

def main():
    load_dotenv()
    
    agents_config = load_agents_config()

    parser = argparse.ArgumentParser(description="Auto Code Review for GitLab using multiple AI Agents")
    parser.add_argument("--project-id", help="GitLab Project ID (Optional)")
    parser.add_argument("--mr-iid", help="Merge Request IID (Optional. Requires --project-id)")
    parser.add_argument("--gitlab-url", default=os.getenv("GITLAB_URL"), help="GitLab URL")
    parser.add_argument("--gitlab-token", default=os.getenv("GITLAB_TOKEN"), help="GitLab Private Token")
    parser.add_argument("--log-dir", default="reviews", help="Directory to save review logs")
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode (continuously)")
    parser.add_argument("--interval", type=int, default=600, help="Check interval in seconds for daemon mode (default: 600)")
    
    # Dynamically add arguments for each agent
    for agent_key in agents_config:
        parser.add_argument(f"--{agent_key}", action="store_true", help=f"Use {agents_config[agent_key].get('name', agent_key)}")

    args = parser.parse_args()

    if not args.gitlab_url or not args.gitlab_token:
        print("Error: GITLAB_URL and GITLAB_TOKEN must be set via env vars or arguments.")
        return

    # Determine active agents
    active_agents = []
    # Check if any explicit flags were set
    explicit_selection = False
    for agent_key in agents_config:
        if getattr(args, agent_key, False):
            active_agents.append(agent_key)
            explicit_selection = True
    
    # If no explicit selection, use defaults from config
    if not explicit_selection:
        for agent_key, config in agents_config.items():
            if config.get('enabled', False):
                active_agents.append(agent_key)
    
    if not active_agents:
        print("Error: No agents selected. Enable an agent in agents.json or use a CLI flag (e.g. --codex).")
        return

    print(f"Active Agents: {', '.join(active_agents)}")

    reviewer = Reviewer(args.gitlab_url, args.gitlab_token, agents_config, active_agents, args.log_dir)

    if args.daemon:
        print(f"Starting in Daemon mode. Checking every {args.interval} seconds...")
        try:
            while True:
                print(f"\n--- Checking for reviews at {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
                reviewer.run(args.project_id, args.mr_iid)
                print(f"Waiting {args.interval} seconds for next check...")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nDaemon stopped by user.")
    else:
        reviewer.run(args.project_id, args.mr_iid)

if __name__ == "__main__":
    main()