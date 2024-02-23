hosts="
root@10.1.7.161:22
root@10.1.7.162:22
"

for host in $hosts
do
echo "=============================== COPY to SERVER ========================"
pscp -t 5 -v -H $host /home/a/Documents/GitHub/wicket-client/build/arm-client/arm-client /usr
#pssh -t 5 -v -i -H $host rm /usr/r
pssh -t 5 -v -i -H $host mv -f /usr/arm-client /usr/r
echo "==================================== SYNC ============================="
pssh -t 5 -v -i -H $host  sync
echo "================================ COPY to RUN =========================="
pssh -t 5 -v -i -H $host cp /usr/r /run/r
echo "================================= KILLALL R ==========================="
pssh -t 5 -v -i -H $host killall r
echo "==================================== RUN =============================="
pssh -t 5 -v -i -H $host /run/r &
done
