echo "=============================== SSH ========================"

pssh -p 32 -t 7 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-GATE-2.txt echo ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC2qjn89ZE2YEgPGaJ75iymrXcJXFSk7vRF+WjApWTd8vuLRhPiN533hM99qYffSIArXTXMn85vr4lhawA0HF6Mwr1pj0tOIJzFpJXbUMaeAF8gBGRPRqDuWnrqKh6aQh7ji8nid5UZI439CXJ7THC/2LsE89U8o4tKEHf8C0U5lwCrhaiE5TO4isXs1tYrgysqihAK/MP7/17LbtTN12oH+blVHMMO/eygCYG3w8W4FltL/AuzHH2uKDkmVhHpSF4YtKFzTHS8t4RyzXR1KU0ony2KBYrS76DNjqJWXdsRH+X+Ia6uXRRJQdjE3zb3mRMc/0X8qc988+s+mRvrfuM3 a@ubuntu >> ~/.ssh/authorized_keys
pssh -p 32 -t 7 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-GATE-2.txt sync
pssh -p 32 -t 7 -v -i -h /home/a/Desktop/buildroot/mass-scripts/host-listS/host_list-GATE-2.txt reboot
