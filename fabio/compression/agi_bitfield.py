from io import BytesIO
from struct import pack, unpack

import numpy as np

unpack_ = unpack
unpack = lambda fmt, buff: unpack_(fmt, buff)[0]


def compress(frame):
    """compress a frame using the agi_bitfield algorithm
    :param frame: numpy.ndarray
    :returns bytes
    """

    dim = frame.shape
    buffer = BytesIO()

    row_adresses = BytesIO()

    for frame_row in range(0, dim[0]):
        row_adresses.write(pack("I", buffer.tell() + 4))
        compress_row(frame[frame_row], buffer)

    data_size = pack("I", buffer.tell())
    buffer.write(row_adresses.getvalue())

    row_adresses.close()
    return data_size + buffer.getvalue()


def compress_row(data, buffer):
    """compress a single row
    :arg data numpy.array
    :arg buffer io.BytesIO
    """

    first_pixel = data[0]
    pixel_diff = data[1:] - data[:-1]

    write_escaped(first_pixel, buffer)

    n_fields = len(pixel_diff) // 16
    n_restpx = len(pixel_diff) % 16

    for field in range(0, n_fields):
        fielda = pixel_diff[:8]
        fieldb = pixel_diff[8:16]

        len_a, len_b = get_fieldsize(fielda), get_fieldsize(fieldb)
        len_byte = (len_b << 4) | (0xf & len_a)
        buffer.write(pack("B", len_byte))

        of_buff = BytesIO()
        compressed_fielda = compress_field(fielda, len_a, of_buff)
        compressed_fieldb = compress_field(fieldb, len_b, of_buff)

        buffer.write(compressed_fielda + compressed_fieldb + of_buff.getvalue())

        pixel_diff = pixel_diff[16:]

    for restpx in range(0, n_restpx):
        write_escaped(pixel_diff[restpx], buffer)


def decompress(comp_frame, dimensions):
    """decompresses a frame that was compressed using the agi_bitfield algorithm
    :param comp_frame: bytes
    :param dimensions: tuple
    :return numpy.ndarray
    """

    row_count, col_count = dimensions

    # read data components (row indices are ignored)
    data_size = unpack("I", comp_frame[:4])
    data_block = BytesIO(comp_frame[4:])

    output = []

    # iterate over rows
    for row_index in range(0, row_count):
        output.append(decompress_row(data_block, col_count))

    return np.array(output, dtype="int32").cumsum(axis=1)


def decompress_row(buffer, row_length):
    """decompress a single row
    :param buffer: io.BytesIO
    :param row_length: int
    :returns list
    """

    first_pixel = read_escaped(buffer)

    n_fields = (row_length - 1) // 16
    n_restpx = (row_length - 1) % 16

    pixels = [first_pixel]

    for field in range(n_fields):
        lb = unpack("B", buffer.read(1))
        len_b, len_a = read_len_byte(lb)

        field_a = decode_field(buffer.read(len_a))
        field_b = decode_field(buffer.read(len_b))

        undo_escapes(field_a, len_a, buffer)
        undo_escapes(field_b, len_b, buffer)

        pixels += field_a
        pixels += field_b

    for restpx in range(n_restpx):
        pixels.append(read_escaped(buffer))

    return pixels


def get_fieldsize(array):
    """determine the fieldsize to store the given values
    :param array numpy.array
    :returns int
    """

    def fieldsize(n):
        return min(8, max(1, abs(n.item()).bit_length() + 1))

    return max(fieldsize(array.max()), fieldsize(array.min()))


def compress_field(ifield, fieldsize, overflow_table):
    """compress a field with given size
    :param ifield: numpy.ndarray
    :param fieldsize: int
    :param overflow_table: io.BytesIO
    :returns int
    """

    compressed_field = np.uint64(0)  # uint64
    fieldsize = np.uint8(fieldsize)

    mask_ = mask(fieldsize)
    conv_ = conv(fieldsize)
    for i, elem in enumerate(ifield):
        if -127 <= elem < 127:
            val = np.uint8((elem + conv_) & mask_)
        elif -32767 <= elem < 32767:
            val = np.uint8(254)
            overflow_table.write(pack("h", elem))
        else:
            val = np.uint8(255)
            overflow_table.write(pack("i", elem))
        compressed_field = val | (compressed_field << fieldsize)
    return pack("Q", compressed_field)[:fieldsize]


def decode_field(field):
    """decodes a field from bytes
    :param field: bytes
    :returns list
    """
    size = len(field)
    assert 0 < size <= 8, str(size)
    field = unpack("Q", field + (b'\x00' * (8 - size)))
    mask_ = mask(size)
    values = []
    for i in range(0, 8):
        values.append((field >> (size * (7 - i)) & mask_))
    return values


def read_len_byte(lb):
    """parses the length byte and returns the sizes of the next twofields
    :param lb: int/byte
    :returns tuple
    """
    return lb >> 4,  lb & 0xf


def mask(length):
    """returns a bit mask of the given length
    :param length: int
    :returns int
    """
    return (1 << length) - 1


def conv(length):
    """returns the conversion value of the given length
    :param length: int
    :returns int
    """
    return (1 << length - 1) - 1


def write_escaped(value, buffer):
    """write an value to the buffer and escape when overflowing one byte
    :param value: int
    :param buffer: io.BytesIO
    """
    if -127 <= value < 127:
        buffer.write(pack("B", value + 127))
    elif -32767 < value < 32767:
        buffer.write(b'\xfe' + pack("h", value))
    else:
        buffer.write(b'\xff' + pack("i", value))


def read_escaped(buffer):
    """reads byte value that might be escaped from a buffer
    :param buffer: io.BytesIO
    :returns int
    """
    byte = buffer.read(1)
    if byte == b'\xfe':  # two byte overflow
        return unpack("h", buffer.read(2))
    elif byte == b'\xff':  # four byte overflow
        return unpack("i", buffer.read(4))
    else:  # no overflow
        return unpack("B", byte) - 127


def undo_escapes(field, length, buffer):
    """undo escaping of values in a field
    :param field: list
    :param length: int
    :param buffer: io.BytesIO
    """
    conv_ = conv(length)
    for i, val in enumerate(field):
        if val == 0xfe:
            field[i] = unpack("h", buffer.read(2))
        elif val == 0xff:
            field[i] = unpack("i", buffer.read(4))
        else:
            field[i] = field[i] - conv_
