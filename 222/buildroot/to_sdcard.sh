sudo umount /dev/sdb1
sudo umount /dev/sdb2
sudo umount /dev/sdb3
sudo dd if=~/Documents/GitHub/imx28_buildroot/output/images/sdcard.img of=/dev/sdb bs=8M count=32 status=progress
