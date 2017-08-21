from niah.base import BaseIOS

class CiscoIOS(BaseIOS):

        @property
        def _running_config(self):
            return self.cmd('show run').split('\r\n')

        @property
        def config_parse(self):
            """
                Returns a list of objects to parse the running config
            """
            return ciscoconfparse.CiscoConfParse(self._running_config, factory=True)

        def shorten_int_name(self,interface_name):
            """
            Returns the Cisco shortened interface name from a full one.
            If the full interface name is invalid, this will return None
            """

            short = None
            regex = "(\w{2}).*?(\d+(?:/\d+)?(?:/\d+)?)"

            match = re.match(regex, interface_name)

            if match is not None:
                short = ""
                for group in match.groups():
                    short += group

            return short

        def get_arp_table(self):
            """
            Returns the ARP table from the device as a list of dicts.
            Only retreives IP and ARPA addresses at the moment.

            {ip, age, mac, interface}
            """
            re_text = 'Internet\s+(?P<ip>\d+\.\d+\.\d+\.\d+)\s+(\d+|-)\s+((?:\d|\w){4}\.(?:\d|\w){4}\.(?:\d|\w){4})\s+ARPA\s+(.+)\r?\n?'
            table = dict()
            for item in re.findall(re_text, self.cmd("show arp")):
                #print "%s,%s,%s,%s,%s"%(self.host,item[0],item[1],item[2],item[3])
                table[item[0]] = {
                    "age": item[1],
                    "mac": item[2],
                    "interface": item[3].strip()
                }

            return table

        def get_model(self):
            """ Gets the model number of the switch using the `get version` command """

            re_text = '[cC]isco (\S+) .* memory.'
            cmd_output = self.cmd('show version')
            match = re.search(re_text, cmd_output)
            if match is not None:
                one = match.group(1)
                if one is not None:
                    model = one
                else:
                    model = None
            else:
                model = None

            return model

        def task(self):
            pass

        def get_neighbors(self):
            """ Returns a list of dicts of the switch's neighbors:
                {hostname, ip, local_port, remote_port} """
            data = self.cmd('show cdp nei det')
            re_text = "-+\r?\nDevice ID: (.+)\\b\r?\n.+\s+\r?\n\s*IP address:\s+(\d+\.\d+\.\d+\.\d+)\s*\r?\n(?:\s+IPv6 address.*\r?\n)?.*\r?\nInterface: (.+),.+Port ID.+: (.+)\\b\r?\n"
            neighbors = {}
            for hostname, ip, local_port, remote_port in re.findall(re_text, data):
                #n_dict['hostname'], n_dict['ip'], n_dict['local_port'], n_dict['remote_port'] = neighbor
                neighbors[hostname] = {
                    'ip': ip,
                    'local_port': local_port,
                    'remote_port': remote_port
                }
            return neighbors

        def get_mac_table(self):
            """ Returns the mac address table from the device """
            re_text = '\*?\s+(\d+|All)\s+((?:\d|\w){4}\.(?:\d|\w){4}\.(?:\d|\w){4})\s+(static|dynamic)\s+(?:(?:Yes|No)\s+(?:-|\d+)\s+)?(.+?)\r?\n'

            try:
                data = self.cmd("show mac address-table")
            except:
                try:
                    data = self.cmd("show mac-address-table")
                except:
                    print self.child.before
                    raise errors.ModelNotSupported("No MAC address table command", self.ip)

            table = None
            if data is not None:
                rows = re.findall(re_text, data, flags=re.I)
                table = dict()
                for row in rows:
                    table[row[1]] = {
                        'vlan': row[0],
                        'type': row[2],
                        'port': row[3].strip()
                    }

            return table

        def get_interfaces(self,interface=None):
            data = self.cmd("show ip interface brief")
            self.interfaces = dict()
            data = data.split('\n')
            index = [s for s in data if 'Interface' in s]
            index = data.index(index[0]) + 1
            for line in data[index:]:
                row = line.split()
                if len(row) > 0:
                    if 'administratively' in row[4]:
                        row[4] = 'administratively down'

                    self.interfaces[row[0]] = {
                        'ip_address': row[1],
                        'status': row[4],
                        'protocol': row[5]
                    }
            return self.interfaces

        def get_interfaces_config(self):
            self.get_interfaces()
            config = dict()
            for k,v in self.interfaces.iteritems():
                if v['status'] != 'deleted' and 'NVI' not in k:
                    data = self.cmd("show run int " + k)
                    data = data.split('\n')[5:-3]
                    config[k] = data
            return config

        def get_interface_stats(self):
            data = []
            stats = dict()
            for k,v in self.interfaces.iteritems():
                stats[k] = dict()
                if v['status'] != 'deleted':
                    stats[k]['load'] = dict()
                    stats[k]['errors'] = dict()
                    self.interfaces[k]['description'] = dict()
                    data = self.cmd("show interface %s | i is up|is down|output drops|input errors|output errors|[dD]uplex|load|MTU|escription"%(k))
                    regex = dict()
                    regex = {
                        'description': '[dD]escription[:]? ([ \S]+)\r?\n',
                        'mtu':'\s+MTU (\d+) bytes',
                        'bw':'BW (\d+ Kbit/sec)',
                        'dly':'DLY (\d+) usec',
                        'txload':'txload (\d{1,3}/255)',
                        'rxload':'rxload (\d{1,3}/255)',
                        'duplex':'(Auto|Full)[ -][dD]uplex',
                        'speed' :'(?:Auto|Full)-[dD]uplex\, (\w+)',
                        'media_type':'media type is (\S+)',
                        'output_drops':'output drops: (\d+)',
                        'input_errors':'(\d+) input errors',
                        'crc_errors':'(\d+) CRC',
                        'output_errors':'(\d+) output errors'
                    }
                    for key, value in regex.iteritems():
                        found = re.findall(value,data)
                        if not found:
                            found.append('N/A')
                        if 'txload' in key:
                            stats[k]['load']['tx'] = found[0]
                        elif 'rxload' in key:
                            stats[k]['load']['rx'] = found[0]
                        elif 'input_errors' in key:
                            stats[k]['errors']['input'] = found[0]
                        elif 'output_errors' in key:
                            stats[k]['errors']['output'] = found[0]
                        elif 'crc_errors' in key:
                            stats[k]['errors']['crc'] = found[0]
                        elif 'description' in key:
                            self.interfaces[k]['description'] = found[0]
                        else:
                            stats[k][key] = found[0]
                        found = None
            return stats

        def get_lan_interfaces(self):
            interfaces = self.get_interfaces()
            lan_interfaces = []
            for k,v in interfaces.iteritems():
                if v['ip_address'] != 'unassigned' and 'down' not in v['status'] and 'Loopback' not in k:
                    if IPAddress(v['ip_address']) in IPNetwork('10.0.0.0/8'):
                        lan_interfaces.append(k)
            return lan_interfaces

        def get_wan_interface(self):
            interfaces = self.get_interfaces()
            wan_interface = []
            for k,v in interfaces.iteritems():
                if v['ip_address'] != 'unassigned' and 'down' not in v['status']:
                    if not IPAddress(v['ip_address']).is_private():
                        wan_interface.append(k)
                    else:
                        for NETWORK in WAN_NETWORKS:
                            if IPAddress(v['ip_address']) in NETWORK:
                                return k


            return wan_interface

        def get_inventory(self):
            data = self.cmd("show inventory")
            re_text = r'(?:NAME:[^"]+"([^"]+)", DESCR:[^"]+"([^"]+)".*\r?\nPID: ([^ ]+)\s+.*SN: (.*))'
            rows = re.findall(re_text, data)
            table = dict()
            table['inventory'] = []
            for row in rows:
                table['inventory'].append({
                    'name': row[0],
                    'descriptione': row[1],
                    'pid': row[2],
                    'serial_number': row[3].strip()
                })
            return table

        def save(self):
            self.write('wr mem')
            exp_list = self.child.compile_pattern_list(['confirm\]','OK\]','#'])
            j = 0
            while True:
                i = self.child.expect_list(exp_list)
                if i == 0:
                    self.write('')
                    continue
                if i == 1:
                    self.logger.info("Saved Config Successfully")
                if i == 2:
                    break
