#!/bin/bash

set -x

function createPostgresConfig() {
    cp /etc/postgresql/12/main/postgresql.custom.conf.tmpl /etc/postgresql/12/main/conf.d/postgresql.custom.conf
    sudo -u postgres echo "autovacuum = $AUTOVACUUM" >>/etc/postgresql/12/main/conf.d/postgresql.custom.conf
    cat /etc/postgresql/12/main/conf.d/postgresql.custom.conf
}

function setPostgresPassword() {
    sudo -u postgres psql -c "ALTER USER renderer PASSWORD '${PGPASSWORD:-renderer}'"
}

# オリジナルのrun.shを編集してPostGIS環境だけ起動
# https://github.com/Overv/openstreetmap-tile-server/blob/master/run.sh

# Clean /tmp
rm -rf /tmp/*

# Fix postgres data privileges
chown postgres:postgres /var/lib/postgresql -R

# Initialize PostgreSQL
createPostgresConfig
service postgresql start
setPostgresPassword

# シェル起動、シェルを抜けたらコンテナも停止する
bash

service postgresql stop

exit 0
