"""Private GitHub release updates. Network and filesystem work runs off the UI thread."""
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile

from . import bootstrap, core
from .version import VERSION, REPOSITORY, RELEASE_ASSET

MAX_DOWNLOAD = 100 * 1024 * 1024


class AccessRequired(RuntimeError):
    pass


def version_tuple(value):
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        raise ValueError("Invalid version: " + str(value))
    return tuple(map(int, match.groups()))


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


def _protect(data, decrypt=False):
    if os.name != "nt":
        raise RuntimeError("Protected credential storage requires Windows.")
    buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    source = _Blob(len(data), buffer)
    result = _Blob()
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    function = crypt32.CryptUnprotectData if decrypt else crypt32.CryptProtectData
    function.argtypes = [ctypes.POINTER(_Blob), ctypes.c_void_p, ctypes.c_void_p,
                         ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_Blob)]
    function.restype = wintypes.BOOL
    if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(result)):
        raise RuntimeError("Could not access the Windows-protected credential.")
    try:
        return ctypes.string_at(result.pbData, result.cbData)
    finally:
        kernel32.LocalFree(result.pbData)


def token_path(data_dir=bootstrap.DATA):
    return Path(data_dir) / "cream-github-access.dpapi"


def save_token(token, data_dir=bootstrap.DATA):
    token = token.strip()
    if not token or any(c.isspace() for c in token):
        raise ValueError("Enter a valid GitHub token without whitespace.")
    encrypted = _protect(token.encode("utf-8"))
    path = token_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_bytes(encrypted)
    os.replace(temp, path)


def load_token(data_dir=bootstrap.DATA):
    value = os.environ.get("CREAM_GITHUB_TOKEN", "").strip()
    if value:
        return value
    path = token_path(data_dir)
    return _protect(path.read_bytes(), decrypt=True).decode("utf-8") if path.exists() else ""


class _GitHubRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlparse(newurl)
        host = parsed.hostname or ""
        if parsed.scheme != "https" or not (host == "github.com" or host.endswith(".github.com") or host.endswith(".githubusercontent.com")):
            raise RuntimeError("Download redirect outside GitHub was refused.")
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None and host != urllib.parse.urlparse(req.full_url).hostname:
            redirected.remove_header("Authorization")
        return redirected


def _request(path, token, binary=False):
    if not path.startswith("/repos/" + REPOSITORY + "/"):
        raise ValueError("Invalid update endpoint.")
    headers = {"User-Agent": "CREAM/" + VERSION, "X-GitHub-Api-Version": "2022-11-28",
               "Accept": "application/octet-stream" if binary else "application/vnd.github+json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request("https://api.github.com" + path, headers=headers)
    try:
        return urllib.request.build_opener(_GitHubRedirect()).open(req, timeout=20)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 404):
            raise AccessRequired("Configure a token with read access to the private repository " + REPOSITORY + ".") from None
        if exc.code == 403:
            raise RuntimeError("GitHub refused the request: check token permissions or try again later.") from None
        raise RuntimeError("GitHub returned HTTP " + str(exc.code) + ".") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise RuntimeError("Cannot connect to GitHub. The plugin remains available; try checking again later.") from None


def _release_request(path, token=None, binary=False, data_dir=bootstrap.DATA):
    if token is not None:
        return _request(path, token, binary=binary)
    try:
        return _request(path, "", binary=binary)
    except AccessRequired:
        credential = load_token(data_dir)
        if not credential:
            raise
        return _request(path, credential, binary=binary)


def check_latest(current=VERSION, token=None):
    with _release_request("/repos/" + REPOSITORY + "/releases/latest", token) as response:
        data = response.read(2 * 1024 * 1024 + 1)
    if len(data) > 2 * 1024 * 1024:
        raise ValueError("The GitHub response is too large.")
    release = json.loads(data)
    if release.get("draft") or release.get("prerelease"):
        return None
    tag = release["tag_name"]
    if version_tuple(tag) <= version_tuple(current):
        return None
    matches = [a for a in release.get("assets", []) if a["name"] == RELEASE_ASSET and a.get("state") == "uploaded"]
    if len(matches) != 1:
        raise ValueError("The published release does not yet have a complete CREAM package.")
    asset = matches[0]
    digest = asset.get("digest", "")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest) or not 0 < asset["size"] <= MAX_DOWNLOAD:
        raise ValueError("The package has no valid SHA-256 or has an invalid size.")
    return {"version": tag.removeprefix("v"), "id": int(asset["id"]), "sha256": digest[7:],
            "size": asset["size"], "notes": str(release.get("body", ""))[:12000]}


def extract_verified(archive, destination):
    destination = Path(destination)
    with zipfile.ZipFile(archive) as package:
        infos = package.infolist()
        if len(infos) > 500 or sum(i.file_size for i in infos) > bootstrap.MAX_UNPACKED:
            raise ValueError("The update package exceeds the allowed size.")
        names = set()
        for item in infos:
            name = item.filename.rstrip("/") if item.is_dir() else item.filename
            bootstrap.safe_relative(name)
            if name.casefold() in names or stat.S_ISLNK(item.external_attr >> 16):
                raise ValueError("Duplicate entry or symbolic link in the ZIP.")
            names.add(name.casefold())
        for item in infos:
            path = destination / item.filename
            if item.is_dir():
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                with package.open(item) as source, path.open("wb") as target:
                    shutil.copyfileobj(source, target, 1024 * 1024)
    return bootstrap.read_manifest(destination)


def stage_release(release, target, cancel, data_dir=bootstrap.DATA, token=None):
    target = Path(target).resolve()
    if target.name != "cream" or not (target / "__init__.py").is_file():
        raise ValueError("Invalid plugin folder.")
    updates = Path(data_dir) / "updates"
    updates.mkdir(parents=True, exist_ok=True)
    stage = updates / uuid.uuid4().hex
    stage.mkdir()
    archive = updates / (stage.name + ".zip.partial")
    committed = False
    try:
        digest = hashlib.sha256()
        size = 0
        with _release_request(f"/repos/{REPOSITORY}/releases/assets/{release['id']}", token, binary=True, data_dir=data_dir) as response, archive.open("wb") as handle:
            while True:
                core.check_cancel(cancel)
                chunk = response.read(256 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_DOWNLOAD or size > release["size"]:
                    raise ValueError("The download exceeds the announced package size.")
                digest.update(chunk)
                handle.write(chunk)
        core.check_cancel(cancel)
        if size != release["size"] or digest.hexdigest() != release["sha256"]:
            raise ValueError("Incomplete download or incorrect SHA-256. No update was applied.")
        manifest = extract_verified(archive, stage)
        if manifest["version"] != release["version"]:
            raise ValueError("The package version differs from the announced release.")
        core.check_cancel(cancel)
        core.atomic_json(bootstrap.pending_path(target, data_dir), {
            "target": str(target), "stage": stage.name, "version": release["version"],
            "process_id": os.getpid(),
            "manifest_sha256": bootstrap.sha256(stage / "manifest.json")})
        committed = True
        return release["version"]
    finally:
        archive.unlink(missing_ok=True)
        if not committed:
            shutil.rmtree(stage, ignore_errors=True)
