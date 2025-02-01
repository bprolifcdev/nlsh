#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys

# Store command execution history
command_history = []

def get_system_info():
    """
    Gather basic system information and return it as a formatted string.
    """
    try:
        os_name = subprocess.run(["uname", "-o"], capture_output=True, text=True).stdout.strip()
        kernel = subprocess.run(["uname", "-r"], capture_output=True, text=True).stdout.strip()
        arch = subprocess.run(["uname", "-m"], capture_output=True, text=True).stdout.strip()
        package_manager = "dnf" if os.path.exists("/usr/bin/dnf") else "apt-get"
        return f"OS: {os_name}; Kernel: {kernel}; Arch: {arch}; Package Manager: {package_manager}"
    except Exception as e:
        return f"Error gathering system info: {e}"

def command_exists(command):
    """
    Check if a command exists using 'command -v'.
    """
    cmd = command.split()[0]
    result = subprocess.run(["command", "-v", cmd], capture_output=True, text=True)
    return result.returncode == 0

def is_command_valid(command):
    """
    Validate the command by checking its existence and testing --help.
    """
    cmd_parts = command.split()
    if len(cmd_parts) > 1:
        try:
            result = subprocess.run([cmd_parts[0], "--help"], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    return True

def extract_json_array(raw_output):
    """
    Extracts a JSON array from raw_output if present.
    """
    try:
        # Use regex to extract only the JSON portion
        match = re.search(r"\[\s*{.*?}\s*\]", raw_output, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            print("⚠️ No valid JSON found. Treating as plaintext command.", file=sys.stderr)
            return None
    except json.JSONDecodeError:
        print("❌ JSON Parsing Error: Could not decode valid JSON.", file=sys.stderr)
        return None

def process_output(raw_output):
    """
    Processes AI-generated commands and filters out invalid ones.
    """
    commands = extract_json_array(raw_output)
    if not commands:
        print("⚠️ No valid JSON found. Treating as plaintext command.", file=sys.stderr)
        commands = [raw_output.strip()]
    
    if isinstance(commands, list) and all(isinstance(cmd, str) for cmd in commands):
        commands = [{"command": cmd} for cmd in commands]
    
    valid_commands = [cmd for cmd in commands if command_exists(cmd["command"])]
    
    if not valid_commands:
        print("❌ No valid commands found. AI might have generated incorrect commands.", file=sys.stderr)
        return None
    
    return valid_commands

def present_menu(commands):
    """
    Presents a menu of generated commands for selection.
    """
    print("\n📋 Available Commands:")
    for i, cmd_obj in enumerate(commands):
        print(f"{i+1}) {cmd_obj.get('command')}")
    choice = input("\nSelect command number to execute (or q to quit): ").strip()
    if choice.lower() == 'q':
        sys.exit(0)
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(commands):
            print("❌ Invalid selection.")
            sys.exit(1)
        return commands[idx]["command"]
    except ValueError:
        print("❌ Invalid input. Exiting.")
        sys.exit(1)

def execute_command(command):
    """
    Executes the selected command with safety checks and tracks history.
    """
    global command_history
    if not is_command_valid(command):
        print(f"⚠️ Skipping invalid command: {command}")
        return
    
    print(f"\n➡️ Executing: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        command_history.append({"command": command, "status": "success" if result.returncode == 0 else "failed", "output": result.stderr if result.returncode else result.stdout})
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"⚠️ Command failed with exit code {result.returncode}: {command}")
            print(result.stderr)
    except Exception as e:
        command_history.append({"command": command, "status": "error", "output": str(e)})
        print(f"⚠️ Error executing command: {e}")

def query_ollama(query):
    """
    Generates shell commands using Ollama with system context and execution history.
    """
    sys_info = get_system_info()

    # Format command history into a readable context
    history_context = "\n".join([f"- {entry['command']} (Status: {entry['status']})" for entry in command_history[-5:]])

    full_prompt = f"""
    You are a command-line assistant helping users execute shell commands efficiently.
    The user is running a system with the following specifications:
    {sys_info}

    Previous command history:
    {history_context if history_context else "No previous commands"}

    Generate a single valid shell command based on the following query:
    "{query}"

    If a previous command failed, correct the mistake in your response.

    Respond in JSON format as:
    [
        {{"command": "actual_command_here"}}
    ]
    """
    try:
        result = subprocess.run(["ollama", "run", "llama3.2:latest"], input=full_prompt, text=True, capture_output=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("❌ Failed to get output from Ollama.", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Natural Language Shell Helper using Ollama")
    parser.add_argument("query", nargs="+", help="The natural language query to generate shell commands for")
    args = parser.parse_args()

    query = " ".join(args.query)
    print("🔍 System info:", get_system_info())

    raw_output = query_ollama(query)
    print("\n📝 Raw output from Ollama:\n", raw_output)

    commands = process_output(raw_output)
    if not commands:
        print("❌ No valid commands found.", file=sys.stderr)
        sys.exit(1)

    selected_command = present_menu(commands)
    execute_command(selected_command)

if __name__ == "__main__":
    main()
