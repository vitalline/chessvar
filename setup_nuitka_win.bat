python -m nuitka main.py --standalone --include-data-dir=assets=assets --output-filename=chessvarw.exe --windows-console-mode=disable --windows-force-stderr-spec=chessvar.stderr.txt --windows-force-stdout-spec=chessvar.stdout.txt
copy cwda_2024.txt main.dist\cwda_2024.txt
copy readme.txt main.dist\readme.txt