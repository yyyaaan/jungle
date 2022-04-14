
sudo apt install python3-certbot-nginx sqlite3
git clone https://github.com/yyyaaan/jungle.git

cd ./jungle
sudo -H pip install


sudo tee -a /etc/systemd/system/jungle.service > /dev/null <<EOT
[Unit]
Description=Gunicorn service to Django
After=network.target

[Service]
User=yan
Group=www-data
WorkingDirectory=/home/yan/jungle/jungle
ExecStart=gunicorn --workers 3 --bind unix:jungle.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
EOT

sudo tee -a /etc/nginx/sites-enabled/jungle > /dev/null <<EOT
server {
    listen 80;
    server_name app.yanpan.fi;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/yan/jungle/jungle/jungle.sock;
    }
}
EOT

sudo chmod 664 /etc/systemd/system/jungle.service
sudo systemctl daemon-reload
sudo systemctl enable jungle.service

sudo certbot --nginx -d domain