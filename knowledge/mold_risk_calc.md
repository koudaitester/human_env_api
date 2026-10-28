# FEATURE_GROUPS
深色斑块,dark patch,dark spot,mold||81||墙面识别到深色斑块样痕迹，有可能是霉斑、污渍，此模型只做辅助评估；建议近距离实地观察，触摸辨别，同步控制环境湿度
积水,地面积水,standing water,pooled water,water on the floor||30||地面存在积水，及时擦干，保持地面干燥
起皮,鼓包,墙皮脱落,peeling,bulging||25||墙皮起皮鼓包，大概率受潮，建议检查墙体内部渗水
dirt,dirty||10||墙面/角落存在积尘脏污，积尘在高湿环境易滋生霉菌孢子，建议及时清洁，控制环境湿度
水痕印记,水渍,water stain,water mark,stain||30||墙面存在水痕印记/地面水渍，排查渗水源并持续观察
水珠,冷凝水,结露,water droplet,condensation||30||观察到冷凝水珠，加强通风，降低室内湿度
紧贴墙面,紧靠墙面,贴墙摆放,靠墙,against wall||6||家具/杂物紧贴墙面摆放，建议预留空隙，减少受潮发霉风险
纸箱,硬纸箱,纸箱子,cardboard box||6||室内堆放易吸潮纸箱，建议远离墙面并定期清理
被子,被褥,厚床品,bedding||5||厚床品容易蓄积潮气，建议定期晾晒
布艺沙发,布艺家具,布艺窗帘,fabric sofa,fabric curtain||5||布艺织物容易吸附潮气，定期通风晾晒
地毯,地垫,carpet,rug||7||地毯容易蓄积潮气，定期吸尘干燥
昏暗,光线差,采光不足,采光昏暗,dim,dark||5||区域采光昏暗，紫外线不足，不利于抑制霉菌
盆栽,绿植,花盆,plant,potted plant||4||盆栽浇水容易增加局部湿度，尽量远离墙体
浮尘,灰尘,积灰,dust||3||表面积灰，灰尘容易附着潮气，定期清洁
蛛网,蜘蛛网,cobweb||3||角落存在蛛网，建议清洁，保持环境干燥
关闭,关窗,窗户紧闭,window closed||5||窗户处于关闭状态，建议每日定时开窗通风换气
密闭,不通风,空气不流通,poor ventilation||5||空间相对密闭，建议增加通风频次
排风,排风扇,排气扇,exhaust fan||-8||空间配有排风设备，合理开启可以降低潮湿风险
除湿机,除湿设备,dehumidifier||-12||现场配有除湿设备，合理使用能够抑制霉菌滋生
wood,wooden||30||老旧木质表面存在积污，存在滋生霉菌风险，建议伍德灯复检，加强通风除湿

# MUTEX_GROUPS
["点状深色小点","深色斑块","dark patch","dark spot"]||深色痕迹同源互斥
["水痕印记","水渍印记","water stain","water mark"]||水痕同源互斥

# NEGATION_WORDS
没有,无,未见,未发现,不存在,无明显,无可见,没有可见

# HUMIDITY_RULES
75||30||当前相对湿度{rh}%≥75%，极易滋生霉菌，优先除湿
65||20||当前相对湿度{rh}%处于霉菌快速繁殖区间，建议除湿至65%以下
55||10||当前相对湿度{rh}%已达霉菌萌发阈值，注意通风控湿

# TEMP_CONFIG
18,28||5||当前温度{t}℃落在霉菌适宜繁殖区间，需配合湿度重点防控

# LEVEL_RULES
81||高风险||risk-high
41||中风险||risk-medium
21||初级风险||risk-primary
0||低风险||risk-low

# SOFT_DOWNGRADE_RULES
\b(a small amount of mold|a small mold spot|visible mold|some mold spots)\b||only_keep||深色斑块||81||墙面识别到深色斑块样痕迹，有可能是霉斑、污渍，此模型只做辅助评估；建议近距离实地观察，触摸辨别，同步控制环境湿度
\b(some appearing to be mold|or mold|free of mold|not contain any mold|other visible signs of mold growth|no visible mold|not clear if it is a mold stain or a fungal growth)\b||convert||水痕印记||20||墙面疑似存在水痕印记/地面水渍，排查渗水源并持续观察
\b(wood|wooden)\b.*?\bdirt\b||offset||dirt||-10||木质表面普通尘土，抵消 dirt 10分

# SOFT_APPEND_FEATURE_RULES
\b(water stain|water mark)\b||append||水痕印记||20||墙面存在水痕印记/地面水渍，排查渗水源并持续观察

# LESION_KEYWORDS
深色斑块,点状深色小点,积水,起皮,水痕印记,水珠,mold,wood,wooden,water stain,water droplet

# SPACE_MAP
卫生间: bathroom,toilet
厨房: kitchen
卧室: bedroom
客厅: living room,lounge
书房: study
地下室: basement

# FIELD_KEYWORDS
wall_info: wall,walls,mold,stain,water mark,dirt,墙面,霉斑,水渍
ceiling_info: ceiling,top,水渍,霉斑,stain
floor_info: floor,ground,water,积水,水渍
moisture_trace: droplet,condensation,水珠,凝露
furniture_layout: furniture,cabinet,chair,towel rack,家具
window_info: window,窗户
light_vent: light,dark,vent,ventilation,采光,昏暗
clutter: clutter,mess,杂物
cleanliness: clean,dirty,干净,脏污
other_detail: