echo "=============================== COPY to SERVER ========================"
pscp -p 32 -t 5 -v -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-GATE-2.txt /home/a/Desktop/buildroot/mass-scripts/fstab /etc
echo "==================================== SYNC ============================="
pssh -p 32 -t 5 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-GATE-2.txt sync

