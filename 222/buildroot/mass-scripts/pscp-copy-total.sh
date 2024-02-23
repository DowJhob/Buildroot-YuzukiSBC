echo "============================== COPY ========================"
#pssh -p 32 -t 1 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list.txt killall r
pscp -p 32 -t 7 -v -h    /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list.txt /home/a/Desktop/wicket-gate-client-FSM/build-FSM-test-imx28-Debug/FSM-test /usr/r
echo "============================== SYNC ========================"
pssh -p 32 -t 7 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list.txt sync
echo "============================== REBOOT ========================"
pssh -p 32 -t 1 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list.txt reboot
