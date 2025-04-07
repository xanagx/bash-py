#!/usr/bin/env python3

import argparse

def main():
    parser = argparse.ArgumentParser(description="Process a file and label to generate stp_mt commands.")
    parser.add_argument('-c', '--commands', type=str, default='./cmds', help='Path to the commands file (default: ./cmds)')
    parser.add_argument('-l', '--label', type=str, default='label1', help='Label name (default: label1)')

    args = parser.parse_args()

    with open(args.commands, 'r') as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        if line:
            print(f'stp_mt --record "{line}" --label {args.label}')

if __name__ == "__main__":
    main()