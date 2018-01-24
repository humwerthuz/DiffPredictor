import struct

def rshift(val, n):
	return (val % 0x100000000) >> n

def lshift(val, n):
	return (val % 0x100000000) << n

def compactFromBigNum(bigNum):
	exponent = (len(hex(bigNum))-2)/2
	mantissa = 0

	if(exponent <= 3):
		mantissa = bigNum
		mantissa <<= 8 * (3 - exponent)
	else:
		mantissa = bigNum >> (8 * (exponent - 3))

	if mantissa & 0x800000:
		mantissa >>= 8
		exponent += 1

	compact = (exponent << 24) | mantissa

	if(bigNum < 0):
		compact |= 0x800000;

	return rshift(compact, 0)

def bigNumFromCompact(compact):
	if(compact == 0):
		return 0

	num = 0

	exponent = rshift(compact, 24)
	negative = rshift(compact, 23) & 1

	mantissa = compact & 0x7fffff
	if (exponent <= 3):
		num = rshift(mantissa, 8 * (3 - exponent))
	else:
		num = mantissa
		num <<= (8 * (exponent - 3))

	if num < 0: 
		num *= -1

	return num


def reverseByteOrder(line):
	byteList = [line[i:i+2] for i in range(0, len(line), 2)]
	byteList.reverse()
	return "".join(byteList)

def uint1(stream, binary=True):

	return ord(stream.read(1 if binary else 2))

def uint2(stream, binary=True):
	return struct.unpack('H', stream.read(2 if binary else 4))[0]

def uint4(stream, binary=True):
	return struct.unpack('I', stream.read(4 if binary else 8))[0]

def uint8(stream, binary=True):
	return struct.unpack('Q', stream.read(8 if binary else 16))[0]

def hash32(stream, binary=True):
	return stream.read(32 if binary else 32)[::-1]

def time(stream, binary=True):
	time = uint4(stream, binary)
	return time

def varint(stream, binary=True):
	size = uint1(stream, binary)

	if size < 0xfd:
		return size
	if size == 0xfd:
		return uint2(stream, binary)
	if size == 0xfe:
		return uint4(stream, binary)
	if size == 0xff:
		return uint8(stream, binary)
	return -1

def hashStr(bytebuffer):
	return ''.join(('%02x'%ord(a)) for a in bytebuffer)

