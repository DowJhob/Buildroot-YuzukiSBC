IP='root@10.1.7.109'
while true 
do
echo "=============================== COPY to SERVER ========================"
pscp -t 1 -v -H $IP /home/a/Desktop/wicket-gate-client-FSM/build-FSM-test-imx28-Debug/FSM-test /usr/r
echo "==================================== SYNC ============================="
pssh -t 1 -v -i -H $IP sync
#echo "================================ COPY to RUN =========================="
#pssh -p 32 -t 4 -v -i -H $IP cp /usr/r /run/r
#echo "================================= KILLALL R ==========================="
#pssh -p 32 -t 4 -v -i -H $IP killall r
#echo "==================================== RUN =============================="
#pssh -p 32 -t 4 -v -i -H $IP /run/r &
done
