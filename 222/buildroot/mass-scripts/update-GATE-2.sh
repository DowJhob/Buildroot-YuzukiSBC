hosts="
root@10.1.7.121:22
root@10.1.7.122:22
root@10.1.7.123:22
root@10.1.7.124:22
root@10.1.7.125:22
root@10.1.7.126:22
root@10.1.7.127:22
root@10.1.7.128:22
root@10.1.7.129:22
root@10.1.7.130:22
root@10.1.7.131:22
root@10.1.7.132:22
root@10.1.7.133:22
root@10.1.7.134:22
"

for host in $hosts
do
echo "=============================== COPY to SERVER ========================"
pscp -t 5 -v -H $host /home/a/Documents/GitHub/wicket-client/build/r /usr
#pssh -t 5 -v -i -H $host rm /usr/r
#pssh -t 5 -v -i -H $host mv -f /usr/arm-client /usr/r
echo "==================================== SYNC ============================="
pssh -t 5 -v -i -H $host  sync
echo "================================ COPY to RUN =========================="
pssh -t 5 -v -i -H $host cp /usr/r /run/r
echo "================================= KILLALL R ==========================="
pssh -t 5 -v -i -H $host killall r
echo "==================================== RUN =============================="
pssh -t 5 -v -i -H $host /run/r &
done
