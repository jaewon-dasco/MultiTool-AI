/usr/sbin/iptables -P INPUT DROP
/usr/sbin/iptables -P FORWARD DROP
/usr/sbin/iptables -P OUTPUT ACCEPT
/usr/sbin/iptables -A INPUT -s localhost -j ACCEPT
/usr/sbin/iptables -A FORWARD -s localhost -j ACCEPT
/usr/sbin/iptables -A INPUT -i lo -j ACCEPT
/usr/sbin/iptables -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT

/usr/sbin/iptables -A INPUT -i eth0 -p tcp --dport 11740 -j ACCEPT # CODESYS login
/usr/sbin/iptables -A INPUT -i eth0 -p udp --dport 1740 -j ACCEPT # CODESYS login
/usr/sbin/iptables -A INPUT -i eth0 -p tcp --dport 20 -j ACCEPT # FTP
/usr/sbin/iptables -A INPUT -i eth0 -p tcp --dport 21 -j ACCEPT # FTP
/usr/sbin/iptables -A INPUT -i eth0 -p tcp --dport 8080 -j ACCEPT # Webvisu
/usr/sbin/iptables -A INPUT -i eth0 -p tcp --dport 22 -j ACCEPT # SSH/SFTP
/usr/sbin/iptables -A INPUT -i eth0 -p tcp --dport 1200 -j ACCEPT # CODESYS gateway 2.3
/usr/sbin/iptables -A INPUT -i eth0 -p tcp --dport 1217 -j ACCEPT # CODESYS gateway 3.5
/usr/sbin/iptables -A INPUT -i eth0 -p tcp --dport 5900 -j ACCEPT # VNC
/usr/sbin/iptables -A INPUT -i uap0 -p udp --dport 67 -j ACCEPT # DHCP

