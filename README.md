Natural Language Shell Helper (nlsh)
nlsh is a Python-based command-line tool that leverages a local Large Language Model (LLM) via Ollama (using the llama3.2:latest model) to generate shell commands from natural language queries. The tool gathers local system context, sends a refined prompt to Ollama, processes the JSON output, and then presents you with a numbered menu of generated commands. You can then select a command to execute on your system.

This project aims to provide a lightweight, interactive shell assistant—ideal for automating tasks on Fedora-based systems (or similar Linux distributions).

Features
Local System Context:
Automatically gathers OS, kernel, architecture, and package manager details from your system.

LLM-Powered Command Generation:
Uses a refined prompt (including system context) to generate shell commands via Ollama.

Robust JSON Parsing:
Processes the raw output from Ollama and, if needed, wraps plain text output into a JSON array. Automatically converts an array of strings into an array of objects with a "command" key.

Interactive Menu:
Presents a numbered menu of generated commands so you can choose which one to execute.

Global Installation:
Designed to be installed into your PATH (e.g. /usr/local/bin) so that you can run it from anywhere.

Requirements
Python 3:
The script is written in Python 3 and uses only standard library modules (e.g. json, subprocess, etc.).

Ollama:

Must be installed and running locally.
The model llama3.2:latest must be pulled.
Run:
bash
Copy
ollama pull llama3.2:latest
Operating System:
Tested on Fedora-based systems (or similar Linux distributions).

Installation
Clone the Repository:

bash
Copy
git clone https://github.com/yourusername/nlsh.git
cd nlsh
Make the Script Executable:

bash
Copy
chmod +x nlsh.py
Install Globally (Optional):

To run nlsh from anywhere, copy the script to a directory in your PATH (for example, /usr/local/bin):

bash
Copy
sudo cp nlsh.py /usr/local/bin/nlsh
sudo chmod +x /usr/local/bin/nlsh
Usage
Run the tool by providing a natural language query. For example:

bash
Copy
nlsh tail journalctl
What Happens
System Info:
The script gathers and displays your system information (OS, kernel, architecture, package manager).

Prompt Generation:
A refined prompt is built using your query and system context, then sent to Ollama.

LLM Output & Processing:

The raw output from Ollama is printed for debugging.
The script attempts to extract a valid JSON array. If none is found, it wraps the output as a plain-text command.
If the JSON is an array of strings, it is automatically converted to an array of objects with a "command" key.
Interactive Menu:
A numbered list of available commands is presented. You select a command by entering its number.

Command Execution:
The selected command is executed on your system. The script then reports whether the command executed successfully.

Example
Suppose you run:

bash
Copy
nlsh show docker ps
A typical session might look like:

yaml
Copy
System info: OS: fedora 41; Kernel: 6.12.9-200.fc41.x86_64; Arch: x86_64; Package Manager: dnf
Raw output:
[journalctl -n 100 --no-pager]

Generated commands:
{'command': 'journalctl -n 100 --no-pager'}

Available commands:
1) journalctl -n 100 --no-pager
Select the command number to execute (or q to quit): 1
Executing: journalctl -n 100 --no-pager
Command executed successfully.
Debugging
Raw Output Inspection:
The script prints the raw output from Ollama. If JSON parsing fails, inspect the output to adjust your prompt or extraction logic.

JSON Extraction:
The script uses a regular expression to extract the JSON array. If the output format changes, you might need to update this extraction logic.

Customization
Refining the Prompt:
You can modify the prompt string in the query_ollama() function to better suit your needs.

Modifying Postprocessing:
Adjust the regular expression in extract_json_array() if Ollama's output format changes.

Contributing
Contributions, bug reports, and feature requests are welcome! Please open an issue or submit a pull request on GitHub.

License
This project is released under the MIT License. See the LICENSE file for details.
