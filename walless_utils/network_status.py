from threading import Thread
import time
import requests


class NetworkStatus:
    ipv6_check_patience = 3

    def __init__(self, refresh_interval: int = 5, patience: int = 2):
        """
        Check the status of the network to see if IPv4 or IPv6 are available.
        :param refresh_interval: In seconds. How long does it take to perform a refresh.
        :param patience: How many trials will be conducted.
        """
        self.refresh_interval = float(refresh_interval)
        self.patience = patience
        self.ips = {4: None, 6: None}
        # pull information
        Thread(None, self.pull_network_status).start()
        # this flag is True if all checkups are done.
        self.checking_done_flag = False

    @property
    def ipv4(self):
        return self.ips.get(4)

    @property
    def ipv6(self):
        return self.ips.get(6)

    def network_is_available(self):
        return self.ipv4 is not None or self.ipv6 is not None

    def pull_network_status(self):
        # pull the network status from ipify

        def pull(protocol, patience):
            start = time.time()
            # for ipv4
            for i in range(patience):
                try:
                    ip_addr = requests.get(f'https://api{protocol}.ipify.org').text.strip()
                    if ip_addr != '':
                        self.ips[protocol] = ip_addr
                    return
                except KeyboardInterrupt:
                    return
                except:
                    time.sleep(max(0, -time.time() + self.refresh_interval * (i+1) + start))

        pull(4, self.patience)
        pull(6, self.ipv6_check_patience)
        self.checking_done_flag = True

    def wait_for_network(self):
        for i in range(self.patience):
            if self.network_is_available():
                return
            time.sleep(self.refresh_interval)

    def wait_for_checkups(self):
        # wait until all checkups are done
        for i in range(self.patience + self.ipv6_check_patience):
            if self.checking_done_flag:
                return
            time.sleep(self.refresh_interval)
