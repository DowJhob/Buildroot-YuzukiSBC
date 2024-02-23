OUT_DIR='/home/a/Documents/GitHub/Buildroot-YuzukiSBC/buildroot/output/images'

rm r $OUT_DIR/total.jffs2

dd if=$OUT_DIR/u-boot-sunxi-with-spl.bin bs=1 status=progress >> $OUT_DIR/total.jffs2
fallocate -l $((0x50000)) /home/a/Documents/GitHub/Buildroot-YuzukiSBC/buildroot/output/images/total.jffs2

dd if=$OUT_DIR/sun8i-v3s-licheepi-zero-linux.dtb bs=1 seek=$((0x50000)) status=progress >> $OUT_DIR/total.jffs2
fallocate -l $((0x60000)) /home/a/Documents/GitHub/Buildroot-YuzukiSBC/buildroot/output/images/total.jffs2

dd if=$OUT_DIR/zImage bs=1                            seek=$((0x60000)) status=progress >> $OUT_DIR/total.jffs2
fallocate -l $((0x360000)) /home/a/Documents/GitHub/Buildroot-YuzukiSBC/buildroot/output/images/total.jffs2

dd if=$OUT_DIR/rootfs.jffs2 bs=1                      seek=$((0x360000)) status=progress >> $OUT_DIR/total.jffs2
fallocate -l $((0x1D60000)) /home/a/Documents/GitHub/Buildroot-YuzukiSBC/buildroot/output/images/total.jffs2

dd if=$OUT_DIR/home.jffs2 bs=1                        seek=$((0x1D60000)) status=progress >> $OUT_DIR/total.jffs2
#fallocate -l $((0x10000000)) /home/a/Documents/GitHub/Buildroot-YuzukiSBC/buildroot/output/images/total.jffs2
