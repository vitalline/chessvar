python -m nuitka main.py --standalone --include-data-dir=assets=assets --output-filename=chessvar.exe
copy cwda_2024.txt main.dist\cwda_2024.txt
copy config.txt dist\config.txt
copy readme.txt main.dist\readme.txt
copy source.txt main.dist\source.txt