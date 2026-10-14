"""
Standalone llama-server.exe Manager & Local Inference Engine (PRINCIPLE-003, PRINCIPLE-007, PRINCIPLE-008)
Provides 1-click download, process lifecycle management, and high-performance local inference
via the official precompiled llama.cpp server binary (zero Python C++ dependencies).
"""

import os
import sys
import time
import json
import atexit
import shutil
import zipfile
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Tuple, Callable, Dict, Any, Union

# Official pinned stable release for Windows x64 (AVX2-optimized, compatible with all modern 64-bit CPUs)
OFFICIAL_RELEASE_TAG = "b11624"
OFFICIAL_RELEASE_URL = (
    f"https://github.com/ggml-org/llama.cpp/releases/download/{OFFICIAL_RELEASE_TAG}/"
    f"llama-{OFFICIAL_RELEASE_TAG}-bin-win-cpu-x64.zip"
)
LATEST_API_URL = "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest"


def get_bin_dir() -> Path:
    """Return the directory path where standalone binaries are stored."""
    base_dir = Path(__file__).resolve().parent.parent
    bin_dir = base_dir / "models" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    return bin_dir


def get_server_exe_path() -> Path:
    """Return the absolute path to llama-server.exe."""
    exe_name = "llama-server.exe" if sys.platform == "win32" else "llama-server"
    return get_bin_dir() / exe_name


def is_server_installed() -> bool:
    """Return True if the standalone server executable is present and valid."""
    exe_path = get_server_exe_path()
    if exe_path.exists() and exe_path.stat().st_size > 4000:
        return True
    
    # Check if available in system PATH
    system_exe = shutil.which("llama-server") or shutil.which("llama-server.exe")
    return bool(system_exe)


def download_server(
    progress_callback: Optional[Callable[[str, int, int, float], None]] = None,
    cancel_event=None,
) -> Path:
    """
    Download and extract the official standalone llama-server release.
    
    Args:
        progress_callback: Optional function(status_text, bytes_read, total_bytes, pct)
        cancel_event: Optional threading.Event to signal cancellation

    Returns:
        Path to the installed llama-server.exe
    """
    bin_dir = get_bin_dir()
    target_exe = get_server_exe_path()
    part_path = bin_dir / f".llama_win_{OFFICIAL_RELEASE_TAG}.zip.part"

    download_url = OFFICIAL_RELEASE_URL

    # Attempt to resolve latest release URL dynamically if available
    try:
        req = urllib.request.Request(
            LATEST_API_URL,
            headers={"User-Agent": "NoMoreClutter-LlamaServer/1.0"}
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                for asset in data.get("assets", []):
                    name = asset.get("name", "").lower()
                    if "win" in name and "cpu-x64" in name and name.endswith(".zip"):
                        download_url = asset.get("browser_download_url", download_url)
                        break
    except Exception:
        # Fall back to pinned stable URL
        download_url = OFFICIAL_RELEASE_URL

    # Stream download with progress tracking
    req = urllib.request.Request(
        download_url,
        headers={"User-Agent": "NoMoreClutter-LlamaServer/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30.0) as resp:
        total_size = int(resp.headers.get("Content-Length", 0)) or 18 * 1024 * 1024
        downloaded = 0
        chunk_size = 128 * 1024

        with open(part_path, "wb") as f:
            while True:
                if cancel_event and cancel_event.is_set():
                    if part_path.exists():
                        part_path.unlink()
                    raise InterruptedError("Download was cancelled by user.")

                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)

                if progress_callback:
                    pct = min(100.0, (downloaded / total_size) * 100) if total_size else 0.0
                    mb_read = downloaded / (1024 * 1024)
                    mb_total = total_size / (1024 * 1024)
                    progress_callback(
                        f"Downloading official llama-server ({mb_read:.1f}/{mb_total:.1f} MB)...",
                        downloaded,
                        total_size,
                        pct,
                    )

    # Extract all binary files and DLLs into bin_dir
    if progress_callback:
        progress_callback("Extracting official binaries...", total_size, total_size, 99.0)

    try:
        with zipfile.ZipFile(part_path, "r") as z:
            for file_info in z.infolist():
                filename = os.path.basename(file_info.filename)
                # Extract only executable binaries and supporting DLLs
                if filename and (filename.endswith(".exe") or filename.endswith(".dll")):
                    source = z.open(file_info)
                    dest_file = bin_dir / filename
                    with open(dest_file, "wb") as target:
                        shutil.copyfileobj(source, target)
    finally:
        if part_path.exists():
            try:
                part_path.unlink()
            except OSError:
                pass

    if progress_callback:
        progress_callback("Standalone local engine ready!", total_size, total_size, 100.0)

    return target_exe


class LlamaServerManager:
    """Manages the background execution, lifecycle, and inference requests for llama-server.exe."""

    _process: Optional[subprocess.Popen] = None
    _current_model_path: Optional[str] = None
    _current_mmproj_path: Optional[str] = None
    _current_port: int = 8080

    @classmethod
    def get_effective_exe_path(cls) -> Optional[Path]:
        """Resolve path to executable (local models/bin or system PATH)."""
        local_exe = get_server_exe_path()
        if local_exe.exists() and local_exe.stat().st_size > 4000:
            return local_exe
        sys_exe = shutil.which("llama-server") or shutil.which("llama-server.exe")
        if sys_exe:
            return Path(sys_exe)
        return None

    @classmethod
    def is_server_running(cls, port: int = 8080) -> bool:
        """Check if llama-server is currently active and healthy on the given port."""
        url = f"http://127.0.0.1:{port}/health"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "NoMoreClutter-LlamaServer/1.0"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                return resp.status == 200
        except Exception:
            return False

    @classmethod
    def start_server(
        cls,
        model_path: Union[str, Path],
        mmproj_path: Optional[Union[str, Path]] = None,
        port: int = 8080,
        threads: Optional[int] = None,
        timeout: float = 30.0,
    ) -> Tuple[bool, str]:
        """
        Start the standalone llama-server subprocess hosting the specified model.
        
        Args:
            model_path: Path to GGUF model weights
            mmproj_path: Optional path to multimodal vision projector
            port: Port to bind HTTP server to (default 8080)
            threads: Number of CPU threads (defaults to min(4, cpu_count))
            timeout: Maximum seconds to wait for model to load into memory
            
        Returns:
            Tuple[bool, str]: (success, status_or_error_message)
        """
        model_str = str(Path(model_path).resolve())
        mmproj_str = str(Path(mmproj_path).resolve()) if mmproj_path and Path(mmproj_path).exists() else None

        # 1. If already running with identical model and vision projector, reuse
        if (
            cls._process is not None
            and cls._process.poll() is None
            and cls._current_model_path == model_str
            and cls._current_mmproj_path == mmproj_str
            and cls._current_port == port
        ):
            if cls.is_server_running(port):
                return True, f"llama-server already running on port {port}"

        # 2. Stop any existing server instance before launching new model
        cls.stop_server()

        exe_path = cls.get_effective_exe_path()
        if not exe_path or not exe_path.exists():
            return False, "llama-server.exe is not installed. Download via '1-Click Quick Deploy'."

        if not Path(model_str).exists():
            return False, f"Model weights not found at: {model_str}"

        # 3. Assemble command line
        n_threads = threads or min(4, os.cpu_count() or 2)
        cmd = [
            str(exe_path),
            "-m", model_str,
            "--host", "127.0.0.1",
            "--port", str(port),
            "-c", "2048",
            "-t", str(n_threads),
            "--log-disable",
        ]
        if mmproj_str:
            cmd.extend(["--mmproj", mmproj_str])

        # 4. Launch subprocess with no visible console window on Windows
        creationflags = 0
        if sys.platform == "win32":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

        try:
            cls._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                creationflags=creationflags,
                text=True,
            )
            cls._current_model_path = model_str
            cls._current_mmproj_path = mmproj_str
            cls._current_port = port
        except Exception as e:
            return False, f"Failed to spawn llama-server: {str(e)}"

        # 5. Poll /health endpoint until HTTP 200 (model weights fully loaded)
        start_time = time.time()
        url = f"http://127.0.0.1:{port}/health"

        while time.time() - start_time < timeout:
            if cls._process.poll() is not None:
                _, stderr = cls._process.communicate()
                cls._process = None
                return False, f"llama-server exited abruptly: {stderr[:300] if stderr else 'unknown error'}"

            try:
                req = urllib.request.Request(url, headers={"User-Agent": "NoMoreClutter-LlamaServer/1.0"})
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    if resp.status == 200:
                        return True, f"llama-server ready on port {port}"
            except urllib.error.HTTPError as e:
                # HTTP 503 means server is running and actively loading weights into RAM
                if e.code == 503:
                    pass
            except Exception:
                pass

            time.sleep(0.4)

        # Timeout reached
        cls.stop_server()
        return False, f"Timed out after {timeout:.0f}s waiting for llama-server to load model."

    @classmethod
    def stop_server(cls) -> None:
        """Terminate the running llama-server subprocess gracefully."""
        if cls._process is not None:
            try:
                if cls._process.poll() is None:
                    cls._process.terminate()
                    try:
                        cls._process.wait(timeout=2.0)
                    except subprocess.TimeoutExpired:
                        cls._process.kill()
            except Exception:
                pass
            finally:
                cls._process = None
                cls._current_model_path = None
                cls._current_mmproj_path = None

    @classmethod
    def complete(
        cls,
        prompt: str,
        model_path: Union[str, Path],
        temperature: float = 0.2,
        max_tokens: int = 1500,
        port: int = 8080,
    ) -> str:
        """
        Execute text completion using the standalone llama-server.
        """
        ok, msg = cls.start_server(model_path=model_path, port=port)
        if not ok:
            raise RuntimeError(f"Could not initialize local inference server: {msg}")

        url = f"http://127.0.0.1:{port}/v1/chat/completions"
        payload = {
            "messages": [
                {"role": "system", "content": "You are a fast, structured JSON-only file organizer."},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json", "User-Agent": "NoMoreClutter-LlamaServer/1.0"},
        )
        with urllib.request.urlopen(req, timeout=60.0) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            return res_json["choices"][0]["message"]["content"] or ""

    @classmethod
    def analyze_image(
        cls,
        image_path: Union[str, Path],
        prompt: str,
        model_path: Union[str, Path],
        mmproj_path: Union[str, Path],
        max_tokens: int = 100,
        port: int = 8080,
    ) -> str:
        """
        Analyze an image using the standalone llama-server with multimodal vision projector.
        """
        import base64
        ok, msg = cls.start_server(model_path=model_path, mmproj_path=mmproj_path, port=port)
        if not ok:
            raise RuntimeError(f"Could not initialize vision server: {msg}")

        with open(str(image_path), "rb") as f:
            b64_img = base64.b64encode(f.read()).decode("utf-8")

        # Native /completion endpoint with image_data is fast and robust across all vision models
        url = f"http://127.0.0.1:{port}/completion"
        formatted_prompt = f"Question: {prompt}\n\nAnswer:"
        payload = {
            "prompt": formatted_prompt,
            "image_data": [{"data": b64_img, "id": 1}],
            "n_predict": max_tokens,
            "temperature": 0.1,
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json", "User-Agent": "NoMoreClutter-LlamaServer/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60.0) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                return (res_json.get("content") or "").strip()
        except Exception:
            # Fallback to OpenAI multimodal chat completions format
            chat_url = f"http://127.0.0.1:{port}/v1/chat/completions"
            data_uri = f"data:image/jpeg;base64,{b64_img}"
            chat_payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": data_uri}},
                        ],
                    }
                ],
                "max_tokens": max_tokens,
            }
            chat_req = urllib.request.Request(
                chat_url,
                data=json.dumps(chat_payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "NoMoreClutter-LlamaServer/1.0"},
            )
            with urllib.request.urlopen(chat_req, timeout=60.0) as chat_resp:
                res_json = json.loads(chat_resp.read().decode("utf-8"))
                return (res_json["choices"][0]["message"]["content"] or "").strip()


# Cleanly terminate any running server when application exits (PRINCIPLE-012)
atexit.register(LlamaServerManager.stop_server)
