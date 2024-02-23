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
pssh -t 9 -v -i -H $host sed -i '11s/^/#/' /etc/dhcpcd.conf
pssh -t 9 -v -i -H $host sed -i '12s/^/#/' /etc/dhcpcd.conf
done
