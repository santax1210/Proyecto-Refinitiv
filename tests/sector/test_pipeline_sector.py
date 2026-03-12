"""Runner simple para los tests sintéticos del pipeline de sector."""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from tests.sector.test_sector_pipeline import main as run_sector_tests


def main():
    print('\n' + '=' * 80)
    print(' SUITE DE TESTS — PIPELINE DE SECTOR '.center(80, '='))
    print(f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ".center(80))
    print('=' * 80)
    return run_sector_tests()


if __name__ == '__main__':
    sys.exit(0 if main() else 1)