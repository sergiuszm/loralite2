# Energy usage over a year for a GW always on with radio always in RX mode

## SX1262 

Radio current draw in RX mode: 4,3mA

MCU current draw: 0.5mA

TOTAL ENERGY USED @ 5.025V: 
- 758529.10080J
- 227.55873Wh
- 45285.31945mAh => 45.32Ah

## SX1276

Radio current draw in RX mode: 12mA

MCU current draw: 0.5mA

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

GW: 46091.04398J => 13.82731Wh => 2751.70412mAh @ 5.025V
End-Device: 7044.99774J => 2.11350Wh => 420.59688mAh @ 5.025V

Number of packets: 52559

## SX1276

GW: 46091.04398J => 13.82731Wh => 2751.70412mAh @ 5.025V
End-Device: 18172.20487J => 5.45166Wh => 1084.90775mAh @ 5.025V

Packets received: 52560
Bytes received: 777290

# Energy of end-device

## SX1276

## GW always on in RX

31,536,000.000s	Stats for dev_0 [GW]
31,536,000.000s		[Packets sent]      : 0
31,536,000.000s		[Bytes sent]        : 0
31,536,000.000s		[Packets received]  : 2100
31,536,000.000s		[Bytes received]    : 68,190

31,536,000.000s	Stats for dev_1 [END_DEV]
31,536,000.000s		[Packets sent]      : 2100
31,536,000.000s		[Bytes sent]        : 68,190
31,536,000.000s		[Packets received]  : 0
31,536,000.000s		[Bytes received]    : 0

31,536,000.000s	Energy usage for dev_0
31,536,000.000s		[DEVICE][state][SLEEP]        : 0.00000J, 0.001s / 31536000.0s
31,536,000.000s		[DEVICE][state][ON]           : 79013.44800J, 31535999.999s / 31536000.0s
31,536,000.000s		[DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[DEVICE][substate][NONE]      : 0.00000J, 31536000.0s / 31536000.0s
31,536,000.000s		[DEVICE][substate][OP]        : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][ON]      : 0.00000J, 31535999.998s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][OFF]     : 0.00000J, 0.002s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][NONE] : 0.00000J, 0.002s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][RX]   : 1896322.75188J, 31535999.998s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][TX]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s	TOTAL ENERGY USED: 1975336.19988J => 592.60086Wh => 117930.51940mAh @ 5.025V

31,536,000.000s	Energy usage for dev_1
31,536,000.000s		[DEVICE][state][SLEEP]        : 158.44406J, 31531155.348s / 31536000.0s
31,536,000.000s		[DEVICE][state][ON]           : 12.13828J, 4844.652s / 31536000.0s
31,536,000.000s		[DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[DEVICE][substate][NONE]      : 0.00000J, 31531260.3s / 31536000.0s
31,536,000.000s		[DEVICE][substate][OP]        : 0.00000J, 4739.7s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][ON]      : 0.00000J, 4804.752s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][OFF]     : 0.00000J, 31531195.248s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][NONE] : 0.00000J, 31531298.1s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][RX]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][TX]   : 2827.34651J, 4701.9s / 31536000.0s
31,536,000.000s	TOTAL ENERGY USED: 2997.92884J => 0.89938Wh => 178.98083mAh @ 5.025V


### CMD every 120

Number of packets received: 52559
Number of packets sent: 1907

31,536,000.000s	Energy usage for dev_0
31,536,000.000s		[DEVICE][state][SLEEP]        : 157.73228J, 31389509.442s / 31536000.0s
31,536,000.000s		[DEVICE][state][ON]           : 367.03209J, 146490.558s / 31536000.0s
31,536,000.000s		[DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[DEVICE][substate][NONE]      : 0.00000J, 31392137.442s / 31536000.0s
31,536,000.000s		[DEVICE][substate][OP]        : 0.00000J, 143862.558s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][ON]      : 0.00000J, 145478.562s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][OFF]     : 0.00000J, 31390521.438s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][NONE] : 0.00000J, 31393096.878s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][RX]   : 4015.61496J, 66780.0s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][TX]   : 45774.35572J, 76123.122s / 31536000.0s
31,536,000.000s	TOTAL ENERGY USED: 50314.73506J => 15.09442Wh => 3003.86478mAh @ 5.025V

31,536,000.000s	Energy usage for dev_1
31,536,000.000s		[DEVICE][state][SLEEP]        : 156.99347J, 31242482.06s / 31536000.0s
31,536,000.000s		[DEVICE][state][ON]           : 735.40920J, 293517.94s / 31536000.0s
31,536,000.000s		[DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[DEVICE][substate][NONE]      : 0.00000J, 31531692.69s / 31536000.0s
31,536,000.000s		[DEVICE][substate][OP]        : 0.00000J, 4307.31s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][ON]      : 0.00000J, 290837.379s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][OFF]     : 0.00000J, 31245162.621s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][NONE] : 0.00000J, 31245162.621s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][RX]   : 17229.62611J, 286530.069s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][TX]   : 2590.07165J, 4307.31s / 31536000.0s
31,536,000.000s	TOTAL ENERGY USED: 20712.10043J => 6.21363Wh => 1236.54331mAh @ 5.025V

31,536,000.000s	Energy usage for dev_2
31,536,000.000s		[DEVICE][state][SLEEP]        : 156.97026J, 31237863.442s / 31536000.0s
31,536,000.000s		[DEVICE][state][ON]           : 746.98115J, 298136.558s / 31536000.0s
31,536,000.000s		[DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[DEVICE][substate][NONE]      : 0.00000J, 31531573.288s / 31536000.0s
31,536,000.000s		[DEVICE][substate][OP]        : 0.00000J, 4426.712s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][ON]      : 0.00000J, 295455.997s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][OFF]     : 0.00000J, 31240544.003s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][NONE] : 0.00000J, 31240544.003s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][RX]   : 17500.17297J, 291029.285s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][TX]   : 2661.87046J, 4426.712s / 31536000.0s
31,536,000.000s	TOTAL ENERGY USED: 21065.99484J => 6.31980Wh => 1257.67133mAh @ 5.025V

31,536,000.000s	Energy usage for dev_3
31,536,000.000s		[DEVICE][state][SLEEP]        : 156.97900J, 31239602.888s / 31536000.0s
31,536,000.000s		[DEVICE][state][ON]           : 742.62296J, 296397.112s / 31536000.0s
31,536,000.000s		[DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[DEVICE][substate][NONE]      : 0.00000J, 31531692.69s / 31536000.0s
31,536,000.000s		[DEVICE][substate][OP]        : 0.00000J, 4307.31s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][ON]      : 0.00000J, 293716.551s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][OFF]     : 0.00000J, 31242283.449s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][NONE] : 0.00000J, 31242283.449s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][RX]   : 17402.75648J, 289409.241s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][TX]   : 2590.07165J, 4307.31s / 31536000.0s
31,536,000.000s	TOTAL ENERGY USED: 20892.43010J => 6.26773Wh => 1247.30926mAh @ 5.025V

31,536,000.000s	Energy usage for dev_4
31,536,000.000s		[DEVICE][state][SLEEP]        : 156.95700J, 31235223.074s / 31536000.0s
31,536,000.000s		[DEVICE][state][ON]           : 753.59659J, 300776.926s / 31536000.0s
31,536,000.000s		[DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[DEVICE][substate][NONE]      : 0.00000J, 31531692.69s / 31536000.0s
31,536,000.000s		[DEVICE][substate][OP]        : 0.00000J, 4307.31s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][ON]      : 0.00000J, 298096.365s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][OFF]     : 0.00000J, 31237903.635s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][NONE] : 0.00000J, 31237903.635s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][RX]   : 17666.12346J, 293789.055s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][TX]   : 2590.07165J, 4307.31s / 31536000.0s
31,536,000.000s	TOTAL ENERGY USED: 21166.74869J => 6.35002Wh => 1263.68649mAh @ 5.025V

31,536,000.000s	Energy usage for dev_5
31,536,000.000s		[DEVICE][state][SLEEP]        : 156.96454J, 31236723.716s / 31536000.0s
31,536,000.000s		[DEVICE][state][ON]           : 749.83673J, 299276.284s / 31536000.0s
31,536,000.000s		[DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[DEVICE][substate][NONE]      : 0.00000J, 31531692.69s / 31536000.0s
31,536,000.000s		[DEVICE][substate][OP]        : 0.00000J, 4307.31s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][ON]      : 0.00000J, 296595.723s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][OFF]     : 0.00000J, 31239404.277s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][NONE] : 0.00000J, 31239404.277s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][RX]   : 17575.88685J, 292288.413s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][TX]   : 2590.07165J, 4307.31s / 31536000.0s
31,536,000.000s	TOTAL ENERGY USED: 21072.75977J => 6.32183Wh => 1258.07521mAh @ 5.025V

31,536,000.000s	Energy usage for dev_6
31,536,000.000s		[DEVICE][state][SLEEP]        : 156.93893J, 31231627.49s / 31536000.0s
31,536,000.000s		[DEVICE][state][ON]           : 762.60532J, 304372.51s / 31536000.0s
31,536,000.000s		[DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[DEVICE][substate][NONE]      : 0.00000J, 31531573.288s / 31536000.0s
31,536,000.000s		[DEVICE][substate][OP]        : 0.00000J, 4426.712s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][ON]      : 0.00000J, 301691.949s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][OFF]     : 0.00000J, 31234308.051s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][NONE] : 0.00000J, 31234308.051s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][RX]   : 17875.15323J, 297265.237s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][TX]   : 2661.87046J, 4426.712s / 31536000.0s
31,536,000.000s	TOTAL ENERGY USED: 21456.56794J => 6.43697Wh => 1280.98913mAh @ 5.025V

31,536,000.000s	Energy usage for dev_7
31,536,000.000s		[DEVICE][state][SLEEP]        : 156.99287J, 31242362.658s / 31536000.0s
31,536,000.000s		[DEVICE][state][ON]           : 735.70836J, 293637.342s / 31536000.0s
31,536,000.000s		[DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[DEVICE][substate][NONE]      : 0.00000J, 31531573.288s / 31536000.0s
31,536,000.000s		[DEVICE][substate][OP]        : 0.00000J, 4426.712s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][ON]      : 0.00000J, 290956.781s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][OFF]     : 0.00000J, 31245043.219s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][NONE] : 0.00000J, 31245043.219s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][RX]   : 17229.62611J, 286530.069s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][TX]   : 2661.87046J, 4426.712s / 31536000.0s
31,536,000.000s	TOTAL ENERGY USED: 20784.19780J => 6.23526Wh => 1240.84763mAh @ 5.025V

31,536,000.000s	Energy usage for dev_8
31,536,000.000s		[DEVICE][state][SLEEP]        : 156.97026J, 31237863.442s / 31536000.0s
31,536,000.000s		[DEVICE][state][ON]           : 746.98115J, 298136.558s / 31536000.0s
31,536,000.000s		[DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[DEVICE][substate][NONE]      : 0.00000J, 31531573.288s / 31536000.0s
31,536,000.000s		[DEVICE][substate][OP]        : 0.00000J, 4426.712s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][ON]      : 0.00000J, 295455.997s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][OFF]     : 0.00000J, 31240544.003s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][NONE] : 0.00000J, 31240544.003s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][RX]   : 17500.17297J, 291029.285s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][TX]   : 2661.87046J, 4426.712s / 31536000.0s
31,536,000.000s	TOTAL ENERGY USED: 21065.99484J => 6.31980Wh => 1257.67133mAh @ 5.025V

31,536,000.000s	Energy usage for dev_9
31,536,000.000s		[DEVICE][state][SLEEP]        : 156.97900J, 31239602.888s / 31536000.0s
31,536,000.000s		[DEVICE][state][ON]           : 742.62296J, 296397.112s / 31536000.0s
31,536,000.000s		[DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[DEVICE][substate][NONE]      : 0.00000J, 31531692.69s / 31536000.0s
31,536,000.000s		[DEVICE][substate][OP]        : 0.00000J, 4307.31s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][ON]      : 0.00000J, 293716.551s / 31536000.0s
31,536,000.000s		[RADIO][radio_state][OFF]     : 0.00000J, 31242283.449s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][NONE] : 0.00000J, 31242283.449s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][RX]   : 17402.75648J, 289409.241s / 31536000.0s
31,536,000.000s		[RADIO][radio_substate][TX]   : 2590.07165J, 4307.31s / 31536000.0s
31,536,000.000s	TOTAL ENERGY USED: 20892.43010J => 6.26773Wh => 1247.30926mAh @ 5.025V


### CMD every 100

31,536,000.000s Stats for dev_0 [GW]
31,536,000.000s         [Packets sent]      : 52560
31,536,000.000s         [Bytes sent]        : 785,690
31,536,000.000s         [Packets received]  : 18350
31,536,000.000s         [Bytes received]    : 598,010

31,536,000.000s Stats for dev_1 [END_DEV]
31,536,000.000s         [Packets sent]      : 2100
31,536,000.000s         [Bytes sent]        : 67,140
31,536,000.000s         [Packets received]  : 52560
31,536,000.000s         [Bytes received]    : 785,690

31,536,000.000s Stats for dev_2 [END_DEV]
31,536,000.000s         [Packets sent]      : 2100
31,536,000.000s         [Bytes sent]        : 68,190
31,536,000.000s         [Packets received]  : 52560
31,536,000.000s         [Bytes received]    : 785,690

31,536,000.000s Stats for dev_3 [END_DEV]
31,536,000.000s         [Packets sent]      : 2100
31,536,000.000s         [Bytes sent]        : 67,140
31,536,000.000s         [Packets received]  : 52560
31,536,000.000s         [Bytes received]    : 785,690

31,536,000.000s Stats for dev_4 [END_DEV]
31,536,000.000s         [Packets sent]      : 2100
31,536,000.000s         [Bytes sent]        : 67,140
31,536,000.000s         [Packets received]  : 52560
31,536,000.000s         [Bytes received]    : 785,690

31,536,000.000s Stats for dev_5 [END_DEV]
31,536,000.000s         [Packets sent]      : 2100
31,536,000.000s         [Bytes sent]        : 67,140
31,536,000.000s         [Packets received]  : 52560
31,536,000.000s         [Bytes received]    : 785,690

31,536,000.000s Stats for dev_6 [END_DEV]
31,536,000.000s         [Packets sent]      : 2100
31,536,000.000s         [Bytes sent]        : 68,190
31,536,000.000s         [Packets received]  : 52560
31,536,000.000s         [Bytes received]    : 785,690

31,536,000.000s Stats for dev_7 [END_DEV]
31,536,000.000s         [Packets sent]      : 2100
31,536,000.000s         [Bytes sent]        : 68,190
31,536,000.000s         [Packets received]  : 52560
31,536,000.000s         [Bytes received]    : 785,690

31,536,000.000s Stats for dev_8 [END_DEV]
31,536,000.000s         [Packets sent]      : 2100
31,536,000.000s         [Bytes sent]        : 68,190
31,536,000.000s         [Packets received]  : 52560
31,536,000.000s         [Bytes received]    : 785,690

31,536,000.000s Stats for dev_9 [END_DEV]
31,536,000.000s         [Packets sent]      : 2100
31,536,000.000s         [Bytes sent]        : 67,140
31,536,000.000s         [Packets received]  : 52560
31,536,000.000s         [Bytes received]    : 785,690

31,536,000.000s Energy usage for dev_0
31,536,000.000s         [DEVICE][state][SLEEP]        : 157.69848J, 31382782.102s / 31536000.0s
31,536,000.000s         [DEVICE][state][ON]           : 383.88744J, 153217.898s / 31536000.0s
31,536,000.000s         [DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s         [DEVICE][substate][NONE]      : 0.00000J, 31385410.102s / 31536000.0s
31,536,000.000s         [DEVICE][substate][OP]        : 0.00000J, 150589.898s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][ON]      : 0.00000J, 152204.558s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][OFF]     : 0.00000J, 31383795.442s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][NONE] : 0.00000J, 31386370.882s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][RX]   : 4419.70200J, 73500.0s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][TX]   : 45777.96124J, 76129.118s / 31536000.0s
31,536,000.000s TOTAL ENERGY USED: 50739.24916J => 15.22177Wh => 3029.20891mAh @ 5.025V

31,536,000.000s Energy usage for dev_1
31,536,000.000s         [DEVICE][state][SLEEP]        : 156.99179J, 31242146.54s / 31536000.0s
31,536,000.000s         [DEVICE][state][ON]           : 736.24984J, 293853.46s / 31536000.0s
31,536,000.000s         [DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s         [DEVICE][substate][NONE]      : 0.00000J, 31531259.25s / 31536000.0s
31,536,000.000s         [DEVICE][substate][OP]        : 0.00000J, 4740.75s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][ON]      : 0.00000J, 291172.899s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][OFF]     : 0.00000J, 31244827.101s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][NONE] : 0.00000J, 31244827.101s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][RX]   : 17223.73798J, 286432.149s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][TX]   : 2850.70779J, 4740.75s / 31536000.0s
31,536,000.000s TOTAL ENERGY USED: 20967.68740J => 6.29031Wh => 1251.80223mAh @ 5.025V

31,536,000.000s Energy usage for dev_2
31,536,000.000s         [DEVICE][state][SLEEP]        : 156.96611J, 31237036.69s / 31536000.0s
31,536,000.000s         [DEVICE][state][ON]           : 749.05257J, 298963.31s / 31536000.0s
31,536,000.000s         [DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s         [DEVICE][substate][NONE]      : 0.00000J, 31531114.6s / 31536000.0s
31,536,000.000s         [DEVICE][substate][OP]        : 0.00000J, 4885.4s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][ON]      : 0.00000J, 296282.749s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][OFF]     : 0.00000J, 31239717.251s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][NONE] : 0.00000J, 31239717.251s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][RX]   : 17522.30539J, 291397.349s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][TX]   : 2937.68873J, 4885.4s / 31536000.0s
31,536,000.000s TOTAL ENERGY USED: 21366.01280J => 6.40980Wh => 1275.58285mAh @ 5.025V

31,536,000.000s Energy usage for dev_3
31,536,000.000s         [DEVICE][state][SLEEP]        : 156.97586J, 31238977.64s / 31536000.0s
31,536,000.000s         [DEVICE][state][ON]           : 744.18952J, 297022.36s / 31536000.0s
31,536,000.000s         [DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s         [DEVICE][substate][NONE]      : 0.00000J, 31531259.25s / 31536000.0s
31,536,000.000s         [DEVICE][substate][OP]        : 0.00000J, 4740.75s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][ON]      : 0.00000J, 294341.799s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][OFF]     : 0.00000J, 31241658.201s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][NONE] : 0.00000J, 31241658.201s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][RX]   : 17414.29028J, 289601.049s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][TX]   : 2850.70779J, 4740.75s / 31536000.0s
31,536,000.000s TOTAL ENERGY USED: 21166.16345J => 6.34985Wh => 1263.65155mAh @ 5.025V

31,536,000.000s Energy usage for dev_4
31,536,000.000s         [DEVICE][state][SLEEP]        : 156.95164J, 31234157.09s / 31536000.0s
31,536,000.000s         [DEVICE][state][ON]           : 756.26741J, 301842.91s / 31536000.0s
31,536,000.000s         [DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s         [DEVICE][substate][NONE]      : 0.00000J, 31531259.25s / 31536000.0s
31,536,000.000s         [DEVICE][substate][OP]        : 0.00000J, 4740.75s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][ON]      : 0.00000J, 299162.349s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][OFF]     : 0.00000J, 31236837.651s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][NONE] : 0.00000J, 31236837.651s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][RX]   : 17704.15959J, 294421.599s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][TX]   : 2850.70779J, 4740.75s / 31536000.0s
31,536,000.000s TOTAL ENERGY USED: 21468.08643J => 6.44043Wh => 1281.67680mAh @ 5.025V

31,536,000.000s Energy usage for dev_5
31,536,000.000s         [DEVICE][state][SLEEP]        : 156.95994J, 31235808.74s / 31536000.0s
31,536,000.000s         [DEVICE][state][ON]           : 752.12920J, 300191.26s / 31536000.0s
31,536,000.000s         [DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s         [DEVICE][substate][NONE]      : 0.00000J, 31531259.25s / 31536000.0s
31,536,000.000s         [DEVICE][substate][OP]        : 0.00000J, 4740.75s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][ON]      : 0.00000J, 297510.699s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][OFF]     : 0.00000J, 31238489.301s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][NONE] : 0.00000J, 31238489.301s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][RX]   : 17604.84257J, 292769.949s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][TX]   : 2850.70779J, 4740.75s / 31536000.0s
31,536,000.000s TOTAL ENERGY USED: 21364.63950J => 6.40939Wh => 1275.50087mAh @ 5.025V

31,536,000.000s Energy usage for dev_6
31,536,000.000s         [DEVICE][state][SLEEP]        : 156.93135J, 31230120.29s / 31536000.0s
31,536,000.000s         [DEVICE][state][ON]           : 766.38161J, 305879.71s / 31536000.0s
31,536,000.000s         [DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s         [DEVICE][substate][NONE]      : 0.00000J, 31531114.6s / 31536000.0s
31,536,000.000s         [DEVICE][substate][OP]        : 0.00000J, 4885.4s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][ON]      : 0.00000J, 303199.149s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][OFF]     : 0.00000J, 31232800.851s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][NONE] : 0.00000J, 31232800.851s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][RX]   : 17938.20235J, 298313.749s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][TX]   : 2937.68873J, 4885.4s / 31536000.0s
31,536,000.000s TOTAL ENERGY USED: 21799.20405J => 6.53976Wh => 1301.44502mAh @ 5.025V

31,536,000.000s Energy usage for dev_7
31,536,000.000s         [DEVICE][state][SLEEP]        : 156.99106J, 31242001.89s / 31536000.0s
31,536,000.000s         [DEVICE][state][ON]           : 736.61226J, 293998.11s / 31536000.0s
31,536,000.000s         [DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s         [DEVICE][substate][NONE]      : 0.00000J, 31531114.6s / 31536000.0s
31,536,000.000s         [DEVICE][substate][OP]        : 0.00000J, 4885.4s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][ON]      : 0.00000J, 291317.549s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][OFF]     : 0.00000J, 31244682.451s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][NONE] : 0.00000J, 31244682.451s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][RX]   : 17223.73798J, 286432.149s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][TX]   : 2937.68873J, 4885.4s / 31536000.0s
31,536,000.000s TOTAL ENERGY USED: 21055.03004J => 6.31651Wh => 1257.01672mAh @ 5.025V

31,536,000.000s Energy usage for dev_8
31,536,000.000s         [DEVICE][state][SLEEP]        : 156.96611J, 31237036.69s / 31536000.0s
31,536,000.000s         [DEVICE][state][ON]           : 749.05257J, 298963.31s / 31536000.0s
31,536,000.000s         [DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s         [DEVICE][substate][NONE]      : 0.00000J, 31531114.6s / 31536000.0s
31,536,000.000s         [DEVICE][substate][OP]        : 0.00000J, 4885.4s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][ON]      : 0.00000J, 296282.749s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][OFF]     : 0.00000J, 31239717.251s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][NONE] : 0.00000J, 31239717.251s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][RX]   : 17522.30539J, 291397.349s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][TX]   : 2937.68873J, 4885.4s / 31536000.0s
31,536,000.000s TOTAL ENERGY USED: 21366.01280J => 6.40980Wh => 1275.58285mAh @ 5.025V

31,536,000.000s Energy usage for dev_9
31,536,000.000s         [DEVICE][state][SLEEP]        : 156.97586J, 31238977.64s / 31536000.0s
31,536,000.000s         [DEVICE][state][ON]           : 744.18952J, 297022.36s / 31536000.0s
31,536,000.000s         [DEVICE][state][OFF]          : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s         [DEVICE][substate][NONE]      : 0.00000J, 31531259.25s / 31536000.0s
31,536,000.000s         [DEVICE][substate][OP]        : 0.00000J, 4740.75s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][SLEEP]   : 0.00000J, 0.0s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][ON]      : 0.00000J, 294341.799s / 31536000.0s
31,536,000.000s         [RADIO][radio_state][OFF]     : 0.00000J, 31241658.201s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][NONE] : 0.00000J, 31241658.201s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][RX]   : 17414.29028J, 289601.049s / 31536000.0s
31,536,000.000s         [RADIO][radio_substate][TX]   : 2850.70779J, 4740.75s / 31536000.0s
31,536,000.000s TOTAL ENERGY USED: 21166.16345J => 6.34985Wh => 1263.65155mAh @ 5.025V
