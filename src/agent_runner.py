import subprocess
import os
import shlex

class AgentRunner:
    def __init__(self):
        pass

    def run_from_file(self, file_path, command_template):
        """
        Runs an agent command against an existing file.
        """
        # Replace placeholder with actual file path
        # We wrap file_path in quotes just in case, though shlex might handle it better if we pass args list.
        # But since we are templating a string, we simply replace.
        command_str = command_template.replace("{file_path}", file_path)
        
        try:
            # Parse command string into args list
            args = shlex.split(command_str)
            
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error running agent: {e.stderr}"
        except FileNotFoundError:
            return f"Error: Command not found in: {args[0] if args else command_str}"
        except Exception as e:
            return f"Error: {e}"
