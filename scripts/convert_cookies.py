import json
from datetime import datetime

# Chemin du fichier JSON exporté
input_path = '/Users/happi/cookies.txt'
# Chemin du fichier texte à générer
output_path = '/Users/happi/cookies_converted.txt'

with open(input_path, 'r') as f:
    cookies = json.load(f)

header = '# Netscape HTTP Cookie File\n# This file is generated from JSON cookies export\n\n'

lines = [header]
for c in cookies:
    domain = c['domain']
    flag = 'TRUE' if not c.get('hostOnly', False) else 'FALSE'
    path = c['path']
    secure = 'TRUE' if c.get('secure', False) else 'FALSE'
    expires = str(int(c.get('expirationDate', 0)))
    name = c['name']
    value = c['value']
    http_only = c.get('httpOnly', False)
    # Format: domain\tflag\tpath\tsecure\texpires\tname\tvalue
    line = f'{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n'
    lines.append(line)

with open(output_path, 'w') as f:
    f.writelines(lines)

print(f'Cookies convertis et sauvegardés dans {output_path}')