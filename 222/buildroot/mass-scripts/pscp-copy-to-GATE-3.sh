echo "=============================== COPY to SERVER ========================"
pscp -p 32 -t 2 -v -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-GATE-3.txt /home/a/Desktop/build-r-imx28-Release/r /usr/r
echo "==================================== SYNC ============================="
pssh -p 32 -t 2 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-GATE-3.txt sync
echo "================================ COPY to RUN =========================="
pssh -p 32 -t 2 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-GATE-3.txt cp /usr/r /run/r
echo "================================= KILLALL R ==========================="
pssh -p 32 -t 2 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-GATE-3.txt killall r
echo "==================================== RUN =============================="
pssh -p 32 -t 2 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-GATE-3.txt /run/r &
