#!/bin/sh

echo " ======================== ${BINARIES_DIR} ================================= "
echo " ======================== ${TARGET_DIR} ================================= "

mkfs.jffs2 -l -e0x10000 -s256 -d ${CONFIG_DIR}/board/DowJhob-devboard/home -o ${BINARIES_DIR}/home.jffs2

LINE='/dev/mtdblock4     /home           jffs2   defaults        0       2'
FILE=${TARGET_DIR}/etc/fstab
grep -qxF -- "$LINE" "$FILE" || echo "$LINE" >> "$FILE"
