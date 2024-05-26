from pathlib import Path
from shutil import which
from typing import Iterable
import os
import platform


def find_program(name: str) -> Path:
    result = which(name)
    if result is None:
        raise RuntimeError(f"Program \"{name}\" not found")
    return Path(result).resolve()


def home_dir() -> Path:
    def getenv_must_exist(key: str) -> str:
        value = os.getenv(key)
        if value is not None:
            return value
        raise RuntimeError(f"Environment variable {key} not defined")

    s = platform.system()
    match s.lower():
        case "darwin": return Path(getenv_must_exist("HOME")).resolve()
        case "windows": return Path(getenv_must_exist("USERPROFILE")).resolve()
        case _: raise NotImplementedError(f"Unsupported platform \"{s}\"")


def clean_dir(dir: Path, fail_ok: bool = False) -> None:
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


def iter_files(start_dir: Path, include_suffixes: Iterable[str] | None = None, ignore_dirs: Iterable[str] | None = None) -> Iterable[Path]:
    include_suffixes = {x.lower() for x in include_suffixes} \
        if include_suffixes is not None \
        else None

    for d, ds, fs in start_dir.walk():
        if ignore_dirs is not None and len(ds) > 0:
            for ignore_dir in ignore_dirs:
                if ignore_dir in ds:
                    ds.remove(ignore_dir)

        ds.sort()
        fs.sort()

        for f in fs:
            p = d / f
            if include_suffixes is None or p.suffix.lower() in include_suffixes:
                yield p
