with open('test_licm.py', 'rb') as f:
    c = f.read()
c = c.replace(b'\x00', b'')
c = c.replace(b'print("\\\\nFlattened:")', b'print("\\nFlattened:")')
with open('test_licm.py', 'wb') as f:
    f.write(c)
