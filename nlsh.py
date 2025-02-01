#!/usr/bin/env python3
import argparse
import json
import os
import platform
import re
import subprocess
import sys

def get_system_info():
    """
    Gather basic system information from /etc/os-release and platform.
    Returns a string with OS name, version, kernel, architecture, and package manager.
    """
    os_name = "unknown"
    os_version = "unknown"
    if os.path.exists("/etc/os-release"):
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID="):
                        os_name = line.split("=")[1].strip().strip('"')
                    elif line.startswith("VERSION_ID="):
                        os_version = line.split("=")[1].strip().strip('"')
        except Exception as e:
            print("Error reading /etc/os-release:", e, file=sys.stderr)
    kernel = platform.release()
    arch = platform.machine()
    pkg_manager = "dnf"
    if os_name.lower() in ("ubuntu", "debian"):
        pkg_manager = "apt-get"
    return f"OS: {os_name} {os_version}; Kernel: {kernel}; Arch: {arch}; Package Manager: {pkg_manager}"

def query_ollama(query, sys_info):
    """
    Builds the prompt and calls the local Ollama model.
    Returns the raw output (string) from Ollama.
    """
    prompt = (
        f'You are a Linux automation assistant.\n'
        f'The user\'s query is: "{query}".\n'
        f'Local system context: {sys_info}.\n'
        f'Your task is to generate a JSON array containing one or more objects.\n'
        f'Each object MUST have exactly one key "command" whose value is a single, simple, executable shell command that accomplishes the query on a Fedora system.\n'
        f'Do not output any extra keys, commentary, markdown, or escape characters.\n'
        f'Output exactly and only a valid JSON array.'
    )
    try:
        result = subprocess.run(
            ["ollama", "run", "llama3.2:latest"],
            input=prompt,
            text=True,
            capture_output=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("Error calling Ollama:", e, file=sys.stderr)
        return None

def extract_json_array(raw_output):
    """
    Attempts to extract a JSON array from raw_output by locating the first '[' and the last ']'.
    Returns the substring if found, otherwise None.
    """
    match = re.search(r'\[.*\]', raw_output, re.DOTALL)
    if match:
        return match.group(0)
    return None

def process_output(raw_output):
    """
    Cleans the raw output by trying to extract a JSON array.
    If none is found, treats the output as a plain text command and wraps it in a JSON array.
    If the JSON is an array of strings, converts it to an array of objects with a "command" key.
    Returns the resulting Python list or None on error.
    """
    json_str = extract_json_array(raw_output)
    if not json_str:
        # If no JSON array was found, assume raw_output is a plain text command.
        print("Failed to locate a JSON array in the output.", file=sys.stderr)
        print("Raw output:", raw_output, file=sys.stderr)
        # Wrap the trimmed raw output in a JSON array.
        json_str = json.dumps([raw_output.strip()])
        print("Using wrapped output:", json_str, file=sys.stderr)
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print("JSON decode error:", e, file=sys.stderr)
        print("Attempted JSON string:", json_str, file=sys.stderr)
        return None
    # Convert an array of strings to an array of objects if needed.
    if isinstance(data, list) and data and all(isinstance(item, str) for item in data):
        data = [{"command": item} for item in data]
    return data

def present_menu(commands):
    """
    Presents a numbered menu of commands to the user.
    Returns the selected command (string) or exits if the user quits.
    """
    print("Available commands:")
    for idx, cmd_obj in enumerate(commands):
        print(f"{idx+1}) {cmd_obj.get('command')}")
    choice = input("Select the command number to execute (or q to quit): ").strip()
    if choice.lower() == 'q':
        sys.exit(0)
    try:
        index = int(choice) - 1
        if index < 0 or index >= len(commands):
            print("Invalid selection.")
            sys.exit(1)
        return commands[index]["command"]
    except ValueError:
        print("Invalid input. Exiting.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Natural Language Shell Helper using Ollama (Python version)"
    )
    parser.add_argument("query", nargs="+", help="The natural language query to generate shell commands for")
    args = parser.parse_args()
    
    query = " ".join(args.query)
    sys_info = get_system_info()
    print("System info:", sys_info)
    
    raw_output = query_ollama(query, sys_info)
    if raw_output is None:
        print("Failed to get output from Ollama.", file=sys.stderr)
        sys.exit(1)
    
    # For development: print the raw output for debugging.
    print("Raw output:")
    print(raw_output)
    
    commands = process_output(raw_output)
    if not commands or not isinstance(commands, list):
        print("No valid commands found in Ollama output.", file=sys.stderr)
        sys.exit(1)
    
    print("Generated commands:")
    for cmd in commands:
        print(cmd)
    
    selected_command = present_menu(commands)
    print(f"Executing: {selected_command}")
    ret = subprocess.call(selected_command, shell=True)
    if ret == 0:
        print("Command executed successfully.")
    else:
        print(f"Command failed with exit code {ret}.")

if __name__ == "__main__":
    main()
