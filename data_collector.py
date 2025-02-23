from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, ipv6, tcp, udp, icmp, icmpv6, arp
import time
import sqlite3

class PacketCaptureApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(PacketCaptureApp, self).__init__(*args, **kwargs)
        
        # Connect to the database and create a cursor
        self.db_connection = sqlite3.connect('ids_data.db')
        self.cursor = self.db_connection.cursor()

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        in_port = msg.match['in_port']

        # Parse the packet
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        # Get Ethernet type and packet length
        eth_type = eth.ethertype
        pkt_len = len(msg.data)  # Total packet size

        # Handle IPv4 packets
        ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
        if ipv4_pkt:
            src_ip = ipv4_pkt.src
            dst_ip = ipv4_pkt.dst
            protocol = ipv4_pkt.proto
            ip_header_length = ipv4_pkt.header_length * 4  # IPv4 header length in bytes
            self.handle_ipv4_packet(pkt, src_ip, dst_ip, protocol, ip_header_length, pkt_len)
            return

        # Handle IPv6 packets
        ipv6_pkt = pkt.get_protocol(ipv6.ipv6)
        if ipv6_pkt:
            src_ip = ipv6_pkt.src
            dst_ip = ipv6_pkt.dst
            next_header = ipv6_pkt.nxt
            ip_header_length = 40  # Fixed IPv6 header length
            self.handle_ipv6_packet(pkt, src_ip, dst_ip, next_header, ip_header_length, pkt_len)
            return

        # Handle ARP packets
        arp_pkt = pkt.get_protocol(arp.arp)
        if arp_pkt:
            self.save_packet_info(arp_pkt.src_ip, arp_pkt.dst_ip, 'N/A', 'N/A', 'ARP', 28, pkt_len)
            return

        self.logger.info(f"Non-IPv4/IPv6/ARP packet received. Ethernet Type: {hex(eth_type)}")

    def handle_ipv4_packet(self, pkt, src_ip, dst_ip, protocol, ip_header_length, pkt_len):
        if protocol == 6:  # TCP
            tcp_pkt = pkt.get_protocol(tcp.tcp)
            if tcp_pkt:
                transport_header_length = tcp_pkt.offset * 4  # TCP header length
                src_port = tcp_pkt.src_port
                dst_port = tcp_pkt.dst_port
                self.save_packet_info(src_ip, dst_ip, src_port, dst_port, 'TCP', 
                                      ip_header_length + transport_header_length, pkt_len)

        elif protocol == 17:  # UDP
            udp_pkt = pkt.get_protocol(udp.udp)
            if udp_pkt:
                transport_header_length = 8  # UDP header length is fixed
                src_port = udp_pkt.src_port
                dst_port = udp_pkt.dst_port
                self.save_packet_info(src_ip, dst_ip, src_port, dst_port, 'UDP', 
                                      ip_header_length + transport_header_length, pkt_len)

        elif protocol == 1:  # ICMP
            icmp_pkt = pkt.get_protocol(icmp.icmp)
            if icmp_pkt:
                transport_header_length = len(icmp_pkt)
                self.save_packet_info(src_ip, dst_ip, 'N/A', 'N/A', 'ICMP', 
                                      ip_header_length + transport_header_length, pkt_len)

        else:
            self.logger.info(f"Unsupported IPv4 protocol number: {protocol}. Skipping.")

    def handle_ipv6_packet(self, pkt, src_ip, dst_ip, next_header, ip_header_length, pkt_len):
        if next_header == 6:  # TCP
            tcp_pkt = pkt.get_protocol(tcp.tcp)
            if tcp_pkt:
                transport_header_length = tcp_pkt.offset * 4  # TCP header length
                src_port = tcp_pkt.src_port
                dst_port = tcp_pkt.dst_port
                self.save_packet_info(src_ip, dst_ip, src_port, dst_port, 'TCPv6', 
                                      ip_header_length + transport_header_length, pkt_len)

        elif next_header == 17:  # UDP
            udp_pkt = pkt.get_protocol(udp.udp)
            if udp_pkt:
                transport_header_length = 8  # UDP header length is fixed
                src_port = udp_pkt.src_port
                dst_port = udp_pkt.dst_port
                self.save_packet_info(src_ip, dst_ip, src_port, dst_port, 'UDPv6', 
                                      ip_header_length + transport_header_length, pkt_len)

        elif next_header == 58:  # ICMPv6
            icmpv6_pkt = pkt.get_protocol(icmpv6.icmpv6)
            if icmpv6_pkt:
                transport_header_length = len(icmpv6_pkt)
                self.save_packet_info(src_ip, dst_ip, 'N/A', 'N/A', 'ICMPv6', 
                                      ip_header_length + transport_header_length, pkt_len)

        else:
            self.logger.info(f"Unsupported IPv6 next header: {next_header}. Skipping.")

    def save_packet_info(self, src_ip, dst_ip, src_port, dst_port, protocol, header_length, pkt_len):
        # Insert packet information into the database
        self.cursor.execute('''
            INSERT INTO collected_data (
                timestamp, source_ip, destination_ip, source_port, 
                destination_port, protocol, header_length, packet_length
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (time.time(), src_ip, dst_ip, src_port, dst_port, protocol, header_length, pkt_len))
        self.db_connection.commit()

    def __del__(self):
        # Close the database connection on app shutdown
        self.db_connection.close()

