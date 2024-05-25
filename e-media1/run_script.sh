#!bin/bash


if ! command -v poetry $> /dev/null
then
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi
chmod +x run_script.sh
#
# -r [optional] -> Removes ALL Ancillary Chunks from PNG Image
# By default we save 3 Ancilary Chunks (if exists):
#   *EXIF
#   *GAMA
#   *CHRM
#
poetry run python e_media1/main.py images/car.png -r
