from pathlib import Path
from shutil import which
import os
import platform


def find_program(name):
    result = which(name)
    if result is None:
        raise RuntimeError(f"Program \"{name}\" not found")
    return Path(result).resolve()


def home_dir():
    s = platform.system()
    match s.lower():
        case "darwin": return Path(os.getenv("HOME")).resolve()
        case "windows": return Path(os.getenv("USERPROFILE")).resolve()
        case _: raise NotImplementedError(f"Unsupported platform \"{s}\"")


def clean_dir(dir, fail_ok=False):
    for root, ds, _ in dir.walk(top_down=False):
        ds.sort()
        for d in ds:
            p = root / d
            if len(list(p.iterdir())) == 0:
                if fail_ok:
                    try:
                        p.rmdir()
                    except PermissionError:
                        pass
                else:
                    p.rmdir()


def iter_files(dir, include_suffixes=None, ignore_dirs=None):
    include_suffixes = {x.lower() for x in include_suffixes} \
        if include_suffixes is not None \
        else None

    for d, ds, fs in dir.walk():
        if ignore_dirs is not None:
            for d in ignore_dirs:
                if d in ds:
                    ds.remove(d)

        ds.sort()
        fs.sort()

        for f in fs:
            p = d / f
            if include_suffixes is None or p.suffix.lower() in include_suffixes:
                yield p
