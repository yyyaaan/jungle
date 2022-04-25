# gunicorn jungle.wsgi:application -b 0.0.0.0:8999

sudo apt install python3-certbot-nginx sqlite3
git clone https://github.com/yyyaaan/jungle.git
cd ~/jungle
sudo -H pip install -r requirements.txt

cd ~/jungle/jungle
python manage.py collectstatic --noinput



domain="xxx.xxx.com"


# upload models, clouds, etc.
unzip opencv_model.zip -d ~/jungle/jungle/vision
sudo mkdir /etc/openstack && sudo mv clouds.yaml /etc/openstack/clouds.yaml

# add service
sudo rm -f /etc/systemd/system/jungle.service 
sudo tee -a /etc/systemd/system/jungle.service > /dev/null <<EOT
[Unit]
Description=Gunicorn service to Django
After=network.target

[Service]
User=yan
Group=www-data
Environment="djangosecret='xxxxxxx'"
Environment="djangodebug='no'"
WorkingDirectory=/home/yan/jungle/jungle
ExecStart=gunicorn --workers 3 --bind unix:/home/yan/jungle/jungle/jungle.sock jungle.wsgi:application

[Install]
WantedBy=multi-user.target
EOT


sudo chmod 664 /etc/systemd/system/jungle.service
sudo systemctl daemon-reload
sudo systemctl enable jungle.service
sudo systemctl restart jungle.service


sudo rm -f /etc/nginx/sites-enabled/jungle
sudo tee -a /etc/nginx/sites-enabled/jungle > /dev/null <<EOT
server {
    listen 80;
    server_name $domain;
    client_max_body_size 100M;

    location /static/ {
        alias /home/yan/jungle/jungle/staticfiles/;
    }
    location / {
        include proxy_params;
        proxy_pass http://unix:/home/yan/jungle/jungle/jungle.sock;
    }
}
EOT

sudo certbot --nginx -d $domain
sudo chown -R :www-data /home/yan/jungle/jungle/staticfiles/


# for git update, run collect static first