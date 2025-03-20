import argparse
import os
from typing import Generator

# tree-sitter
import tree_sitter_bash
from tree_sitter import Language, Parser, Tree, Node

# claude

# gemini
from google import genai

# groq
from groq import Groq

# huggingface
from huggingface_hub import InferenceClient

# buffer manager
from buffmgr.buffer_manager import BufferManager

BASH_TO_PY_CONV_PROMPT = """Assistant is an Bash and Python expert. Your task is to convert the given Bash function to a to Python function.

Follow the <Instructions> to convert the Bash function to Python function.

<Instructions>
1. Convert the given Bash function to syntactically correct Python function.
2. Do not change the logic of the code.
3. Use appropriate variables and functions in Python.
4. Add necessary Python imports if required.
5. Do not remove any code.
6. Do not add add extra code such as function usage, examples and main functions other than the function definition.
7. Do not add any other text such as description, comments and explanations etc.
8. Do not merge multiple functions into a single function.
</Instructions>

<Bash_Code>
function myfunc() {{
    echo "Hello World"
}}
</Bash_Code>

<Output>:
```
def myfunc():
    print("Hello World")
```

<Bash_Code>
function myfunc() {{
    echo "Hello World"
    echo "Welcome to Assistant"
}}
</Bash_Code>

<Output>:
```
def myfunc():
    print("Hello World")
    print("Welcome to Assistant")
```

<Bash_Code>
function myfunc() {{
    echo "Hello World"
    echo "Welcome to Assistant"
    return 0
}}
</Bash_Code>

<Output>:
```
def myfunc():
    print("Hello World")
    print("Welcome to Assistant")
    return 0
```

<Bash_Code>
{bash_code}
</Bash_Code>

<Output>:
"""

def call_LLM(func_def, model, marg, verbose, file_handle):
    """Call the Language Model to generate the function definition."""
    # query = f"Convert the following shell script into a Python script.\n {func_def}"
    query = BASH_TO_PY_CONV_PROMPT.format(bash_code=func_def)
    response = get_response_from_client(marg, model, query, verbose)
    print(response) if (verbose) else None
    file_handle.write(response + "\n")

def traverse_tree(tree: Tree, model, marg, verbose, buffer_size):
    """Traverse the syntax tree and print the function definitions."""

    # import pdb; pdb.set_trace()
    buffer_manager = BufferManager(size=buffer_size)
    fn = f"func_{marg}.py"
    cursor = tree.walk()
    with open(fn, "w") as file_handle:
        file_handle.write("#!/usr/bin/env python3\n")
        file_handle.write("# -*- coding: utf-8 -*-\n")
        file_handle.write("#\n")
        file_handle.write("# Converted from shell script to python script\n")
        file_handle.write("#\n")
        for child in cursor.node.children:
            """
            if child.type == 'function_definition':
                call_LLM(child.text, model, marg, verbose, file_handle)
                continue
            """

            # Process the current node
            if not buffer_manager.add_line(child.text):
                # Call the LLM with the buffered lines
                call_LLM(buffer_manager.get_snapshot(), model, marg, verbose, file_handle)

        # Flush any remaining lines in the buffer
        if (buffer_manager.flush()):
            call_LLM(buffer_manager.get_snapshot(), model, marg, verbose, file_handle)

def get_response_from_client(marg, client, query, verbose):  
    """Get the response from the client."""
    resp = f"{marg} LLM answer: " if (verbose) else ""
    if (marg == "gemini"):
        answer = client.models.generate_content( 
                model="gemini-2.0-flash-001",
                contents=f"{query}",
        )
        resp += answer.text
    elif (marg == "groq"):
        answer = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": query}],
        )
        resp += answer.choices[0].message.content
    elif (marg == "hf"):
        answer = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3-8B-Instruct", 
            messages=[{"role": "user", "content": query}],
        )
        resp += answer.choices[0].message.content
    else:
        answer = client.messages.create(  
            max_tokens=1024,  
            messages=[{ "role": "user", "content": query }],  
            model="claude-3-5-sonnet-v2@20241022",)  
        for ans in answer.content:
            resp += ans.text

    return resp

def prepare_model(marg, verbose):
    print(marg) if (verbose) else None
 
    if (marg == "gemini"):
        print("Using gemini") if (verbose) else None
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    elif (marg == "groq"):
        print("Using groq") if (verbose) else None
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    elif (marg == "hf"):
        print("Using huggingface") if (verbose) else None
        client = InferenceClient(
            provider="hf-inference",
            api_key=os.environ.get("HUGGINGFACE_API_KEY"),
        )
    else:
        print("Using claude") if (verbose) else None
        LOCATION="us-east5" # or "europe-west1" 
        # client = AnthropicVertex(region=LOCATION, project_id="snps-ai-gemini-edag01") 

    if (verbose):
        print ("Testing the model: who were the founders of Google?")
        query = "Who were the founders of Google?" 
        response = get_response_from_client(marg, client, query, verbose)  
        print(response) 

    return client

def main():
    """Parses command-line arguments for model path and verbose mode."""

    parser = argparse.ArgumentParser(description="Example program using argparse.")
    parser.add_argument('--model', '-m', type=str, default='gemini', 
                            help='Path to the ML model(default: claude-3-5-sonnet-v2@20241022)')
    parser.add_argument('--verbose', '-v', action='store_true', 
                              help='Enable verbose output')
    parser.add_argument('--buf_sz', '-b', type=int, default=500, 
                              help='Buffer size for BufferManager (default: 500)')
    parser.add_argument('--input', '-i', type=str, required=True, 
                              help='Input file name')

    args = parser.parse_args()

    print("Model choice:", args.model)
    if args.verbose:
        print("Verbose mode enabled.")
    else:
        print("Verbose mode disabled.")

    bash_lang = Language(tree_sitter_bash.language())

    # Create a parser
    parser = Parser(bash_lang)

    # Define the source code
    with open(args.input, "r") as f:  # Read your shell script file
        shell_code = f.read()

    # Parse the source code
    mtree = parser.parse(bytes(shell_code, "utf8"))

    # find model
    client = prepare_model(args.model, args.verbose);

    # Traverse the syntax tree for VCS script
    traverse_tree(mtree, client, args.model, args.verbose, args.buf_sz)


if __name__ == "__main__":
      main()
