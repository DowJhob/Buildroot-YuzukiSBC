FD_DIR=/home/a/Documents/qt/face-detector---landmarker
CUSTOM_HOME_DIR=~/Documents/GitHub
CUSTOM_HOME_START_ADDR=0x1E60000
SUNXI_FEL_TOOLS_DIR=/home/a/Documents/GitHub/sunxi-tools

mkdir ${FD_DIR}/build2
cp ${FD_DIR}/build/fd ${FD_DIR}/build2

mkfs.jffs2 -l -e0x10000 -s256 -d ${FD_DIR}/build2 -o ${CUSTOM_HOME_DIR}/home.jffs2

sudo sunxi-fel -p spiflash-write ${CUSTOM_HOME_START_ADDR} ${CUSTOM_HOME_DIR}/home.jffs2
