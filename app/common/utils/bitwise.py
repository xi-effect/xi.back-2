def construct_continuous_bitmask(left: int, right: int, size: int) -> int:
    if left <= right:
        bitmask = 0
        for bit in range(left, right + 1):
            bitmask ^= 1 << bit
    else:
        bitmask = (1 << size) - 1
        for bit in range(right, left - 1):
            bitmask ^= 1 << bit
    return bitmask


def bitwise_cyclic_shift_left(value: int, size: int, rotations: int = 1) -> int:
    return ((value << rotations) % (1 << size)) | (value >> (size - rotations))


def bitwise_cyclic_shift_right(value: int, size: int, rotations: int = 1) -> int:
    return ((1 << size) - 1) & (value >> rotations | value << (size - rotations))
