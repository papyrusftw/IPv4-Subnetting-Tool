import math

def IPtoINT(ip):
    parts = ip.split('.')
    return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])
def INTtoIP(num):
    return f"{(num >> 24) & 255}.{(num >> 16) & 255}.{(num >> 8) & 255}.{num & 255}"
def GetNetworkInfo():
    print("=" * 60)
    print("IPv4 SUBNETTING CALCULATOR")
    print("=" * 60)
    while True:
        try:
            network = input("\nEnter the base network address (e.g., 192.168.1.0/24): ")
            IPpart, CIDRpart = network.split('/')
            cidr = int(CIDRpart)
            if cidr < 0 or cidr > 32:
                print("CIDR must be between 0 and 32")
                continue
            IPparts = IPpart.split('.')
            if len(IPparts) != 4:
                print("Invalid IP address format")
                continue
            for part in IPparts:
                if int(part) < 0 or int(part) > 255:
                    print("IP parts must be between 0 and 255")
                    raise ValueError
            ipint = IPtoINT(IPpart)
            mask = ((1 << 32) - 1) << (32 - cidr)
            NetworkInt = ipint & mask
            return {
                'address': INTtoIP(NetworkInt),
                'cidr': cidr,
                'NetworkInt': NetworkInt,
                'mask': mask,
                'BroadcastInt': NetworkInt + (1 << (32 - cidr)) - 1}
        except ValueError:
            print("Invalid input. Please use format: x.x.x.x/xx")
        except Exception as e:
            print(f"Error: {e}")

def GetSegmentUsers():
    segments = []
    print("\n" + "=" * 60)
    print("ENTER SEGMENT REQUIREMENTS")
    print("=" * 60)
    print("Enter the number of users for each segment (enter 0 to finish):")
    segmentcount = 1
    while True:
        try:
            users = int(input(f"Segment {segmentcount} users: "))
            if users == 0:
                if segmentcount == 1:
                    print("You need at least one segment. Please enter a valid number.")
                    continue
                break
            if users < 1:
                print("Number of users must be positive. Please try again.")
                continue
            if users > 65534:
                print("Too many users. Maximum is 65534 per segment.")
                continue
            segments.append(users)
            segmentcount += 1
        except ValueError:
            print("Invalid input. Please enter a number.")
    return segments

def CalcSubnetInfo(users):
    TotalNeeded = users + 2
    SubnetSize = 1
    while SubnetSize < TotalNeeded:
        SubnetSize *= 2
    HostsBits = int(math.log2(SubnetSize))
    cidr = 32 - HostsBits
    if users == 2 and cidr != 30:
        cidr = 30
        SubnetSize = 4
    mask = ((1 << 32) - 1) << (32 - cidr)
    MaskOctets = [
        (mask >> 24) & 255,
        (mask >> 16) & 255,
        (mask >> 8) & 255,
        mask & 255]
    maskstr = f"{MaskOctets[0]}.{MaskOctets[1]}.{MaskOctets[2]}.{MaskOctets[3]}"
    return {
        'size': SubnetSize,
        'cidr': cidr,
        'mask': mask,
        'maskstr': maskstr,
        'usable': SubnetSize - 2}

def AllocateSubnets(BaseNetwork, segments):
    SegsWithIndexes = [(i, users) for i, users in enumerate(segments)]
    SegsSorted = sorted(SegsWithIndexes, key=lambda x: x[1], reverse=True)
    
    subnets = []
    currentip = BaseNetwork['NetworkInt']
    maxip = BaseNetwork['BroadcastInt']
    
    for OgIndex, users in SegsSorted:
        SubnetInfo = CalcSubnetInfo(users)
        if users <= 2 and SubnetInfo['size'] < 4:
            SubnetInfo['size'] = 4
            SubnetInfo['cidr'] = 30
            SubnetInfo['usable'] = 2
        if currentip + SubnetInfo['size'] - 1 > maxip:
            print(f"\nERROR: Not enough IP space for segment with {users} users!")
            print(f"Need {SubnetInfo['size']} IPs but only {(maxip - currentip + 1)} remaining")
            return None
        NetworkInt = currentip
        BroadcastInt = currentip + SubnetInfo['size'] - 1
        FirstUsable = NetworkInt + 1 if SubnetInfo['size'] > 2 else None
        LastUsable = BroadcastInt - 1 if SubnetInfo['size'] > 2 else None
        subnets.append({
            'OgIndex': OgIndex,
            'users': users,
            'NetworkInt': NetworkInt,
            'network': INTtoIP(NetworkInt),
            'BroadcastInt': BroadcastInt,
            'broadcast': INTtoIP(BroadcastInt),
            'cidr': SubnetInfo['cidr'],
            'mask': SubnetInfo['maskstr'],
            'size': SubnetInfo['size'],
            'usable': SubnetInfo['usable'],
            'FirstUsable': INTtoIP(FirstUsable) if FirstUsable else "N/A",
            'LastUsable': INTtoIP(LastUsable) if LastUsable else "N/A"})
        currentip += SubnetInfo['size']
    return subnets
def DisplayResults(BaseNetwork, subnets):
    if not subnets:
        return
    subnets.sort(key=lambda x: x['OgIndex'])
    print("\n" + "=" * 100)
    print("SUBNETTING RESULTS")
    print("=" * 100)
    print(f"Base Network: {BaseNetwork['address']}/{BaseNetwork['cidr']}")
    print(f"Total IPs available: {BaseNetwork['BroadcastInt'] - BaseNetwork['NetworkInt'] + 1}")
    print("-" * 100)
    print(f"{'Seg':<4} {'Users':<6} {'Network':<16} {'Mask':<16} "
          f"{'Broadcast':<16} {'Usable Range':<25} {'Size':<8}")
    print("-" * 100)
    UsedIPsCount = 0
    UsableCount = 0
    for i, subnet in enumerate(subnets, 1):
        range_str = f"{subnet['FirstUsable']} - {subnet['LastUsable']}" if subnet['usable'] > 0 else "No usable IPs"
        print(f"{i:<4} {subnet['users']:<6} {subnet['network'] + '/' + str(subnet['cidr']):<16} "
              f"{subnet['mask']:<16} {subnet['broadcast']:<16} "
              f"{range_str:<25} /{subnet['cidr']:<6}")
        UsedIPsCount += subnet['size']
        UsableCount += subnet['usable']

def Main():
    print("Welcome to the IPv4 Subnetting Calculator!")
    print("This tool will help you create subnets based on user requirements.")
    while True:
        BaseNetwork = GetNetworkInfo()
        segments = GetSegmentUsers()
        if not segments:
            print("No segments specified. Exiting...")
            break
        subnets = AllocateSubnets(BaseNetwork, segments)
        if subnets:
            DisplayResults(BaseNetwork, subnets)
        else:
            print("\nFailed to allocate subnets. Please try with a larger base network.")
        another = input("\nPerform another calculation? (y/n): ").lower()
        if another != 'y':
            break
Main()