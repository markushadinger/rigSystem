import sys


def reload_modules(mods_to_clear=("src",)):
    keys = list(sys.modules.keys())
    print("Reloading modules:")
    for each in keys:
        for x in mods_to_clear:
            if each.startswith(x):
                sys.modules.pop(each)
                print(f"- {each}")
