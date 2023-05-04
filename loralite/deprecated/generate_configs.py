import json

if __name__ == '__main__':
    # parser = argparse.ArgumentParser('LoRa scenario simulator for DAO')
    # parser.add_argument('config', help='Specify config file for the simulator')
    # args = parser.parse_args()

    radio_types = ['sx1262', 'sx1276']

    with open(f'configs/default.json', 'r') as f:
        config = json.load(f)

    count = 1
    for radio_type in radio_types:

        for send_interval in range(600, 3601, 600):
            for disc_every_n in range(25, 101, 25):
                print(f'[{str(count):2}][{radio_type}] {send_interval} {disc_every_n}')
                count += 1
                
                config['general']['number_of_devices'] = 8 + 1
                config['wcm']['disc_window_s'] = 5
                config['wcm']['dc_window_s'] = 5
                config['wcm']['send_interval_s'] = send_interval
                config['wcm']['disc_every_n_cmd'] = disc_every_n
                config['wcm']['radio_type'] = radio_type
                config['wcl']['radio_type'] = radio_type

                with open(f'configs/experiments/{radio_type}_{send_interval}_{disc_every_n}.json', 'w') as outfile:
                    
                    outfile.write(json.dumps(config, indent=4))

        # #devices 4-20, by 4
        # #disc window (5, 10, 15, 20)
        # #data collection window (5, 10, 15, 20)
        # for nd in range(4, 24, 4):
        #     for disc_w in range(5, 25, 5):
        #         for dc_w in range(5, 25, 5):
        #             print(f'[{count}][{radio_type}] {nd} {disc_w} {dc_w}')
        #             count += 1
                    
        #             config['general']['number_of_devices'] = nd + 1
        #             config['wcm']['disc_window_s'] = disc_w
        #             config['wcm']['dc_window_s'] = dc_w
        #             config['wcm']['radio_type'] = radio_type
        #             config['wcl']['radio_type'] = radio_type

        #             with open(f'configs/experiments/{radio_type}_{nd}_{disc_w}_{dc_w}_{}.json', 'w') as outfile:
                        
        #                 outfile.write(json.dumps(config, indent=4))




