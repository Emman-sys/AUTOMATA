data = {}

prefix_expr = None

# Input phase
print("Enter rows in the format X= a,b,c (type 'done' to finish):")
while True:
    line = input()
    if line.strip().lower() == 'done':
        break
    # Check for prefix command
    if line.strip().lower().startswith('prefix'):
        eq_idx = line.find('=')
        if eq_idx != -1:
            prefix_expr = line[eq_idx+1:].strip()
        continue
    if '=' in line:
        key, values = line.split('=', 1)
        key = key.strip()
        # Filter out empty strings caused by trailing commas
        values = [v.strip() for v in values.strip().split(',') if v.strip()]
        data[key] = values

def eval_concat(a, b):
    # a and b can be either a key in data, a temporary list, or a digit string
    if isinstance(a, list):
        left = a
    elif isinstance(a, str) and a.isdigit():
        left = [a]
    else:
        left = data.get(a)
    if isinstance(b, list):
        right = b
    elif isinstance(b, str) and b.isdigit():
        right = [b]
    else:
        right = data.get(b)
    if left is not None and right is not None:
        return left + right
    return None

def eval_plus(a, b):
    # a and b can be either a key in data, a temporary list, or a digit string
    if isinstance(a, list):
        left = a
    elif isinstance(a, str) and a.isdigit():
        left = [a]
    else:
        left = data.get(a)
    if isinstance(b, list):
        right = b
    elif isinstance(b, str) and b.isdigit():
        right = [b]
    else:
        right = data.get(b)
    if left is not None and right is not None:
        result = []
        seen = set()
        for x in left + right:
            if x not in seen:
                result.append(x)
                seen.add(x)
        return result
    return None

import re

def parse_command(cmd, suppress_print=False):
    cmd = cmd.strip()
    # Helper: recursively replace all |...| with their lengths
    def eval_bars(s):
        bar_pattern = r'\|([^|]+)\|'
        while re.search(bar_pattern, s):
            s = re.sub(bar_pattern, lambda m: str(
                len(parse_command(m.group(1).strip(), suppress_print=True))
                if isinstance(parse_command(m.group(1).strip(), suppress_print=True), list)
                else int(parse_command(m.group(1).strip(), suppress_print=True) or 0)
            ), s)
        return s

    # Pretty print only for top-level single bar expressions
    if re.fullmatch(r'\|\s*[^|]+\s*\|', cmd):
        inner_cmd = cmd[1:-1].strip()
        inner_result = parse_command(inner_cmd, suppress_print=True)
        if isinstance(inner_result, list):
            if not suppress_print:
                print(f"{inner_cmd} = {','.join(inner_result)}")
                print(len(inner_result))
            return str(len(inner_result))
        elif isinstance(inner_result, str) and inner_result.isdigit():
            if not suppress_print:
                print(f"{inner_cmd} = {inner_result}")
                print(inner_result)
            return inner_result
        else:
            if not suppress_print:
                print(f"{inner_cmd} = 0")
                print('0')
            return '0'

    replaced = eval_bars(cmd)
    parts = replaced.split()
    if len(parts) >= 1:
        if len(parts) == 1:
            key = parts[0]
            if key in data:
                if not suppress_print:
                    print(','.join(data[key]))
                return data[key]
            else:
                if not suppress_print:
                    print(key)
                return [key]
        if len(parts) == 2 and parts[1].isdigit():
            key = parts[0]
            if key in data:
                if not suppress_print:
                    print(','.join(data[key]) + ' ' + parts[1])
                return data[key] + [parts[1]]
            else:
                if not suppress_print:
                    print(key + ' ' + parts[1])
                return [key, parts[1]]
        if len(parts) >= 3:
            if parts[-1].isdigit() and len(parts) >= 4 and len(parts) % 2 == 0:
                valid = all(parts[i].lower() == 'concat' or parts[i] == '+' for i in range(1, len(parts)-2, 2))
                if valid:
                    current = parts[0]
                    for i in range(1, len(parts)-2, 2):
                        op = parts[i]
                        next_key = parts[i+1]
                        if isinstance(current, list):
                            left = current
                        else:
                            left = [str(current)] if str(current).isdigit() else data.get(current)
                        right = [str(next_key)] if str(next_key).isdigit() else data.get(next_key)
                        if left is not None and right is not None:
                            if op.lower() == 'concat':
                                current = left + right
                            elif op == '+':
                                current = []
                                seen = set()
                                for x in left + right:
                                    if x not in seen:
                                        current.append(x)
                                        seen.add(x)
                        else:
                            if not suppress_print:
                                print("One of the keys does not exist.")
                            return None
                    if not suppress_print:
                        print(','.join(current) + ' ' + parts[-1])
                    return current + [parts[-1]]
            if len(parts) % 2 == 1: 
                valid = all(parts[i].lower() == 'concat' or parts[i] == '+' for i in range(1, len(parts)-1, 2))
                if valid:
                    current = parts[0]
                    for i in range(1, len(parts), 2):
                        op = parts[i]
                        next_key = parts[i+1]
                        if isinstance(current, list):
                            left = current
                        else:
                            left = [str(current)] if str(current).isdigit() else data.get(current)
                        right = [str(next_key)] if str(next_key).isdigit() else data.get(next_key)
                        if left is not None and right is not None:
                            if op.lower() == 'concat':
                                current = left + right
                            elif op == '+':
                                current = []
                                seen = set()
                                for x in left + right:
                                    if x not in seen:
                                        current.append(x)
                                        seen.add(x)
                        else:
                            if not suppress_print:
                                print("One of the keys does not exist.")
                            return None
                    if not suppress_print:
                        print(','.join(current))
                    return current
    if not suppress_print:
        print("Invalid command.")
    return None

# Command phase
while True:
    cmd = input("Enter command (e.g., A concat B) or 'exit': ")
    if cmd.strip().lower() == 'exit':
        break
    # Allow prefix assignment in command phase
    if cmd.strip().lower().startswith('prefix'):
        eq_idx = cmd.find('=')
        if eq_idx != -1:
            prefix_expr = cmd[eq_idx+1:].strip()
            print(f"Prefix expression set to: {prefix_expr}")
            # Immediately show the prefix answer after setting
            print("prefix = (" + prefix_expr + ")=")
            result = parse_command(prefix_expr, suppress_print=True)
            if isinstance(result, list):
                s = ''.join(result)
                prefixes = ['ε']
                for i in range(1, len(s)+1):
                    prefixes.append(s[:i])
                print(','.join(prefixes))
            else:
                print('ε')
        continue
    # Skip empty commands (don't print "Invalid command.")
    if not cmd.strip():
        continue
    parse_command(cmd)

# After command phase, process prefix if set
if prefix_expr:
    print("prefix = (" + prefix_expr + ")=")
    result = parse_command(prefix_expr, suppress_print=True)
    def flatten(lst):
        for x in lst:
            if isinstance(x, list):
                yield from flatten(x)
            else:
                yield str(x)
    if isinstance(result, list):
        s = ''.join(flatten(result))
        # Debug print to check what s is
        # print(f"DEBUG: s = '{s}'")
        if s.strip():  # Check if s is not just whitespace or empty
            prefixes = ['ε'] + [s[:i] for i in range(1, len(s)+1)]
            print(','.join(prefixes))
        else:
            print('empty')
    else:
        print('empty')