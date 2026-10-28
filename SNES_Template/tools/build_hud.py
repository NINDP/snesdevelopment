"""Six-row exploration dashboard; every text line is inside the mode boundary."""
import struct


def build(out, assembly):
    attr = (7 << 10) | (1 << 13)
    rows = [256 | attr] * (32 * 6)
    for x in range(1, 31):
        rows[x] = 261 | attr
        rows[5*32+x] = 262 | attr
        rows[2*32+x] = 261 | attr
    for y in range(1, 5):
        rows[y*32] = 263 | attr
        rows[y*32+31] = 264 | attr
    for index, tile in ((0,265),(31,266),(160,267),(191,268)):
        rows[index] = tile | attr
    for x, y, label in ((2,1,'ФАКЕЛ'),(13,1,'СТРАХ'),
                        (2,3,'ЧЕРНОРЕЧЬЕ'),(2,4,'A ОСМОТР  X СВЕТ  Y ЗАПИСИ')):
        for offset, ch in enumerate(label.encode('cp1251')):
            rows[y*32+x+offset] = ch | attr
    (out/'exploration-hud.map').write_bytes(struct.pack('<192H', *rows))
    assembly += ['.section "exploration_hud" superfree', 'exploration_hud:',
                 '.incbin "assets/generated/exploration-hud.map"', '.ends', '']
    # Runtime copies tile IDs instead of formatting/dividing on the 65C816.
    def tiles(label):
        return struct.pack('<%dH'%len(label), *(ch | attr for ch in label.encode('ascii')))
    clocks = b''.join(tiles('%02d:%02d'%(second//32, (second%32)*60//32))
                      for second in range(768))
    numbers = b''.join(tiles('%3d'%value) for value in range(121))
    for name, payload in (('hud-clocks', clocks), ('hud-numbers', numbers)):
        (out/(name+'.map')).write_bytes(payload)
        assembly += ['.section "'+name+'" superfree', name.replace('-', '_')+':',
                     '.incbin "assets/generated/'+name+'.map"', '.ends', '']
