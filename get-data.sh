set -a
. .env
set +a
wget --no-check-certificate $DRIVE_DATA_URL -O 'data.tar.gz'
tar -xzvf data.tar.gz
rm data.tar.gz
