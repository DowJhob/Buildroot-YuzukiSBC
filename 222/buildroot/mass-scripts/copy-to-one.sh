echo "=============================== COPY to SERVER ========================"
pscp -t 5 -v -H root@10.1.7.154:22 /home/a/Documents/GitHub/wicket-client/build/arm-client/arm-client /usr
#pssh -t 5 -v -i -H root@10.1.7.154:22 rm /usr/r
pssh -t 5 -v -i -H root@10.1.7.154:22 mv -f /usr/arm-client /usr/r
echo "==================================== SYNC ============================="
pssh -t 5 -v -i -H root@10.1.7.154:22  sync
echo "================================ COPY to RUN =========================="
pssh -t 5 -v -i -H root@10.1.7.154:22 cp /usr/r /run/r
echo "================================= KILLALL R ==========================="
pssh -t 5 -v -i -H root@10.1.7.154:22 killall r
echo "==================================== RUN =============================="
pssh -t 5 -v -i -H root@10.1.7.154:22 /run/r &
