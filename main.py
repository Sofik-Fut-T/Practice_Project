"""
BMP Editor — командний проєкт
Запуск: python main.py
Потребує Python 3.10+ (tkinter входить у стандартну бібліотеку)
"""
import sys
import os

# Додаємо корінь проєкту до шляху
sys.path.insert(0, os.path.dirname(__file__))

from ui.app import BMPApp

if __name__ == "__main__":
    app = BMPApp()
    app.run()
