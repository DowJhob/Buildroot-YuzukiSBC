echo "=============================== COPY to SERVER ========================"
pscp -p 32 -t 4 -v -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-without_exit_reader.txt /home/a/Desktop/wicket-gate-client-FSM/build-FSM-test-imx28-Debug/FSM-test /usr/r
echo "==================================== SYNC ============================="
pssh -p 32 -t 4 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-without_exit_reader.txt sync
echo "================================ COPY to RUN =========================="
pssh -p 32 -t 4 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-without_exit_reader.txt cp /usr/r /run/r
echo "================================= KILLALL R ==========================="
pssh -p 32 -t 4 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-without_exit_reader.txt killall r
echo "==================================== RUN =============================="
pssh -p 32 -t 4 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-without_exit_reader.txt /run/r &
