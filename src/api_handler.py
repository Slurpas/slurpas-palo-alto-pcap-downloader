# This file will handle the communication with the Palo Alto Networks firewall API.
from panos.firewall import Firewall
import requests

class PaloAltoAPI:
    def __init__(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.fw = None

    def connect(self):
        """
        Connects to the firewall and returns True on success, False on failure.
        """
        try:
            self.fw = Firewall(self.hostname, self.username, self.password)
            # The Firewall object handles API key generation automatically.
            # A simple command like fetching the hostname will test the connection.
            self.fw.refresh_system_info()
            print("API KEY:", self.fw.api_key)
            return True, f"Successfully connected to {self.hostname}."
        except Exception as e:
            self.fw = None
            return False, f"Failed to connect to {self.hostname}: {e}"

    def start_packet_capture(self, stage_name, filters):
        """
        Starts a filter-based packet capture using the canonical operational commands.
        Filters is a dict with keys: src_ip, dest_ip, src_port, dest_port, protocol, max_packets
        """
        if not self.fw:
            return False, "Not connected to firewall."
        try:
            api_key = self.fw.api_key
            url = f"https://{self.hostname}/api/"
            # Build the filter string
            filter_parts = []
            if filters.get("src_ip"):
                filter_parts.append(f"source {filters['src_ip']}")
            if filters.get("dest_ip"):
                filter_parts.append(f"destination {filters['dest_ip']}")
            if filters.get("src_port"):
                filter_parts.append(f"sport {filters['src_port']}")
            if filters.get("dest_port"):
                filter_parts.append(f"dport {filters['dest_port']}")
            if filters.get("protocol"):
                filter_parts.append(f"protocol {filters['protocol']}")
            filter_str = ' '.join(filter_parts)

            # Set the filter using <match>
            if filter_str:
                params = {
                    "type": "op",
                    "cmd": f"<request><packet-capture><filter><match>{filter_str}</match></filter></packet-capture></request>",
                    "key": api_key
                }
                requests.get(url, params=params, verify=False)
            # Start the capture at the firewall stage
            params = {
                "type": "op",
                "cmd": "<request><packet-capture><start><stage><firewall/></stage></start></packet-capture></request>",
                "key": api_key
            }
            requests.get(url, params=params, verify=False)
            return True, f"Packet capture started with filter: {filter_str}"
        except Exception as e:
            return False, f"Error starting capture: {e}"

    def stop_packet_capture(self, stage_name):
        """
        Stops the filter-based packet capture using the canonical operational command.
        """
        if not self.fw:
            return False, "Not connected to firewall."
        try:
            api_key = self.fw.api_key
            url = f"https://{self.hostname}/api/"
            params = {
                "type": "op",
                "cmd": "<request><packet-capture><stop/></packet-capture></request>",
                "key": api_key
            }
            requests.get(url, params=params, verify=False)
            return True, "Packet capture stopped."
        except Exception as e:
            return False, f"Error stopping capture: {e}"

    def clear_packet_capture(self, stage_name):
        """
        Clears the filter-based packet capture files using the operational command API.
        """
        if not self.fw:
            return False, "Not connected to firewall."
        try:
            api_key = self.fw.api_key
            url = f"https://{self.hostname}/api/"
            params = {
                "type": "op",
                "cmd": "<clear><filter-pcap>all</filter-pcap></clear>",
                "key": api_key
            }
            requests.get(url, params=params, verify=False)
            return True, "Packet capture cleared."
        except Exception as e:
            return False, f"Error clearing capture: {e}"

    def download_packet_capture(self, stage_name, save_path):
        """
        Downloads all available filtered packet capture files (rx, tx, drp, fw) using the correct API for your PAN-OS version.
        Uses POST, category=filters-pcap, and from=<filename>.
        """
        if not self.fw:
            return False, "Not connected to firewall."
        try:
            api_key = self.fw.api_key
            url = f"https://{self.hostname}/api/"
            files_downloaded = []
            errors = []
            for fname in ["rx.pcap", "tx.pcap", "drp.pcap", "fw.pcap"]:
                params = {
                    'type': 'export',
                    'category': 'filters-pcap',
                    'from': fname,
                    'key': api_key
                }
                response = requests.post(url, params=params, verify=False, stream=True)
                if response.status_code == 200 and response.headers.get('content-type', '').startswith('application/octet-stream'):
                    out_path = f"{stage_name}_{fname}"
                    with open(out_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    files_downloaded.append(out_path)
                elif 'No such file or directory' in response.text or 'No such file' in response.text:
                    continue  # File doesn't exist, skip
                else:
                    errors.append(f"{fname}: {response.text}")
            if files_downloaded:
                return True, f"Downloaded: {', '.join(files_downloaded)}"
            else:
                return False, f"No capture files found. Errors: {'; '.join(errors)}"
        except Exception as e:
            return False, f"Error downloading capture: {e}"

def download_filtered_pcap(hostname, api_key, filename, save_path):
    url = f"https://{hostname}/api/"
    params = {
        "type": "export",
        "category": "filters-pcap",
        "from": filename,
        "key": api_key
    }
    response = requests.post(url, params=params, verify=False, stream=True)
    if response.status_code == 200 and response.headers.get('content-type', '').startswith('application/octet-stream'):
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True, f"Downloaded {filename} to {save_path}"
    else:
        return False, f"Failed to download: {response.text}" 