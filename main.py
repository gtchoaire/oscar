"""Entrada principal do visualizador MASBAL.

Uso: python3 main.py [arquivo.masbal.log] [--save imagem.png --no-show]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox

from masbal.config import DEFAULT_FILE
from masbal.individual import MassBalanceWindow
from masbal.launcher import StartWindow
from masbal.theme import APP_STYLE
from masbal.typography import FONT_FAMILY, configure_matplotlib_typography


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualiza tabelas de balanço de massa MASBAL.")
    parser.add_argument("arquivo", nargs="?", type=Path, help="arquivo .txt ou .log")
    parser.add_argument("--save", type=Path, metavar="IMAGEM", help="salva os gráficos ao iniciar")
    parser.add_argument("--no-show", action="store_true", help="não abre a janela")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    application = QApplication.instance() or QApplication(sys.argv)
    application.setFont(QFont(FONT_FAMILY))
    configure_matplotlib_typography()
    application.setStyle("Fusion")
    application.setStyleSheet(APP_STYLE)

    if args.arquivo is None and not args.save and not args.no_show:
        launcher = StartWindow()
        launcher.show()
        raise SystemExit(application.exec())

    path = args.arquivo or DEFAULT_FILE
    try:
        window = MassBalanceWindow(path.expanduser().resolve())
    except (FileNotFoundError, ValueError) as error:
        if args.no_show:
            raise SystemExit(str(error)) from error
        QMessageBox.critical(None, "Não foi possível abrir o arquivo", str(error))
        raise SystemExit(1) from error

    if args.save:
        target = args.save.expanduser().resolve()
        window.save_figure(target)
        print(f"Imagem salva em: {target}")
    if args.no_show:
        window.close()
        return

    window.show()
    raise SystemExit(application.exec())


if __name__ == "__main__":
    main()
