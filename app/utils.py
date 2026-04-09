from __future__ import annotations

import logging
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from config.settings import CHUNK_OVERLAP, CHUNK_SIZE

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def split_text(text: str) -> List[str]:
    if not text or not str(text).strip():
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return splitter.split_text(str(text))
