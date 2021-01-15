cd /

cd /home/pi/wallflwr_lite/sentinel-scripts
bash cloud_proxy.sh



printf '\n\n\n\n\n RUNNING WITH NO INTERNET / LORA \n\n\n\n\n\n\n'
sudo gsutil -m cp -r gs://sentinel_test_data/ ../data/camera/DCIM
python3 main.py --wilderness