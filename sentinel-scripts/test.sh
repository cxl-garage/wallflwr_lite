cd /

cd /home/pi/wallflwr_lite/sentinel-scripts
bash cloud_proxy.sh


printf '\n\n\n\n\n BASIC BASH SCRIPT TEST (not implemented) \n\n\n\n\n\n\n'
#bash run.sh

printf '\n\n\n\n\n BASIC TEST w/ ALL RELEVANT DATA FORMATS \n\n\n\n\n\n\n'
sudo gsutil -m cp -r gs://sentinel_test_data/ ../data/camera/DCIM
python3 main.py

printf '\n\n\n\n\n INSTALLING A MISSING PIP PACKAGE \n\n\n\n\n\n\n'
pip3 uninstall -y wireless
sudo gsutil -m cp -r gs://sentinel_test_data/ ../data/camera/DCIM
python3 main.py

printf '\n\n\n\n\n PULL GIT \n\n\n\n\n\n\n'
sudo gsutil -m cp -r gs://sentinel_test_data/ ../data/camera/DCIM
python3 main.py --git

printf '\n\n\n\n\n ALL DATA/MODELS DONT EXIST \n\n\n\n\n\n\n'

rm -r ../data/results/
rm -r ../data/camera/DCIM/
mkdir ../data/camera/DCIM/
rm ../data/device_insights.csv
rm -r ../models
sudo gsutil -m cp -r gs://sentinel_test_data/ ../data/camera/DCIM
python3 main.py

printf '\n\n\n\n\n ALL DEVICE INFO IS WIPED \n\n\n\n\n\n\n'
rm ../_device_info.csv
sudo gsutil -m cp -r gs://sentinel_test_data/ ../data/camera/DCIM
python3 main.py


printf '\n\n\n\n\n RUNNING WITH NO INTERNET / LORA \n\n\n\n\n\n\n'
sudo gsutil -m cp -r gs://sentinel_test_data/ ../data/camera/DCIM
python3 main.py --wilderness

printf '\n\n\n\n\n RUNNING AGAIN TO CHECK INTEGRATION OF ENRICHED DATA FROM LORA \n\n\n\n\n\n\n'
python3 main.py
