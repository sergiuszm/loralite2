import math

DEBUG = False

# Returns Time on Air of a given packet
# Used to avoid hard calculations by hand
def get_time_on_air(pkt_size, sf=12, bw=125000, p_len=8, crc=1, hd=1, cr=4):
    # symbol duration
    t_symbol = math.pow(2, sf) / bw

    # preamble duration
    t_preamble = (p_len + 4.25) * t_symbol

    # payload size
    # pkt_size = len(packet['payload'].encode('utf8'))

    # low data rate optimization enabled if t_symbol > 16ms
    # read more: https://www.thethingsnetwork.org/forum/t/a-point-to-note-lora-low-data-rate-optimisation-flag/12007
    ldro = 0
    if t_symbol > 0.016:
        ldro = 1

    # numerator and denominator of the time on air formula
    num = 8 * pkt_size - 4 * sf + 28 + 16 * crc - 20 * hd
    den = 4 * (sf - 2 * ldro)
    payload_symbol_count = 8 + max(math.ceil(num / den) * (cr + 4), 0)

    # payload duration
    t_payload = payload_symbol_count * t_symbol

    return t_preamble + t_payload



def convert_joules(E):
    wh = 3600.0
    wh_to_j = 1 / wh
    total_j_to_wh = E * wh_to_j
    mah = total_j_to_wh / Mc_V * 1000

    return total_j_to_wh, mah

SIM_E_86400 = 110.53403
SIM_E_Ed_86400 = [50.86465, 51.44135, 52.01804, 52.59474, 53.17144]
SIM_E_31536000 = 48354.18655
SIM_E_Ed_31536000 = [18621.41382, 18881.61736, 19053.93749, 19270.19933, 19486.46117]
for x in [86400.0, 31536000.0]:
    Size_P_S = 0                        # max payload size of Sync cmd packet                                       [11...15]
    Size_P_D = 0                        # max payload size of Disc cmd packet                                       [19]
    Size_P_Dc = 0                       # max payload size of Dc cmd packet                                         [19]
    Size_P_DR = 0                       # max payload size of D response packet                                     [15]
    Size_P_DcR = 0                      # max payload size of Dc response packet                                    [44]
    ToA_S = 0.0                         # TimeOnAir of Sync cmd                                                     [s]
    ToA_D = 0.0                         # TimeOnAir of Disc cmd                                                     [s]
    ToA_Dc = 0.0                        # TimeOnAir of Data collection cmd                                          [s]
    ToA_DR = 0.0                        # TimeOnAir of Disc response                                                [s]
    ToA_DcR = 0.0                       # TimeOnAir of Data collection response                                     [s]

    if x == 86400.0:
        Size_P_S = 13
        Size_P_D = 19
        Size_P_Dc = 19
        Size_P_DR = 15
        Size_P_DcR = 44
        D_P_D = 2.0
        Dc_P_D = 2.0
    
    if x == 31536000.0:
        Size_P_S = 15
        Size_P_D = 19
        Size_P_Dc = 19
        Size_P_DR = 15
        Size_P_DcR = 47
        D_P_D = 2.05
        Dc_P_D = 2.05

    ToA_S = get_time_on_air(Size_P_S)
    ToA_D = get_time_on_air(Size_P_D)
    ToA_Dc = get_time_on_air(Size_P_Dc)
    ToA_DR = get_time_on_air(Size_P_DR)
    ToA_DcR = get_time_on_air(Size_P_DcR)

    SD = 600                            # delay between cmd packets                                                 [s]
    Tx_A = 0.12                         # current draw in LoRa TX                                                   [A]
    Rx_A = 0.012                        # current draw in LoRa RX                                                   [A]
    Rx_DW = 20                          # response window duration for Disc cmd                                     [s]
    Rx_DcW = 20                         # response window duration for Data collection cmd                          [s]
    BT_Gw = 0.05                        # GW boot time                                                              [s]
    Mc_I_A = 0.0005                     # current draw of MCU while Idle                                            [A]
    Mc_S_A = 0.000001                   # current draw of MCU while Sleeping                                        [A]
    GT = 10                             # Guard Time for receiving cmd at End-Device                                [s]
    BT_Ed = 0.05                        # End-Device boot time                                                      [s]
    E_Id_P = 0                          # position of End-Device Id in the list received from GW                    [0..n]
    R_GT = 0.05                         # Guard Time for sending response from End-Device                           [s]
    ST_Gw = 0.02                        # time it takes to prepare GW for sleep                                     [s]
    ST_Ed = 0.02                        # time it takes to prepare End-Device for sleep                             [s]
    SchT_Gw = 0.02
    SchT_Ed = 0.02
    Mc_V = 5.025                         # MCU supply voltage                                                       [V]
    R_V = 5.025                          # LoRa supply voltage                                                      [V]

    Gw_C_E = 0.0                        # constant energy cost of GW (boot time + sleep prep time)                  [J]
    Gw_C_T = 0.0                        # constant time of GW (boot time + sleep prep time)                         [s]
    Gw_C_T = BT_Gw + ST_Gw
    Gw_C_E = Gw_C_T * Mc_I_A * Mc_V
    E_C_E = 0.0                         # constant energy cost of Ed (boot time + sleep prep time)                  [J]
    E_C_T = 0.0                         # constat time of Ed (boot time + sleep prep time)                          [s]
    E_C_T = BT_Ed + ST_Ed
    E_C_E = E_C_T * Mc_I_A * Mc_V
    Op_T_Ed = 0.0                       # time Ed spends on perform additional operation after receiving cmd        [s]
    E_Op_Ed = 0.0                       # Ed energy cost of additional operation after receiving cmd                [J]

    ## Sync cmd
    Gw_S_E = 0.0                        # energy cost of sending Sync cmd                                           [J]
    Gw_S_E = Gw_C_E + (Mc_I_A * Mc_V + Tx_A * R_V) * ToA_S
    Gw_S_T = 0.0                        # time needed to perform Sync cmd                                           [s]
    Gw_S_T = Gw_C_T + ToA_S

    E_S_E = 0.0                         # energy cost of receiving Sync cmd                                         [J]
    E_S_E = E_C_E + (Mc_I_A * Mc_V + Rx_A * R_V) * (GT / 2)
    E_S_T = 0.0                         # time needed by Ed to receive and process Sync cmd                         [s]
    E_S_T = E_C_T + (GT / 2)


    ## Disc cmd
    Gw_D_E = 0.0                        # energy cost of sending Disc cmd                                           [J]
    Gw_D_E = Gw_C_E + (Mc_I_A * Mc_V + Tx_A * R_V) * (ToA_D + SchT_Gw) + (Mc_I_A * Mc_V + Rx_A * R_V) * Rx_DW
    Gw_D_T = 0.0                        # time needed to perform Disc cmd                                           [s]
    Gw_D_T = Gw_C_T + ToA_D + SchT_Gw + Rx_DW

    E_D_E = 0.0                         # energy const of receiving Disc cmd                                        [J]
    E_D_E = E_C_E + (Mc_I_A * Mc_V + Rx_A * R_V) * (SchT_Ed + GT / 2 + E_Id_P * (ToA_DR + R_GT)) + (Mc_I_A * Mc_V + Tx_A * R_V) * ToA_DR
    E_D_T = 0.0                         # time needed by Ed to receive and respond to Disc cmd                      [s]
    E_D_T = E_C_T + (SchT_Ed + GT / 2 + E_Id_P * (ToA_DR + R_GT)) + ToA_DR

    ## Dc cmd
    Gw_Dc_E = 0.0                       # energy cost of sending DC cmd                                             [J]
    Gw_Dc_E = Gw_C_E + (Mc_I_A * Mc_V + Tx_A * R_V) * (ToA_Dc + SchT_Gw) + (Mc_I_A * Mc_V + Rx_A * R_V) * Rx_DcW
    Gw_Dc_T = 0.0                       # time needed to perform DC cmd                                             [s]
    Gw_Dc_T = Gw_C_T + ToA_Dc + SchT_Gw + Rx_DcW

    E_Dc_E = 0.0                        # energy const of receiving DC cmd                                          [J]
    E_Dc_E = E_C_E + (Mc_I_A * Mc_V + Rx_A * R_V) * (SchT_Ed + GT / 2 + E_Id_P * (ToA_DcR + R_GT)) + (Mc_I_A * Mc_V + Tx_A * R_V) * ToA_DcR
    E_Dc_T = 0.0                        # time needed by Ed to receive and respond to DC cmd                        [s]
    E_Dc_T = E_C_T + (SchT_Ed + GT / 2 + E_Id_P * (ToA_DcR + R_GT)) + ToA_DcR

    O_D = x
    P_D = 600.0

    Nr_Days = O_D / 86400.0
    Nr_P = int(O_D / P_D)
    Nr_Ed = 5
    Ed_ids = [1, 2, 3, 4, 5]

    Rx_DW_All = Nr_Ed * (ToA_DR + R_GT)
    D_P_D_total = math.ceil(float(Rx_DW_All) / float(Rx_DW)) * D_P_D * Nr_Days

    Rx_DcW_All = Nr_Ed * (ToA_DcR + R_GT)
    Dc_P_D_total = math.ceil(float(Rx_DcW_All) / float(Rx_DcW)) * Dc_P_D * Nr_Days

    Nr_Sync_Gw = Nr_P - (D_P_D_total + Dc_P_D_total)
    Nr_Sync_Ed = Nr_P - (D_P_D * Nr_Days + Dc_P_D * Nr_Days)

    T_Cmd_Gw = Nr_Sync_Gw * Gw_S_T + D_P_D_total * Gw_D_T + Dc_P_D_total * Gw_Dc_T
    T_Sleep_Gw = O_D - T_Cmd_Gw

    Gw_Rx_T = Rx_DW * D_P_D_total + Rx_DcW * Dc_P_D_total
    Gw_Tx_T = ToA_S * Nr_Sync_Gw + (ToA_D + SchT_Gw) * D_P_D_total + (ToA_Dc + SchT_Gw) * D_P_D_total

    E_Gw = Nr_Sync_Gw * Gw_S_E + D_P_D_total * Gw_D_E + Dc_P_D_total * Gw_Dc_E + T_Sleep_Gw * Mc_S_A * Mc_V
    wh, mah = convert_joules(E_Gw)
    print(f'[{"MODEL":5}][{x:13,}s] GW ENERGY USED: {E_Gw:.5f}J => {wh:.5f}Wh '
            f'=> {mah:.5f}mAh @ {Mc_V}V'
    )
    if DEBUG:
        total = 0.0
        j = T_Sleep_Gw * Mc_S_A * Mc_V
        total += j
        print(f'\t[DEVICE][state][SLEEP]        : {j:.5f}J, {T_Sleep_Gw}s / {x}s')
        j = T_Cmd_Gw * Mc_I_A * Mc_V
        total += j
        print(f'\t[DEVICE][state][ON]           : {j:.5f}J, {T_Cmd_Gw}s / {x}s')
        j = Gw_Rx_T * Rx_A * R_V
        total += j
        print(f'\t[RADIO][radio_substate][RX]   : {j:.5f}J, {Gw_Rx_T}s / {x}s')
        j = Gw_Tx_T * Tx_A * R_V
        total += j
        print(f'\t[RADIO][radio_substate][TX]   : {j:.5f}J, {Gw_Tx_T}s / {x}s')
        print(f'\t{"TOTAL":30}: {total:.5f}J')
    Sim_E_Gw = globals()[f'SIM_E_{int(x)}']
    wh, mah = convert_joules(Sim_E_Gw)
    diff = (1 - (E_Gw / Sim_E_Gw)) * 100
    sign = '-'
    if diff < 0:
        sign = '+'
    diff = abs(diff)
    print(f'[{"SIM":5}][{x:13,}s] GW ENERGY USED: {Sim_E_Gw:.5f}J => {wh:.5f}Wh '
            f'=> {mah:.5f}mAh @ {Mc_V}V | MODEL[{sign}{diff:.2f}%]'
    )
    for e_id in Ed_ids:
        E_D_E = E_C_E + (Mc_I_A * Mc_V + Rx_A * R_V) * (SchT_Ed + GT / 2 + Ed_ids.index(e_id) * (ToA_DR + R_GT)) + (Mc_I_A * Mc_V + Tx_A * R_V) * ToA_DR
        E_D_T = E_C_T + (SchT_Ed + GT / 2 + Ed_ids.index(e_id) * (ToA_DR + R_GT)) + ToA_DR
        E_Dc_E = E_C_E + (Mc_I_A * Mc_V + Rx_A * R_V) * (SchT_Ed + GT / 2 + Ed_ids.index(e_id) * (ToA_DcR + R_GT)) + (Mc_I_A * Mc_V + Tx_A * R_V) * ToA_DcR
        E_Dc_T = E_C_T + (SchT_Ed + GT / 2 + Ed_ids.index(e_id) * (ToA_DcR + R_GT)) + ToA_DcR
        
        E_Rx_T = (GT / 2) * Nr_Sync_Ed + (SchT_Ed + GT / 2 + Ed_ids.index(e_id) * (ToA_DR + R_GT)) * (D_P_D * Nr_Days) + (SchT_Ed + GT / 2 + Ed_ids.index(e_id) * (ToA_DcR + R_GT)) * (Dc_P_D * Nr_Days)
        E_Tx_T = ToA_DcR * (Dc_P_D * Nr_Days) + ToA_DR * (D_P_D * Nr_Days)

        T_Cmd_Ed = Nr_Sync_Ed * E_S_T + (D_P_D * Nr_Days) * E_D_T + (Dc_P_D * Nr_Days) * E_Dc_T
        T_Sleep_Ed = O_D - T_Cmd_Ed
        E_Ed = Nr_Sync_Ed * E_S_E + (D_P_D * Nr_Days) * E_D_E + (Dc_P_D * Nr_Days) * E_Dc_E + T_Sleep_Ed * Mc_S_A * Mc_V
        wh, mah = convert_joules(E_Ed)
        print(f'[{"MODEL":5}][{x:13,}s] dev_{e_id} ENERGY USED: {E_Ed:.5f}J => {wh:.5f}Wh '
                f'=> {mah:.5f}mAh @ {Mc_V}V'
        )
        if DEBUG:
            total = 0
            j = T_Sleep_Ed * Mc_S_A * Mc_V
            total += j
            print(f'\t[DEVICE][state][SLEEP]        : {j:.5f}J, {T_Sleep_Ed}s / {x}s')
            j = T_Cmd_Ed * Mc_I_A * Mc_V
            total += j
            print(f'\t[DEVICE][state][ON]           : {j:.5f}J, {T_Cmd_Ed}s / {x}s')
            j = E_Rx_T * Rx_A * R_V
            total += j
            print(f'\t[RADIO][radio_substate][RX]   : {j:.5f}J, {E_Rx_T}s / {x}s')
            j = E_Tx_T * Tx_A * R_V
            total += j
            print(f'\t[RADIO][radio_substate][TX]   : {j:.5f}J, {E_Tx_T}s / {x}s')
            print(f'\t{"TOTAL":30}: {total:.5f}J')
        Sim_E_Ed = globals()[f'SIM_E_Ed_{int(x)}'][Ed_ids.index(e_id)]
        wh, mah = convert_joules(Sim_E_Ed)
        diff = (1 - (E_Ed / Sim_E_Ed)) * 100
        sign = '-'
        if diff < 0:
            sign = '+'
        diff = abs(diff)
        print(f'[{"SIM":5}][{x:13,}s] dev_{e_id} ENERGY USED: {Sim_E_Ed:.5f}J => {wh:.5f}Wh '
                f'=> {mah:.5f}mAh @ {Mc_V}V | Diff MODEL[{sign}{diff:.2f}%]'
        )
    print('\n')