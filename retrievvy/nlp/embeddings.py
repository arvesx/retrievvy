"""
embeddings.py

This module handles generating text embeddings using a heavy model (SentenceTransformer)
in a separate process. We do this to avoid blocking the main event loop, which is crucial
when running an asynchronous web server.

Key Points:
- The heavy embedding model is loaded once in a worker process.
- Communication between the main process and the worker is handled via multiprocessing queues.
- The asynchronous helper function (get_async) uses asyncio’s run_in_executor to offload the
  blocking queue.get() call, ensuring non-blocking behavior in the main event loop.
- This setup allows multiple modules to use the same worker without spawning multiple processes.
- A start function is provided to initialize the worker and a shutdown function to cleanly
  terminate the worker process when the application stops.

By isolating the resource-intensive model in a separate process, we maintain responsiveness
and ensure that our web server can handle other I/O tasks concurrently.
"""

import asyncio
import multiprocessing as mp

from typing import Optional

import torch
from sentence_transformers import SentenceTransformer

from tenacity import retry, stop_after_attempt, wait_fixed
from loguru import logger


# Global variables for inter-process communication and process handle
_embedding_input_queue: Optional[mp.Queue] = None
_embedding_output_queue: Optional[mp.Queue] = None
_embedding_process: Optional[mp.Process] = None


# Worker (Separate Process)
# -------------------------
def worker(inq: mp.Queue, outq: mp.Queue):
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")  # Load the model once
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    while True:
        # Wait for input
        sentences = inq.get()
        if sentences is None:
            break  # Termination signal

        embedding = model.encode(
            sentences, convert_to_tensor=True, normalize_embeddings=True, device=device
        )

        embedding_list = embedding.cpu().numpy().tolist()
        outq.put(embedding_list)


# Get embedding functions
# -----------------------


@retry(wait=wait_fixed(1), stop=stop_after_attempt(3), reraise=True)
async def get_async(sentences: list[str]) -> list[list[float]]:
    """
    Asynchronously get the embedding using asyncio and run_in_executor.
    """
    if _embedding_input_queue is None or _embedding_output_queue is None:
        raise RuntimeError("Worker not started. Call start_worker() first.")
    loop = asyncio.get_running_loop()
    _embedding_input_queue.put(sentences)
    embedding = await loop.run_in_executor(None, _embedding_output_queue.get)
    return embedding


# Start Worker Function
# ----------------------
def start_worker():
    """
    Initializes the embedding worker by creating the inter-process communication queues
    and starting the worker process. Call this function in your server's main block.
    """
    global _embedding_input_queue, _embedding_output_queue, _embedding_process
    _embedding_input_queue = mp.Queue()
    _embedding_output_queue = mp.Queue()
    logger.info("Spawning a new process for embeddings")
    _embedding_process = mp.Process(
        target=worker, args=(_embedding_input_queue, _embedding_output_queue)
    )
    _embedding_process.daemon = True
    _embedding_process.start()


# Shutdown
# --------
def shutdown_worker():
    """
    Sends a termination signal and joins the worker process.
    """
    if _embedding_input_queue is None or _embedding_process is None:
        raise RuntimeError("Worker not started or already shut down.")
    _embedding_input_queue.put(None)
    _embedding_process.join()
