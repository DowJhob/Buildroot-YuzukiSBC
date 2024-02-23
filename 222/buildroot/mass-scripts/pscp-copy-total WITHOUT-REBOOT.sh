echo "=============================== COPY to SERVER ========================"
pscp -p 32 -t 5 -v -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list2.txt /home/a/Desktop/wicket-gate-client-FSM/build-FSM-test-imx28-Debug/FSM-test /usr/r
echo "==================================== SYNC ============================="
pssh -p 32 -t 5 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list2.txt sync
echo "================================ COPY to RUN =========================="
pssh -p 32 -t 5 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list2.txt cp /usr/r /run/r
echo "================================= KILLALL R ==========================="
pssh -p 32 -t 5 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list2.txt killall r
echo "==================================== RUN =============================="
pssh -p 32 -t 5 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list2.txt /run/r &
