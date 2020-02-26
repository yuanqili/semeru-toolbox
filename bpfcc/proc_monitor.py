import re
from pathlib import Path
from pprint import pprint


class ProcMonitor:
    """
    http://man7.org/linux/man-pages/man5/proc.5.html
    """

    def __init__(self, pid):
        self.pid = pid
        self.proc_path = Path(f'/proc/{pid}')

    def smaps(self, pathname_filter=None, field_filter=None, sort_by_size=True):
        smaps_path = self.proc_path / 'smaps'
        with open(smaps_path, 'r') as f:
            smaps_data = f.readlines()
        smaps = self.smaps_parser(smaps_data, field_filter)
        if pathname_filter:
            smaps = [item for item in smaps if item['pathname'] in pathname_filter]
        if sort_by_size:
            smaps.sort(key=lambda x: x['Size'])
        return smaps

    @staticmethod
    def smaps_parser(smaps_data, field_filter=None):
        pattern = r'[0-9a-f]*-[0-9a-f]*\s*'
        if field_filter is None:
            field_filter = ['Size', 'KernelPageSize', 'MMUPageSize', 'Rss', 'Pss',
                            'Shared_Clean', 'Shared_Dirty', 'Private_Clean',
                             'Private_Dirty', 'Referenced', 'Anonymous', 'LazyFree',
                             'AnonHugePages', 'ShmemPmdMapped', 'Shared_Hugetlb',
                             'Private_Hugetlb', 'Swap', 'SwapPss', 'Locked']
        smaps = []
        mapping = {}
        for line in smaps_data:
            if re.match(pattern, line):
                if mapping != {}:
                    smaps.append(mapping)
                    mapping = {}
                try:
                    address, permission, offset, dev, inode, pathname = line.split()
                except ValueError:
                    address, permission, offset, dev, inode = line.split()
                    pathname = ''
                address_start, address_end = address.split('-')
                mapping['pathname'] = pathname
                mapping['address_start'] = int(address_start, 16)
                mapping['address_end'] = int(address_end, 16)
                mapping['permission'] = permission
                mapping['offset'] = int(offset, 16)
                mapping['dev'] = dev
                mapping['inode'] = inode
            else:
                items = line.split()
                name = items[0][:-1]
                if name in field_filter:
                    mapping[name] = int(items[1])
                elif name == 'THPeligible':
                    mapping[name] = items[1]
                elif name == 'VmFlags':
                    mapping[name] = ' '.join(items[1:])
        return smaps

    def pagemap(self):
        ...


if __name__ == '__main__':

    pm = ProcMonitor(pid=23391)
    smaps = pm.smaps(pathname_filter=['', '[heap]'],
                     field_filter=['Size', 'Rss', 'Swap'])
    pprint([(hex(item['address_start']), hex(item['address_end']), item['Size'],
             item['Rss'], item['Swap'], item['pathname'])
            for item in smaps])
