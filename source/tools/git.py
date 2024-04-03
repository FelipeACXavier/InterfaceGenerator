from tools.file_system import *

class Git:
    def __init__(self, src):
        self.src = src

    def clone(self, out_dir, branch=None, shallow=True, submodules=True) -> VoidResult:
        src_branch = f"--branch {branch} " if branch else ""
        shallow_cmd = "--depth 1 --shallow-submodules " if shallow else ""
        submodules_cmd = "--recurse-submodules " if submodules else ""
        command = f'git clone {submodules_cmd}{shallow_cmd}{src_branch}{self.src} {out_dir}'

        print(f'Cloning: {command}')
        return run_command(command)
