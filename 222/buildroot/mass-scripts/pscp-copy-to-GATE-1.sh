#echo "============================== KILL ========================"
#pssh -p 32 -t 1 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-GATE-1.txt killall r

echo "============================== COPY ========================"
pscp -p 32 -t 2 -v -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-GATE-1.txt /home/a/Desktop/build-r-imx28-Release/r /usr/r

echo "============================== SYNC ========================"
pssh -p 32 -t 2 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-GATE-1.txt sync

echo "============================== KILL ========================"
pssh -p 32 -t 1 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-GATE-1.txt killall r

echo "============================== cp /usr/r /run/r ========================"
pssh -p 32 -t 1 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-GATE-1.txt cp /usr/r /run/r
echo "============================== SYNC ========================"
pssh -p 32 -t 2 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-GATE-1.txt sync
echo "============================== ./run/r ========================"
pssh -p 32 -t 1 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-GATE-1.txt /run/r


#echo "============================== REBOOT ========================"
#pssh -p 32 -t 1 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-GATE-1.txt reboot



