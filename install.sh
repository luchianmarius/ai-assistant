sudo apt update && sudo apt upgrade
sudo apt install python3 python3-pip python3-venv espeak-ng libespeak1 ffmpeg alsa-utils
source venv/bin/activate
pip install -r requirements.txt
deactivate
