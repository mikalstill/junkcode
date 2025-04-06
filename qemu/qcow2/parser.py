#!/usr/bin/python3

# A plaything qcow2 implementation. Format documentation is at
# https://gitlab.com/qemu-project/qemu/-/blob/master/docs/interop/qcow2.txt

import mmap
import os
import struct
import sys


class OutOfBounds(Exception):
    ...


class FormatError(Exception):
    ...


class MMapHelper:
    def __init__(self, fd):
        self.fd = fd

    def __enter__(self):
        self.st = os.fstat(self.fd)
        self.max_size = self.st.st_size
        self.mmap = mmap.mmap(self.fd, 0)
        self.offset = 0
        return self

    def __exit__(self, *args):
        self.mmap.close()

    def unpack_from(self, format, length, offset):
        if offset + length > self.max_size:
            raise OutOfBounds()
        return struct.unpack_from(format, self.mmap, offset=offset)


class MMapSequenceReader:
    def __init__(self, mm, offset=0):
        self.mm = mm
        self.offset = offset

    def __enter__(self):
        return self

    def __exit__(self, *args):
        ...

    def unpack(self, format):
        length = struct.calcsize(format)
        out = self.mm.unpack_from(format, length, self.offset)
        self.offset += length
        return out


crypt_method_to_string = {
    0: 'unencrypted',
    1: 'AES',
    2: 'LUKS'
}


compression_type_to_string = {
    0: 'deflate',
    1: 'zstd'
}


feature_type_to_string = {
    0: 'incompatible',
    1: 'compatible',
    2: 'autoclear'
}


with (
    open(sys.argv[1], 'r+b') as f,
    MMapHelper(f.fileno()) as mm
):
    with MMapSequenceReader(mm, offset=0) as first_cluster:
        magic, version = first_cluster.unpack('>4sI')
        if magic != b'QFI\xfb':
            raise FormatError(f'This is not a qcow2 file (magic {magic})!')
        if version not in [2, 3]:
            raise FormatError(f'Unknown version: {version}')
        print(f'qcow2 version: {version}')
        print()

        bf_path_offset, bf_path_size = first_cluster.unpack('>QI')
        print(f'Backing path offset: {bf_path_offset}')
        print(f'Backing path size: {bf_path_size}')
        if bf_path_offset != 0:
            with MMapSequenceReader(mm, offset=0) as backing_path_reader:
                (bf_path, ) = backing_path_reader.unpack(f'{bf_path_size}s')
                print(f'Backing path: {bf_path}')
        print()

        (
            cluster_bits, virtual_size, crypt_method, layer1_size,
            layer1_offset, refcount_table_offset, refcount_table_clusters,
            snapshots_count, snapshots_offset
        ) = first_cluster.unpack('>IQIIQQIIQ')

        crypt_method_str = crypt_method_to_string.get(crypt_method, 'unknown')
        cluster_size = pow(2, cluster_bits)
        print(f'Cluster bits: {cluster_bits} ({cluster_size} bytes per cluster)')
        print(f'Virtual size: {virtual_size}')
        print(f'Encryption method: {crypt_method_str}')
        print()

        print(f'Number of layer 1 entries: {layer1_size}')
        print(f'Layer 1 table offset: {layer1_offset} (cluster '
              f'{int(layer1_offset / cluster_size)})')
        print()

        print(f'Refcount table offset: {refcount_table_offset} (cluster '
              f'{int(refcount_table_offset / cluster_size)})')
        print(f'Number of clusters for refcount table: {refcount_table_clusters}')
        print()

        print(f'Number of snapshots: {snapshots_count}')
        print(f'Snapshots offset: {snapshots_offset} (cluster '
              f'{int(snapshots_offset / cluster_size)})')
        print()

        if version == 2:
            refcount_order = 4
            header_length = 72

        if version == 3:
            (
                incompatible_features, compatible_features, autoclear_features,
                refcount_order, header_length, compression_type
            ) = first_cluster.unpack('>QQQIIB')

            compression_type_str = compression_type_to_string.get(compression_type)
            print(f'v3 Incompatible features bits: {incompatible_features}')
            print(f'v3 Compatible features bits: {compatible_features}')
            print(f'v3 Autoclear features bits: {autoclear_features}')
            print(f'v3 Refcount order: {refcount_order}')
            print(f'v3 Header length: {header_length}')
            print(f'v3 Compression type: {compression_type} '
                  f'({compression_type_str})')
            print()

            # Padding to a multiple of 8 bytes
            first_cluster.unpack('>7B')

            # Possible header extensions
            count = 0
            (extension_type, ) = first_cluster.unpack('>I')
            print(f'v3 header extension {count} type: 0x{extension_type:0x} at '
                  f'offset {first_cluster.offset}')
            while extension_type != 0:
                (extension_length, ) = first_cluster.unpack('>I')
                print(f'v3 header extension {count} length: {extension_length}')
                print(f'v3 header extension {count} length % 8: {extension_length % 8}')

                if extension_type == 0xe2792aca:
                    (format, ) = first_cluster.unpack(f'>{extension_length}s')
                    print(f'    ... backing file format: {format.decode()}')

                elif extension_type == 0x6803f857:
                    print('    ... feature name table:')
                    end_byte = first_cluster.offset + extension_length
                    while first_cluster.offset < end_byte:
                        (
                            feature_type, feature_bit, feature_name
                        ) = first_cluster.unpack('>BB46s')

                        feature_type_str = feature_type_to_string.get(
                            feature_type, 'unknown')
                        feature_name_str = feature_name.rstrip(b'\x00').decode()
                        print(f'    ... {feature_type_str} bit '
                              f'{feature_bit} named {feature_name_str}')

                else:
                    extension_data = first_cluster.unpack(f'{extension_length}B')
                    print(f'v3 header extension {count} data: {extension_data}')

                if extension_length % 8 == 0:
                    print(f'v3 header extension {count} requires no padding')
                else:
                    padding = 8 - (extension_length % 8)
                    first_cluster.offset += padding
                    print(f'v3 header extension {count} padding: {padding}')
                print()

                count += 1
                (extension_type, ) = first_cluster.unpack('>I')
                print(f'v3 header extension {count} type 0x{extension_type:0x} at offset '
                    f'{first_cluster.offset}')
            print()

    # Read L1 table entries
    with MMapSequenceReader(mm, offset=layer1_offset) as l1_table:
        for count in range(layer1_size):
            print(f'L1 table entry {count} of {layer1_size}')
            (l1_table_bytes, ) = l1_table.unpack('>Q')

            if l1_table_bytes & 0xFF:
                print(f'    ... unknown value for bits 0-8! '
                      f'({l1_table_bytes[0]:0x})')

            # This is icky -- the bottom 8 bits might one day be reused, but
            # they're also always zero in a L2 offset because clusters must be
            # at least 512 big. So, we can just use those reserved bits to make
            # the maths easier, in return for some theoretical future fragility
            l2_offset = l1_table_bytes & 0xFFFFFFFFFFFF
            print(f'    ... l2 offset: {l2_offset} (cluster '
                  f'{int(l2_offset / cluster_size)})')

            if l1_table_bytes >> 56 & 0x7f != 0:
                print(f'    ... unknown value for bits 56-62! '
                      f'({l1_table_bytes >> 56 & 0x7f :0x})')

            use_flag = l1_table_bytes >> 63
            if use_flag == 0:
                print(f'    ... entry is unused or requires COW')
            else:
                print(f'    ... entry reference count is exactly 1')

            # for b in l1_table_bytes:
            #     print(f'{b:0x}')

            # l2_offset = 0
            # l2_offset += l2_offset_b1 << 5
            # l2_offset += l2_offset_b2 << 4
            # l2_offset += l2_offset_b3 << 3
            # l2_offset += l2_offset_b4 << 2
            # l2_offset += l2_offset_b5 << 1
            # l2_offset += l2_offset_b6

            # print(f'l1 entry {count} reserved (should be 0): {reserved}')
            # print(f'l2 entry {count} l2 offset: {l2_offset}')
            # print(f'l2 entry {count} reserved and refcount: {reserved_and_refcount}')