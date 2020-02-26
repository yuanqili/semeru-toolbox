import os
import re
import struct
from pathlib import Path


class ProcMonitor:
    """
    - [proc](http://man7.org/linux/man-pages/man5/proc.5.html)
    - [pagemap](https://www.kernel.org/doc/Documentation/vm/pagemap.txt)
    """

    def __init__(self, pid):
        self.pid = pid
        self.proc_path = Path(f'/proc/{pid}')

    def smaps(self, pathname_filter=None, field_filter=None, sort_by_size=True):
        smaps_path = self.proc_path / 'smaps'
        with open(smaps_path, 'r') as f:
            smaps_data = f.readlines()
        smaps = self._smaps_parser(smaps_data, field_filter)
        if pathname_filter:
            smaps = [item for item in smaps if item['pathname'] in pathname_filter]
        if sort_by_size:
            smaps.sort(key=lambda x: x['Size'])
        return smaps

    def maps(self, pathname_filter=None):
        maps_path = self.proc_path / 'maps'
        with open(maps_path, 'r') as f:
            maps_data = f.readlines()
        maps = self._maps_parser(maps_data)
        if pathname_filter:
            maps = [item for item in maps if item['pathname'] in pathname_filter]
        return maps

    def pagemap(self, addr_start, addr_end):
        pagemap_path = self.proc_path / 'pagemap'
        page_size = os.sysconf('SC_PAGE_SIZE')
        pagemap_entry_size = 8
        base_offset = (addr_start // page_size) * pagemap_entry_size

        page_in, page_out = 0, 0
        pagemap = open(pagemap_path, 'rb')
        pagemap.seek(base_offset, 0)
        for addr in range(addr_start, addr_end, 0x1000):
            entry = struct.unpack('Q', pagemap.read(8))[0]
            if self.is_page_present(entry):
                page_in += 1
            if self.is_page_swapped(entry):
                page_out += 1
        pagemap.close()

        if page_in + page_out == 0:
            return {'in': 0, 'out': 0, 'count': 0, 'ratio': 0}
        else:
            return {
                'in': page_in,
                'out': page_out,
                'count': page_in + page_out,
                'ratio': page_in / (page_in + page_out),
            }

    @staticmethod
    def _smaps_parser(smaps_data, field_filter=None):
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

    @staticmethod
    def _maps_parser(maps_data):
        maps = []
        for line in maps_data:
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
            maps.append(mapping)
        return maps

    @staticmethod
    def is_page_present(entry):
        return (entry & (1 << 63)) != 0

    @staticmethod
    def is_page_swapped(entry):
        return (entry & (1 << 62)) != 0
