"""Download service with queue management."""
import subprocess
import logging
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal, QThread

logger = logging.getLogger(__name__)


class DownloadStatus(Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadTask:
    id: str
    name: str
    url: str
    output_path: Path
    status: DownloadStatus = DownloadStatus.QUEUED
    progress: float = 0.0
    speed: str = ""
    eta: str = ""
    error: str = ""
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class DownloadWorker(QThread):
    """Worker for downloading streams."""

    progress = pyqtSignal(str, float, str, str)
    completed = pyqtSignal(str)
    failed = pyqtSignal(str, str)

    def __init__(self, task: DownloadTask):
        super().__init__()
        self.task = task
        self.process: Optional[subprocess.Popen] = None
        self._cancelled = False

    def run(self):
        """Execute download."""
        try:
            cmd = [
                'ffmpeg',
                '-i', self.task.url,
                '-c', 'copy',
                '-t', '3600',
                '-y',
                str(self.task.output_path)
            ]

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            while True:
                if self._cancelled:
                    self.process.kill()
                    return

                line = self.process.stderr.readline()
                if not line:
                    break

                if 'time=' in line:
                    self.progress.emit(self.task.id, 50.0, "", "")

            self.process.wait()

            if self.process.returncode == 0:
                self.completed.emit(self.task.id)
            else:
                self.failed.emit(self.task.id, "Download failed")

        except Exception as e:
            self.failed.emit(self.task.id, str(e))

    def cancel(self):
        """Cancel download."""
        self._cancelled = True
        if self.process:
            self.process.kill()


class DownloadService(QObject):
    """Download queue manager."""

    download_added = pyqtSignal(DownloadTask)
    download_progress = pyqtSignal(str, float, str, str)
    download_completed = pyqtSignal(str)
    download_failed = pyqtSignal(str, str)

    def __init__(self, download_dir: Path):
        super().__init__()
        self.download_dir = download_dir
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.tasks: Dict[str, DownloadTask] = {}
        self.workers: Dict[str, DownloadWorker] = {}
        self.max_concurrent = 3
        self.active_count = 0

    def add_download(self, name: str, url: str) -> str:
        """Add download to queue."""
        task_id = f"{name}_{datetime.now().timestamp()}"

        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_'))
        output_path = self.download_dir / f"{safe_name}.mp4"

        task = DownloadTask(
            id=task_id,
            name=name,
            url=url,
            output_path=output_path
        )

        self.tasks[task_id] = task
        self.download_added.emit(task)

        self._process_queue()

        return task_id

    def cancel_download(self, task_id: str):
        """Cancel download."""
        if task_id in self.workers:
            self.workers[task_id].cancel()
            self.workers[task_id].wait()
            del self.workers[task_id]

        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = DownloadStatus.CANCELLED
            if task.output_path.exists():
                task.output_path.unlink()

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """Get task by ID."""
        return self.tasks.get(task_id)

    def get_all_tasks(self):
        """Get all tasks."""
        return list(self.tasks.values())

    def _process_queue(self):
        """Process queued downloads."""
        if self.active_count >= self.max_concurrent:
            return

        for task in self.tasks.values():
            if task.status == DownloadStatus.QUEUED:
                self._start_download(task)
                if self.active_count >= self.max_concurrent:
                    break

    def _start_download(self, task: DownloadTask):
        """Start download."""
        task.status = DownloadStatus.DOWNLOADING

        worker = DownloadWorker(task)
        worker.progress.connect(self._on_progress)
        worker.completed.connect(self._on_completed)
        worker.failed.connect(self._on_failed)
        worker.finished.connect(lambda: self._on_worker_finished(task.id))

        self.workers[task.id] = worker
        self.active_count += 1

        worker.start()

    def _on_progress(self, task_id: str, progress: float, speed: str, eta: str):
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.progress = progress
            task.speed = speed
            task.eta = eta
            self.download_progress.emit(task_id, progress, speed, eta)

    def _on_completed(self, task_id: str):
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = DownloadStatus.COMPLETED
            task.progress = 100.0
            self.download_completed.emit(task_id)

    def _on_failed(self, task_id: str, error: str):
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = DownloadStatus.FAILED
            task.error = error
            self.download_failed.emit(task_id, error)

    def _on_worker_finished(self, task_id: str):
        if task_id in self.workers:
            del self.workers[task_id]

        self.active_count -= 1
        self._process_queue()

    def cleanup(self):
        """Cleanup all downloads."""
        for worker in self.workers.values():
            worker.cancel()
            worker.wait()
        self.workers.clear()
