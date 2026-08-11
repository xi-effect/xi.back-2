def bitwise_cyclic_shift_left(value: int, size: int, rotations: int = 1) -> int:
    return ((value << rotations) % (1 << size)) | (value >> (size - rotations))


def bitwise_cyclic_shift_right(value: int, size: int, rotations: int = 1) -> int:
    return ((1 << size) - 1) & (value >> rotations | value << (size - rotations))
