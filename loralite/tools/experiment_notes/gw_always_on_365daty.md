# Energy usage over a year for a GW always on with radio always in RX mode

MCU current draw: 0.5mA

## SX1262 

TOTAL ENERGY USED @ 5.025V: 
- 758529.10080J
- 227.55873Wh
- 45285.31945mAh => 45.32Ah

## SX1276

TOTAL ENERGY USED @ 5.025V:
- 1975336.2J
- 592.60086Wh
- 117930.51940mAh => 117.93Ah

## iC880a 4 modulation paths - medium activity

TOTAL ENERGY USED @ 5.025V:
- 45590759.496J
- 13677.22785Wh
- 2721836.38782mAh

## iC880a 10 modulation paths - high activity

TOTAL ENERGY USED @ 5.025V:
- 67714524.936J
- 20314.35748Wh
- 4042658.20513mAh


# Energy usage over a year for GW sending SYNC every 10m

## SX1262

Stats for dev_0 [GW]
[Packets sent]      : 52560
[Bytes sent]        : 777,290
[Packets received]  : 0
[Bytes received]    : 0

Stats for dev_1 [END_DEV]
[Packets sent]      : 0
[Bytes sent]        : 0
[Packets received]  : 52560
[Bytes received]    : 777,290

Energy usage for dev_0
[DEVICE][state][SLEEP]        : 158.06826J, 31456370.8s / 31536000.0s
[DEVICE][state][ON]           : 199.51096J, 79629.2s / 31536000.0s
[RADIO][radio_substate][TX]   : 45733.46476J, 76055.12s / 31536000.0s
TOTAL ENERGY USED: 46091.04398J => 13.82731Wh => 2751.70412mAh @ 5.025V

Energy usage for dev_1
[DEVICE][state][SLEEP]        : 157.01023J, 31245816.29s / 31536000.0s
[DEVICE][state][ON]           : 727.05529J, 290183.71s / 31536000.0s
[RADIO][radio_substate][RX]   : 6194.91660J, 287503.149s / 31536000.0s
TOTAL ENERGY USED: 7078.98211J => 2.12369Wh => 422.62580mAh @ 5.025V

## SX1276

Stats for dev_0 [GW]
Packets sent]      : 52560
Bytes sent]        : 777,290
Packets received]  : 0
Bytes received]    : 0

Stats for dev_1 [END_DEV]
Packets sent]      : 0
Bytes sent]        : 0
Packets received]  : 52560
Bytes received]    : 777,290

Energy usage for dev_0
DEVICE][state][SLEEP]        : 158.06826J, 31456370.8s / 31536000.0s
DEVICE][state][ON]           : 199.51096J, 79629.2s / 31536000.0s
RADIO][radio_substate][TX]   : 45733.46476J, 76055.12s / 31536000.0s
TOTAL ENERGY USED: 46091.04398J => 13.82731Wh => 2751.70412mAh @ 5.025V

Energy usage for dev_1
DEVICE][state][SLEEP]        : 157.01023J, 31245816.29s / 31536000.0s
DEVICE][state][ON]           : 727.05529J, 290183.71s / 31536000.0s
RADIO][radio_substate][RX]   : 17288.13936J, 287503.149s / 31536000.0s
TOTAL ENERGY USED: 18172.20487J => 5.45166Wh => 1084.90775mAh @ 5.025V

# Energy usage over a year for GW and end-device(s)

## SX1262

### GW always on in RX

Stats for dev_0 [GW]
[Packets sent]      : 0
[Bytes sent]        : 0
[Packets received]  : 2100
[Bytes received]    : 68,190

Stats for dev_1 [END_DEV]
[Packets sent]      : 2100
[Bytes sent]        : 68,190
[Packets received]  : 0
[Bytes received]    : 0

Energy usage for dev_0
[DEVICE][state][SLEEP]        : 0.00000J, 0.001s / 31536000.0s
[DEVICE][state][ON]           : 79013.44800J, 31535999.999s / 31536000.0s
[RADIO][radio_substate][RX]   : 679515.65276J, 31535999.998s / 31536000.0s
TOTAL ENERGY USED: 758529.10075J => 227.55873Wh => 45285.31945mAh @ 5.025V

Energy usage for dev_1
[DEVICE][state][SLEEP]        : 158.44406J, 31531155.348s / 31536000.0s
[DEVICE][state][ON]           : 12.13828J, 4844.652s / 31536000.0s
[RADIO][radio_substate][TX]   : 2827.34651J, 4701.9s / 31536000.0s
TOTAL ENERGY USED: 2997.92884J => 0.89938Wh => 178.98083mAh @ 5.025V

### Discovery every 100 cmd, Data collection after, 2 retransmissions per DISC/DC

Stats for dev_0 [GW]
[Packets sent]      : 52560
[Bytes sent]        : 785,690
[Packets received]  : 18350
[Bytes received]    : 598,010

Stats for dev_1 [END_DEV]
[Packets sent]      : 2100
[Bytes sent]        : 67,140
[Packets received]  : 52560
[Bytes received]    : 785,690

Stats for dev_2 [END_DEV]
[Packets sent]      : 2100
[Bytes sent]        : 68,190
[Packets received]  : 52560
[Bytes received]    : 785,690

Stats for dev_3 [END_DEV]
[Packets sent]      : 2100
[Bytes sent]        : 67,140
[Packets received]  : 52560
[Bytes received]    : 785,690

Stats for dev_4 [END_DEV]
[Packets sent]      : 2100
[Bytes sent]        : 67,140
[Packets received]  : 52560
[Bytes received]    : 785,690

Stats for dev_5 [END_DEV]
[Packets sent]      : 2100
[Bytes sent]        : 67,140
[Packets received]  : 52560
[Bytes received]    : 785,690

Stats for dev_6 [END_DEV]
[Packets sent]      : 2100
[Bytes sent]        : 68,190
[Packets received]  : 52560
[Bytes received]    : 785,690

Stats for dev_7 [END_DEV]
[Packets sent]      : 2100
[Bytes sent]        : 68,190
[Packets received]  : 52560
[Bytes received]    : 785,690

Stats for dev_8 [END_DEV]
[Packets sent]      : 2100
[Bytes sent]        : 68,190
[Packets received]  : 52560
[Bytes received]    : 785,690

Stats for dev_9 [END_DEV]
[Packets sent]      : 2100
[Bytes sent]        : 67,140
[Packets received]  : 52560
[Bytes received]    : 785,690

Energy usage for dev_0
[DEVICE][state][SLEEP]        : 157.69848J, 31382782.102s / 31536000.0s
[DEVICE][state][ON]           : 383.88744J, 153217.898s / 31536000.0s
[RADIO][radio_substate][RX]   : 1583.72655J, 73500.0s / 31536000.0s
[RADIO][radio_substate][TX]   : 45777.96124J, 76129.118s / 31536000.0s
TOTAL ENERGY USED: 47903.27371J => 14.37098Wh => 2859.89694mAh @ 5.025V

Energy usage for dev_1
[DEVICE][state][SLEEP]        : 156.99179J, 31242146.54s / 31536000.0s
[DEVICE][state][ON]           : 736.24984J, 293853.46s / 31536000.0s
[RADIO][radio_substate][RX]   : 6171.83944J, 286432.149s / 31536000.0s
[RADIO][radio_substate][TX]   : 2850.70779J, 4740.75s / 31536000.0s
TOTAL ENERGY USED: 9915.78886J => 2.97474Wh => 591.98739mAh @ 5.025V

Energy usage for dev_2
[DEVICE][state][SLEEP]        : 156.96611J, 31237036.69s / 31536000.0s
[DEVICE][state][ON]           : 749.05257J, 298963.31s / 31536000.0s
[RADIO][radio_substate][RX]   : 6278.82610J, 291397.349s / 31536000.0s
[RADIO][radio_substate][TX]   : 2937.68873J, 4885.4s / 31536000.0s
TOTAL ENERGY USED: 10122.53351J => 3.03676Wh => 604.33036mAh @ 5.025V

Energy usage for dev_3
[DEVICE][state][SLEEP]        : 156.97586J, 31238977.64s / 31536000.0s
[DEVICE][state][ON]           : 744.18952J, 297022.36s / 31536000.0s
[RADIO][radio_substate][RX]   : 6240.12068J, 289601.049s / 31536000.0s
[RADIO][radio_substate][TX]   : 2850.70779J, 4740.75s / 31536000.0s
TOTAL ENERGY USED: 9991.99386J => 2.99760Wh => 596.53695mAh @ 5.025V

Energy usage for dev_4
[DEVICE][state][SLEEP]        : 156.95164J, 31234157.09s / 31536000.0s
[DEVICE][state][ON]           : 756.26741J, 301842.91s / 31536000.0s
[RADIO][radio_substate][RX]   : 6343.99052J, 294421.599s / 31536000.0s
[RADIO][radio_substate][TX]   : 2850.70779J, 4740.75s / 31536000.0s
TOTAL ENERGY USED: 10107.91736J => 3.03238Wh => 603.45775mAh @ 5.025V

Energy usage for dev_5
[DEVICE][state][SLEEP]        : 156.95994J, 31235808.74s / 31536000.0s
[DEVICE][state][ON]           : 752.12920J, 300191.26s / 31536000.0s
[RADIO][radio_substate][RX]   : 6308.40192J, 292769.949s / 31536000.0s
[RADIO][radio_substate][TX]   : 2850.70779J, 4740.75s / 31536000.0s
TOTAL ENERGY USED: 10068.19885J => 3.02046Wh => 601.08650mAh @ 5.025V

Energy usage for dev_6
[DEVICE][state][SLEEP]        : 156.93135J, 31230120.29s / 31536000.0s
[DEVICE][state][ON]           : 766.38161J, 305879.71s / 31536000.0s
[RADIO][radio_substate][RX]   : 6427.85584J, 298313.749s / 31536000.0s
[RADIO][radio_substate][TX]   : 2937.68873J, 4885.4s / 31536000.0s
TOTAL ENERGY USED: 10288.85754J => 3.08666Wh => 614.26015mAh @ 5.025V

Energy usage for dev_7
[DEVICE][state][SLEEP]        : 156.99106J, 31242001.89s / 31536000.0s
[DEVICE][state][ON]           : 736.61226J, 293998.11s / 31536000.0s
[RADIO][radio_substate][RX]   : 6171.83944J, 286432.149s / 31536000.0s
[RADIO][radio_substate][TX]   : 2937.68873J, 4885.4s / 31536000.0s
TOTAL ENERGY USED: 10003.13150J => 3.00094Wh => 597.20188mAh @ 5.025V

Energy usage for dev_8
[DEVICE][state][SLEEP]        : 156.96611J, 31237036.69s / 31536000.0s
[DEVICE][state][ON]           : 749.05257J, 298963.31s / 31536000.0s
[RADIO][radio_substate][RX]   : 6278.82610J, 291397.349s / 31536000.0s
[RADIO][radio_substate][TX]   : 2937.68873J, 4885.4s / 31536000.0s
TOTAL ENERGY USED: 10122.53351J => 3.03676Wh => 604.33036mAh @ 5.025V

Energy usage for dev_9
[DEVICE][state][SLEEP]        : 156.97586J, 31238977.64s / 31536000.0s
[DEVICE][state][ON]           : 744.18952J, 297022.36s / 31536000.0s
[RADIO][radio_substate][RX]   : 6240.12068J, 289601.049s / 31536000.0s
[RADIO][radio_substate][TX]   : 2850.70779J, 4740.75s / 31536000.0s
TOTAL ENERGY USED: 9991.99386J => 2.99760Wh => 596.53695mAh @ 5.025V


## SX1276

### GW always on in RX

Stats for dev_0 [GW]
[Packets sent]      : 0
[Bytes sent]        : 0
[Packets received]  : 2100
[Bytes received]    : 68,190

Stats for dev_1 [END_DEV]
[Packets sent]      : 2100
[Bytes sent]        : 68,190
[Packets received]  : 0
[Bytes received]    : 0

Energy usage for dev_0
[DEVICE][state][SLEEP]        : 0.00000J, 0.001s / 31536000.0s
[DEVICE][state][ON]           : 79013.44800J, 31535999.999s / 31536000.0s
[RADIO][radio_substate][RX]   : 1896322.75188J, 31535999.998s / 31536000.0s
TOTAL ENERGY USED: 1975336.19988J => 592.60086Wh => 117930.51940mAh @ 5.025V

Energy usage for dev_1
[DEVICE][state][SLEEP]        : 158.44406J, 31531155.348s / 31536000.0s
[DEVICE][state][ON]           : 12.13828J, 4844.652s / 31536000.0s
[RADIO][radio_substate][TX]   : 2827.34651J, 4701.9s / 31536000.0s
TOTAL ENERGY USED: 2997.92884J => 0.89938Wh => 178.98083mAh @ 5.025V

### Discovery every 100 cmd, Data collection after, 2 retransmissions per DISC/DC

Stats for dev_0 [GW]
[Packets sent]      : 52560
[Bytes sent]        : 785,690
[Packets received]  : 18350
[Bytes received]    : 598,010

Stats for dev_1 [END_DEV]
[Packets sent]      : 2100
[Bytes sent]        : 67,140
[Packets received]  : 52560
[Bytes received]    : 785,690

Stats for dev_2 [END_DEV]
[Packets sent]      : 2100
[Bytes sent]        : 68,190
[Packets received]  : 52560
[Bytes received]    : 785,690

Stats for dev_3 [END_DEV]
[Packets sent]      : 2100
[Bytes sent]        : 67,140
[Packets received]  : 52560
[Bytes received]    : 785,690

Stats for dev_4 [END_DEV]
[Packets sent]      : 2100
[Bytes sent]        : 67,140
[Packets received]  : 52560
[Bytes received]    : 785,690

Stats for dev_5 [END_DEV]
[Packets sent]      : 2100
[Bytes sent]        : 67,140
[Packets received]  : 52560
[Bytes received]    : 785,690

Stats for dev_6 [END_DEV]
[Packets sent]      : 2100
[Bytes sent]        : 68,190
[Packets received]  : 52560
[Bytes received]    : 785,690

Stats for dev_7 [END_DEV]
[Packets sent]      : 2100
[Bytes sent]        : 68,190
[Packets received]  : 52560
[Bytes received]    : 785,690

Stats for dev_8 [END_DEV]
[Packets sent]      : 2100
[Bytes sent]        : 68,190
[Packets received]  : 52560
[Bytes received]    : 785,690

Stats for dev_9 [END_DEV]
[Packets sent]      : 2100
[Bytes sent]        : 67,140
[Packets received]  : 52560
[Bytes received]    : 785,690

Energy usage for dev_0
[DEVICE][state][SLEEP]        : 157.69848J, 31382782.102s / 31536000.0s
[DEVICE][state][ON]           : 383.88744J, 153217.898s / 31536000.0s
[RADIO][radio_substate][RX]   : 4419.70200J, 73500.0s / 31536000.0s
[RADIO][radio_substate][TX]   : 45777.96124J, 76129.118s / 31536000.0s
TOTAL ENERGY USED: 50739.24916J => 15.22177Wh => 3029.20891mAh @ 5.025V

Energy usage for dev_1
[DEVICE][state][SLEEP]        : 156.99179J, 31242146.54s / 31536000.0s
[DEVICE][state][ON]           : 736.24984J, 293853.46s / 31536000.0s
[RADIO][radio_substate][RX]   : 17223.73798J, 286432.149s / 31536000.0s
[RADIO][radio_substate][TX]   : 2850.70779J, 4740.75s / 31536000.0s
TOTAL ENERGY USED: 20967.68740J => 6.29031Wh => 1251.80223mAh @ 5.025V

Energy usage for dev_2
[DEVICE][state][SLEEP]        : 156.96611J, 31237036.69s / 31536000.0s
[DEVICE][state][ON]           : 749.05257J, 298963.31s / 31536000.0s
[RADIO][radio_substate][RX]   : 17522.30539J, 291397.349s / 31536000.0s
[RADIO][radio_substate][TX]   : 2937.68873J, 4885.4s / 31536000.0s
TOTAL ENERGY USED: 21366.01280J => 6.40980Wh => 1275.58285mAh @ 5.025V

Energy usage for dev_3
[DEVICE][state][SLEEP]        : 156.97586J, 31238977.64s / 31536000.0s
[DEVICE][state][ON]           : 744.18952J, 297022.36s / 31536000.0s
[RADIO][radio_substate][RX]   : 17414.29028J, 289601.049s / 31536000.0s
[RADIO][radio_substate][TX]   : 2850.70779J, 4740.75s / 31536000.0s
TOTAL ENERGY USED: 21166.16345J => 6.34985Wh => 1263.65155mAh @ 5.025V

Energy usage for dev_4
[DEVICE][state][SLEEP]        : 156.95164J, 31234157.09s / 31536000.0s
[DEVICE][state][ON]           : 756.26741J, 301842.91s / 31536000.0s
[RADIO][radio_substate][RX]   : 17704.15959J, 294421.599s / 31536000.0s
[RADIO][radio_substate][TX]   : 2850.70779J, 4740.75s / 31536000.0s
TOTAL ENERGY USED: 21468.08643J => 6.44043Wh => 1281.67680mAh @ 5.025V

Energy usage for dev_5
[DEVICE][state][SLEEP]        : 156.95994J, 31235808.74s / 31536000.0s
[DEVICE][state][ON]           : 752.12920J, 300191.26s / 31536000.0s
[RADIO][radio_substate][RX]   : 17604.84257J, 292769.949s / 31536000.0s
[RADIO][radio_substate][TX]   : 2850.70779J, 4740.75s / 31536000.0s
TOTAL ENERGY USED: 21364.63950J => 6.40939Wh => 1275.50087mAh @ 5.025V

Energy usage for dev_6
[DEVICE][state][SLEEP]        : 156.93135J, 31230120.29s / 31536000.0s
[DEVICE][state][ON]           : 766.38161J, 305879.71s / 31536000.0s
[RADIO][radio_substate][RX]   : 17938.20235J, 298313.749s / 31536000.0s
[RADIO][radio_substate][TX]   : 2937.68873J, 4885.4s / 31536000.0s
TOTAL ENERGY USED: 21799.20405J => 6.53976Wh => 1301.44502mAh @ 5.025V

Energy usage for dev_7
[DEVICE][state][SLEEP]        : 156.99106J, 31242001.89s / 31536000.0s
[DEVICE][state][ON]           : 736.61226J, 293998.11s / 31536000.0s
[RADIO][radio_substate][RX]   : 17223.73798J, 286432.149s / 31536000.0s
[RADIO][radio_substate][TX]   : 2937.68873J, 4885.4s / 31536000.0s
TOTAL ENERGY USED: 21055.03004J => 6.31651Wh => 1257.01672mAh @ 5.025V

Energy usage for dev_8
[DEVICE][state][SLEEP]        : 156.96611J, 31237036.69s / 31536000.0s
[DEVICE][state][ON]           : 749.05257J, 298963.31s / 31536000.0s
[RADIO][radio_substate][RX]   : 17522.30539J, 291397.349s / 31536000.0s
[RADIO][radio_substate][TX]   : 2937.68873J, 4885.4s / 31536000.0s
TOTAL ENERGY USED: 21366.01280J => 6.40980Wh => 1275.58285mAh @ 5.025V

Energy usage for dev_9
[DEVICE][state][SLEEP]        : 156.97586J, 31238977.64s / 31536000.0s
[DEVICE][state][ON]           : 744.18952J, 297022.36s / 31536000.0s
[RADIO][radio_substate][RX]   : 17414.29028J, 289601.049s / 31536000.0s
[RADIO][radio_substate][TX]   : 2850.70779J, 4740.75s / 31536000.0s
TOTAL ENERGY USED: 21166.16345J => 6.34985Wh => 1263.65155mAh @ 5.025V


# Current experiments status

List:
- [x] part1
- [x] part2
- [x] part3
- [x] part4
- [x] part5
- [] part6
- [x] part7
- [x] part8