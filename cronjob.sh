echo "59 21 * * * docker rm -f content" >> /etc/crontab
echo "* 22 * * * docker run -d --name content mlacaud/contentsupplying" >> /etc/crontab
