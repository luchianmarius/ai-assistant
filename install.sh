sudo apt update && sudo apt upgrade
sudo apt install espeak-ng libespeak1 ffmpeg alsa-utils
source venv/bin/activate
pip install -r requirements.txt
deactivate
