hosts="
root@10.1.7.141:22
root@10.1.7.142:22
root@10.1.7.143:22
root@10.1.7.144:22
root@10.1.7.145:22
root@10.1.7.146:22
root@10.1.7.147:22
root@10.1.7.148:22
root@10.1.7.149:22
root@10.1.7.150:22
root@10.1.7.151:22
root@10.1.7.152:22
root@10.1.7.153:22
root@10.1.7.154:22
"

for host in $hosts
do
echo "=============================== COPY to SERVER ========================"
pscp -t 6 -v -H $host /home/a/Documents/GitHub/wicket-client/build/r /usr
#pssh -t 5 -v -i -H $host rm /usr/r
#pssh -t 5 -v -i -H $host mv -f /usr/arm-client /usr/r
echo "==================================== SYNC ============================="
pssh -t 6 -v -i -H $host  sync
echo "================================ COPY to RUN =========================="
pssh -t 6 -v -i -H $host cp /usr/r /run/r
echo "================================= KILLALL R ==========================="
pssh -t 6 -v -i -H $host killall r
echo "==================================== RUN =============================="
pssh -t 6 -v -i -H $host /run/r &
done
