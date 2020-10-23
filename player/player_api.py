def api(data, setup, playlist):
    if data.startswith("returnip"):
        func, ip, port = data.split(',')
        setup['rtIp'] = ip; setup['rtPort'] = int(port)
        return ('returnAddr,{},{}'.format(setup['rtIp'], setup['rtPort']), setup)
        
    elif data.startswith("fullscreen"):
        if '1' in data or 'true' in data or 'True' in data:
            setup['fullscreen'] = True
        else: setup['fullscreen'] = False
        return('fullscreen,{}'.format(setup['fullscreen']), setup)

    elif data.startswith('loop_one'):
        if '1' in data or 'true' in data or 'True' in data:
            setup['loop_one'] = True
        else: setup['loop_one'] = False
        return ('loop_one,{}'.format(setup['loop_one']), setup)

    elif data.startswith('loop'):
        if '1' in data or 'true' in data or 'True' in data:
            setup['loop'] = True
        else: setup['loop'] = False
        return ('loop,{}'.format(setup['loop']), setup)

    elif data.startswith('progress'):
        if '1' in data or 'true' in data or 'True' in data:
            setup['progress'] = True
        else: setup['progress'] = False
        return ('progress,{}'.format(setup['progress']), setup)

    elif data.startswith('endclose'):
        if '1' in data or 'true' in data or 'True' in data:
            setup['endclose'] = True
        else: setup['endclose'] = False
        return ('endclose,{}'.format(setup['endclose']), setup)

    elif data == ("getlist"):
        list = []
        for item in playlist:
            list.append(item['name'].replace("'",""))
        return ('getlist,{}'.format(','.join(list)), setup)

    elif data == ("getlist_full"):
        list = []
        for item in playlist:
            list.append("{}.{}".format(item['name'], item['type']).replace("'",""))
        return ('getlist_full,{}'.format(','.join(list)), setup)

    elif data == ("getaudiolist"):
        list = []
        for item in playlist:
            if item['type'] == 'mp3' or item['type'] == 'wav' or item['type'] == 'flac' or item['type'] == 'aac':
                list.append(item['name'].replace("'",""))
        return ('getaudiolist,{}'.format(','.join(list)), setup)

    elif data == ("getaudiolist_full"):
        list = []
        for item in playlist:
            if item['type'] == 'mp3' or item['type'] == 'wav' or item['type'] == 'flac' or item['type'] == 'aac':
                list.append("{}.{}".format(item['name'], item['type']).replace("'",""))
        return ('getaudiolist_full,{}'.format(','.join(list)), setup)

    elif data == ("getvideolist"):
        list = []
        for item in playlist:
            if item['type'] == 'mp4' or item['type'] == 'mov' or item['type'] == 'wmv' or item['type'] == 'mov' or item['type'] == 'avi' or item['type'] == 'mpeg' or item['type'] == 'asf':
                list.append(item['name'].replace("'",""))
        return ('getvideolist,{}'.format(','.join(list)), setup)

    elif data == ("getvideolist_full"):
        list = []
        for item in playlist:
            if item['type'] == 'mp4' or item['type'] == 'mov' or item['type'] == 'wmv' or item['type'] == 'mov' or item['type'] == 'avi' or item['type'] == 'mpeg' or item['type'] == 'asf':
                list.append("{}.{}".format(item['name'], item['type']).replace("'",""))
        return ('getvideolist_full,{}'.format(','.join(list)), setup)
