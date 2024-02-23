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
pssh -t 9 -v -i -H $host sed -i '11s/^/#/' /etc/dhcpcd.conf
pssh -t 9 -v -i -H $host sed -i '12s/^/#/' /etc/dhcpcd.conf
done
