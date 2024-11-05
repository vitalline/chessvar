pyinstaller main.py --onefile --add-data "assets;assets" --name chessvarc
pyinstaller main.py --onefile --windowed --add-data "assets;assets" --name chessvarw
copy cwda_2024.txt dist\cwda_2024.txt
copy readme.txt dist\readme.txt