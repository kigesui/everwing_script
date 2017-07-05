# reference:
# https://github.com/IPFR33LY/EverwingHax/blob/master/Everwing_data.py

from ast import literal_eval
import json
from requests import post, get
from urllib import request
from p3lzstring import LZString


WM_URL = 'https://wintermute-151001.appspot.com'

POST_HDR = {"Host": "wintermute-151001.appspot.com",
            "User-Agent": "Mozilla/5.0 "
                          "(Windows NT 10.0; WOW64; rv:50.0)"
                          " Gecko/20100101 Firefox/50.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json;charset=utf-8",
            "Connection": "keep-alive"}

SPID = 'schemaPrimativeID'
SPT = 'schemaPrimativeType'


def main():
    print("... Starting ...")
    with open('1.cfg') as config_fp:
        cfg = json.load(config_fp)
        remove_list = cfg
        user_id = cfg["user_id"]
        print("user_id:", user_id)
        upgrade_list = cfg["upgrade_list"]
        # print("upgrade_list:", upgrade_list)
        remove_list = cfg["remove_list"]
        # print("remove_list:", remove_list)

    http_state = http_get_state(user_id)
    user_data = json.loads(http_state)
    state = user_data['state'][11:]

    state_decoded = LZString.decompressFromBase64(str(state))
    state_json_str = literal_eval(str(state_decoded))
    # state_json_str = state_json_str.replace("'", '"')
    state_dict = json.loads(state_json_str)

    with open('statefile_old.json', 'w') as state_fp:
        state_fp.write(json.dumps(state_dict, sort_keys=True, indent=4))

    unlock_all_characters(state_dict)
    upgrade_dragons(state_dict, upgrade_list)
    remove_dragons(state_dict, remove_list)

    with open('statefile_new.json', 'w') as state_fp:
        state_fp.write(json.dumps(state_dict, sort_keys=True, indent=4))

    state_dict_str = json.dumps(json.dumps(state_dict))
    state_encoded = LZString.compressToBase64(state_dict_str)
    user_data['state'] = 'lz-string::' + state_encoded
    user_data['timestamp'] = \
        round(float(get(WM_URL+'/game/time').content), ndigits=0)
    user_data['server_timestamp'] = \
        round(float(get(WM_URL+'/game/time').content), ndigits=0)
    user_data = json.dumps(user_data)
    http_post(user_data, get_token(user_id))

    print("... End ...")
    return


def http_get_state(user_id):
    state = get(WM_URL + '/game/state/everwing/default/' + user_id)
    return state.content


def http_post(user_data, token):
    # user_data = unicode(user_data)
    headers = dict(POST_HDR)
    headers['x-wintermute-session'] = str(token['token'])
    post_data = post(WM_URL+'/game/action', data=user_data, headers=headers)
    print (post_data)
    return


def unlock_all_characters(state_dict):
    instances = dict(state_dict['instances'])
    for hero in instances:
        if instances[hero][SPID].startswith('character:'):
            if instances[hero][SPT] == "Item":
                if instances[hero]['state'] == "locked":
                    state_dict['instances'][hero]['state'] = "idle"
                    print("hero unlocked", instances[hero][SPID])
                elif instances[hero]['state'] == "idle":
                    print("already unlocked", instances[hero][SPID])
                elif instances[hero]['state'] == "equipped":
                    print("already equipped", instances[hero][SPID])
            elif instances[hero][SPT] == "Stat":
                state_dict['instances'][hero]['value'] = \
                    state_dict['instances'][hero]['maximum']
    return


def upgrade_dragons(state_dict, upgrade_list):
    for item in upgrade_list:
        exp_sidekick_id = "sidekick:"+item['id']
        exp_maturity_id = exp_sidekick_id+'_maturity'
        exp_xp_id = exp_sidekick_id+'_xp'
        # exp_zodiac_id = exp_sidekick_id+'_zodiac'
        exp_zodiac_bonus_id = exp_sidekick_id+'_zodiac_bonus'
        print("\nupgrading one", item['name'],
              " ", exp_sidekick_id)
        instances = dict(state_dict['instances'])
        for sidekick in instances:
            if instances[sidekick][SPID] == exp_sidekick_id:
                print("found:", sidekick)
                stats = instances[sidekick]['stats']
                for stat in stats:
                    if instances[stat][SPID] == exp_maturity_id:
                        if instances[stat]['value'] != \
                                instances[stat]['maximum']:
                            upgrade = True
                        else:
                            upgrade = False
                        break
                if upgrade:
                    print("\t upgrading")
                    for stat in stats:
                        if instances[stat][SPID] == exp_maturity_id:
                            state_dict['instances'][stat]['value'] = \
                                state_dict['instances'][stat]['maximum']
                        if instances[stat][SPID] == exp_zodiac_bonus_id:
                            state_dict['instances'][stat]['value'] = \
                                state_dict['instances'][stat]['maximum']
                        if instances[stat][SPID] == exp_xp_id:
                            # state_dict['instances'][stat]['value'] = \
                            #     state_dict['instances'][stat]['maximum']
                            state_dict['instances'][stat]['value'] = 125800
                    break
                else:
                    print("\t already max")
    return state_dict


def remove_dragons(state_dict, remove_list):
    SPID = 'schemaPrimativeID'
    for item in remove_list:
        exp_sidekick_id = "sidekick:"+item['id']
        exp_maturity_id = exp_sidekick_id+'_maturity'
        print("\nremoving all", item['name'],
              " ", exp_sidekick_id)
        instances = dict(state_dict['instances'])
        for sidekick in instances:
            if instances[sidekick][SPID] == exp_sidekick_id:
                print("found:", sidekick)
                stats = instances[sidekick]['stats']
                for stat in stats:
                    if instances[stat][SPID] == exp_maturity_id:
                        if instances[stat]['value'] == 1:
                            print("\t removing")
                            remove = True
                        else:
                            print("\t keeping")
                            remove = False
                if remove is True:
                    for stat in stats:
                        del state_dict['instances'][stat]
                    del state_dict['instances'][sidekick]
    return state_dict


def get_token(user_id):
    req = request.Request(WM_URL + "/game/session/everwing/" + user_id)
    response = request.urlopen(req)
    data = response.read()
    token = literal_eval(str(data))
    token = json.loads(token)
    return token


if __name__ == "__main__":
    main()
