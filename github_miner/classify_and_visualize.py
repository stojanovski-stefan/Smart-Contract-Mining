"""
classify_and_visualize.py - Step 5: Classify issues and commits, generate charts.

Reads merged JSONL files from data/merged/, classifies each record using
rule-based keyword matching, writes enriched JSONL to data/classified/,
and saves 8 PNG charts to data/figures/.

Usage:
    python classify_and_visualize.py
"""

import json
import logging
import os
from collections import Counter
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # must be before pyplot import — non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
MERGED_DIR = os.path.join(DATA_DIR, "merged")
CLASSIFIED_DIR = os.path.join(DATA_DIR, "classified")
FIGURES_DIR = os.path.join(DATA_DIR, "figures")

os.makedirs(CLASSIFIED_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)


def load_jsonl(filepath):
    pass


def write_jsonl(records, filepath):
    pass


def _classify_vuln_subtype(text):
    pass


def classify_issue(issue):
    pass


def _classify_fix_type(message):
    pass


def _classify_fix_scope(files_changed):
    pass


def classify_commit(commit):
    pass


def generate_charts(issues, commits):
    pass


def main():
    pass


if __name__ == "__main__":
    main()
