#! /usr/bin/env python3

import os
import subprocess
from typing import List, Optional
from tempfile import NamedTemporaryFile, TemporaryDirectory
from dataclasses import dataclass

DISABLE_CHECK = "<!-- no-check -->"
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
README = os.path.join(ROOT_DIR, 'README.md')

print(f"Checking {README}")

with open(README) as f:
    lines = f.readlines()


@dataclass
class Block:
    lang: str
    check: bool
    content: str = ""


blocks: List[Block] = []

last_block: Optional[Block] = None
check_next = True
for line in lines:
    if line.startswith("```"):
        if last_block is None:
            last_block = Block(line[3:].strip(), check_next)
            check_next = True
        else:
            blocks.append(last_block)
            last_block = None
    elif line.startswith(DISABLE_CHECK):
        if last_block:
            raise Exception(f"Found '{DISABLE_CHECK}' within block")
        else:
            check_next = False
    else:
        if last_block is not None:
            last_block.content += line

print(f"Found {len(blocks)} code blocks:")

with TemporaryDirectory() as tmp_dir:
    # Create these files as some snippets rely on them
    open(os.path.join(tmp_dir, "aas.aasx"), "w")
    open(os.path.join(tmp_dir, "aas.json"), "w")
    open(os.path.join(tmp_dir, "aas.xml"), "w")

    skipped = 0
    for block in blocks:
        if not block.check:
            skipped += 1
            continue
        with NamedTemporaryFile(mode="w") as f:
            print("-"*10)
            print(block.content)
            print("-"*10)
            f.write(block.content)
            f.flush()
            pypath = ROOT_DIR
            try:
                pypath += f"{os.pathsep}{os.environ['PYTHONPATH']}"
            except KeyError:
                pass
            subprocess.check_call(["python", f.name], env={'PYTHONPATH': pypath}, cwd=tmp_dir)
    assert skipped == 7, skipped
