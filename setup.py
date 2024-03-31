from setuptools import setup

def setup_library_path():
    file = "env/bin/activate"
    update_cmd = "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$VIRTUAL_ENV/lib\n"
    with open(file, "r") as f:
        for line in f.readlines():
            if update_cmd in line:
                return

    with open("env/bin/activate", "a") as f:
        f.write(update_cmd)

if __name__ == '__main__':
    setup()
    setup_library_path()