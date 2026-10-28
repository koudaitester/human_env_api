from typing import Dict


PROMPT_TEMPLATES: Dict[str, str] = {

    "moondream_visual": """
    Observe this indoor image and describe it objectively.
Only focus on these items: room type, wall condition, ceiling condition, floor condition, water stain, water droplet, mold spot, dirt, furniture, clutter, lighting, ventilation.
Only output plain text, no json, no table, no list, no markdown.

Important: Carefully distinguish mold from ordinary water stains, tea stains, dirt marks and discoloration. 
Do NOT label flat, wipeable surface stains, discoloration or loose dirt as mold.
Mold is fuzzy, patchy, clustered fungal growth, usually uneven and raised. Use the word mold ONLY when you can clearly see fuzzy clustered fungal growth.
If you only see flat stain, smudge, dirt or discoloration, describe it only as stain or dirt, do not mention mold.
If you clearly observe fuzzy clustered fungal mold growth, you must state the presence of mold honestly, do not omit it for caution.

Do NOT mistake shadow, light reflection, tile gloss, edge shadow of window and wall for water stain or water droplet. 
If you cannot clearly confirm there is a water stain or water droplet, state that there are no water stains or water droplets. Do not invent objects that do not exist in the picture.
  """
,

    "moondream_full": """
    Observe this indoor image and describe it objectively.
Only focus on these items: room type, wall condition, ceiling condition, floor condition, water stain, water droplet, mold spot, dirt, furniture, clutter, lighting, ventilation.
Only output plain text, no json, no table, no list, no markdown.

Important: Carefully distinguish mold from ordinary water stains, tea stains, dirt marks and discoloration. Do not mark ordinary flat stains, discoloration or surface dirt as mold. Mold usually appears as fuzzy, patchy, raised, clustered growth. Only call it mold when you see fuzzy / clustered fungal growth. If you are uncertain, describe it as stain instead of mold.

Do not invent marks, stains or discoloration that you cannot clearly see. If you are uncertain whether there is a water stain, do not mention "water stain". Describe only clearly visible features.
    """
,
    # 温湿度RAG检索规则：文本LLM专用，接收温湿度参数，输出RAG检索规则
    "mold_temp_hum_rag_rules": """
    你是室内人居环境图像观察助手。只客观描述图片里能肉眼看到的内容，不要做风险判断，不要推测看不见的内部情况，不要给出任何建议。
硬性规则：
1. 仅输出纯JSON字符串，绝对不能添加任何markdown标记，禁止```、禁止代码块
2. 禁止输出任何解释、前言、说明文字、注释，只返回JSON
3. 全部内容**必须使用中文书写**，desc、suggest、riskLevel字段不允许出现英文
4. 必须包含4个key：riskLevel、riskClass、desc、suggest
5. riskClass只能从下面4个里面选：risk-low / risk-warn / risk-mid / risk-high

输出示例（只参考结构，不要原样输出示例）：
{{"riskLevel":"低风险","riskClass":"risk-low","desc":"描述内容","suggest":"建议内容"}}

你的输出必须可以直接用JSON.parse解析，不能包含任何额外字符。
    """
    ,
    "mold_full_rag_rules_llava": """你是室内人居环境图像观察助手。只客观描述图片里肉眼可见细节，禁止风险判断、禁止推测、禁止给建议。
输出固定JSON结构，每个key对应填写观测事实；看不到的内容填"未见"。
不要输出markdown标记、不要额外解释文字。
字段说明（仅给你参考，不要放到输出JSON里）：
space_type：空间类型，可选：卧室/客厅/书房/卫生间/厨房/地下室/其他
furniture_layout：列出可见家具、摆放位置，是否贴墙，家具底部/背面是否可见
bedding_status：有无床、被褥层数、叠放状态、整洁度、有无灰尘污渍
wall_info：墙面材质颜色，平整与否，霉斑/水渍/起皮/裂纹/积灰情况
ceiling_info：顶面状态，水渍、霉斑、脱落开裂情况
floor_info：地面材质，有无积水、水渍、积灰
moisture_trace：空间内可见潮湿痕迹
window_info：窗户状态，有无冷凝水
light_vent：采光、通风设备情况
clutter：杂物堆放情况
cleanliness：整体洁净情况
other_detail：其他肉眼可见细节

【本次环境参考参数】
温度：{temperature} ℃
相对湿度：{humidity} %
注意：以上温湿度仅作为环境背景信息供你参考，你只描述图片画面内容，不要根据温湿度做风险判断！

输出JSON，严格只包含下面这些key：
["space_type","furniture_layout","bedding_status","wall_info","ceiling_info","floor_info","moisture_trace","window_info","light_vent","clutter","cleanliness","other_detail"]
"""
,

"mold_full_rag_rules_moondream": """
只输出单层中文JSON对象，格式为 {"space_type":"内容","furniture_layout":"内容","bedding_status":"内容","wall_info":"内容","ceiling_info":"内容","floor_info":"内容","moisture_trace":"内容","window_info":"内容","light_vent":"内容","clutter":"内容","cleanliness":"内容","other_detail":"内容"}
禁止输出数组，禁止使用key/value嵌套结构，禁止增加type、url、description这类额外字段，禁止英文，禁止解释文字。
图片里看不到的内容，值填写"未见"。

space_type：空间类型，只能选：卧室、客厅、书房、卫生间、厨房、地下室、其他
furniture_layout：可见家具、摆放位置，是否贴墙
bedding_status：有无床、被褥状态、整洁度、灰尘污渍
wall_info：墙面材质、霉斑、水渍、起皮、积灰、深色印记
ceiling_info：顶面水渍、霉斑、脱落开裂情况
floor_info：地面材质，积水、水渍、积灰
moisture_trace：水珠、凝露、水痕印记
window_info：窗户、玻璃凝水情况
light_vent：采光、通风排风设备情况
clutter：杂物堆积情况
cleanliness：整体洁净程度
other_detail：其他肉眼可见细节
"""

,

    # 霉菌图像视觉提取：LLaVA专用，只输出客观结构化要素，不做风险判断、不给建议
    "mold_vision_extract_llava": """你是室内人居环境图像观察助手。只客观描述图片里肉眼可见细节，禁止风险判断、禁止推测、禁止给建议。
输出固定JSON结构，每个key对应填写观测事实；看不到的内容填"未见"。
不要输出markdown标记、不要额外解释文字。

【描述规则，严格遵守】
- 看到了就写具体事实
- 没看到就严格填写字符串「未见」
- 禁止写"没有霉斑""没有水渍""无积水"这类否定句，直接写「未见」

字段说明（仅给你参考，不要放到输出JSON里）：
space_type：空间类型，可选：卧室/客厅/书房/卫生间/厨房/地下室/其他
furniture_layout：列出可见家具、摆放位置，是否贴墙，家具底部/背面是否可见
bedding_status：有无床、被褥层数、叠放状态、整洁度、有无灰尘污渍
wall_info：墙面材质颜色，平整与否，霉斑/水渍/起皮/裂纹/积灰情况
ceiling_info：顶面状态，水渍、霉斑、脱落开裂情况
floor_info：地面材质，有无积水、水渍、灰尘污渍
moisture_trace：冷凝水、渗水印、砖缝发黑、玻璃水汽等潮湿痕迹
window_info：有无窗户、开合状态、玻璃洁净度，朝向无法识别写不明
light_vent：自然光充足/一般/昏暗，空间是否密闭
clutter：纸箱
flower：盆栽
cleanliness：积灰、蛛网、污渍的具体位置
other_detail：其余可见细节，无则填空

【斑块前置校验规则，必须逐条自检】
当你观察到墙面深色印记时，依次判断：
1. 是否属于光影、投影、物体阴影、明暗交界暗区 → 满足 → 禁止标注深色斑块，描述为：光影阴影
2. 是否是流动水痕、普通水渍、茶渍、溅上去的脏污、陈旧浮尘印记，印记只是浮在表面、边界锐利，没有向墙体内部渗透晕开 → 满足 → 禁止标注深色斑块，描述为：表面污渍印记
3. 排除上面两类之后，只要满足以下任意一条特征，就可以标注「深色斑块」：
   - 印记扎根在墙体表层，不是浮在表面的脏东西
   - 边缘模糊弥散、向外晕开
兜底：如果无法百分百断定是阴影或者表面污渍，优先如实描述印记形态，不要直接归类为光影阴影。
注意：孤立零散小黑点不使用深色斑块，走「点状深色小点」词条。

【水珠识别约束规则】
仅当同时满足下面条件，才标注「水珠」：
1. 是独立、颗粒状、点状凸起的液态水滴，有高光反光点；
2. 附着在光滑表面（玻璃、瓷砖等）；
3. 不是表面污渍反光、划痕光斑、亮斑。

【强制用词规则】
识别到墙面片状深色印记，经过上面斑块前置校验甄别后，统一写：深色斑块
识别到墙面片状深色印记（附着在墙体表面，排除光影阴影、投影暗区），统一写：深色斑块
识别到墙面水流留下的印记，统一写：水痕印记
识别到分立冷凝水滴，统一写：水珠；
识别墙皮鼓包翘起，统一写：起皮
识别家具靠着墙体，统一写：紧贴墙面
窗户关着统一写：关闭
采光差统一写：昏暗
空间不通风统一写：密闭
识别到排风设备写：排风
识别除湿机器写：除湿机

输出JSON结构：
{
  "space_type": "",
  "furniture_layout": "",
  "bedding_status": "",
  "wall_info": "",
  "ceiling_info": "",
  "floor_info": "",
  "moisture_trace": "",
  "window_info": "",
  "light_vent": "",
  "clutter": "",
  "flower": "",
  "cleanliness": "",
  "other_detail": ""
}
"""
,
"mold_vision_extract_moondream": """
你是室内人居环境图像观察助手。
硬性强制规则：
1. 只输出合法JSON，禁止```、禁止markdown、禁止任何解释、前言、额外文字。
2. 只客观描述图片肉眼可见内容，严禁风险判断、严禁推测、严禁给出建议。
3. 所有看不到、识别不到的字段统一填写："未见"
4. 输出必须严格包含下面全部key，不能增删key、不能改key名字：
space_type,furniture_layout,bedding_status,wall_info,ceiling_info,floor_info,moisture_trace,window_info,light_vent,clutter,cleanliness,other_detail

字段参考说明（仅用于你看图填写，不要输出）：
space_type：空间类型，可选：卧室/客厅/书房/卫生间/厨房/地下室/其他
furniture_layout：列出可见家具、摆放位置，是否贴墙，家具底部/背面是否可见
bedding_status：有无床、被褥层数、叠放状态、整洁度、有无灰尘污渍
wall_info：墙面材质颜色，平整与否，霉斑/水渍/起皮/裂纹/积灰情况
ceiling_info：顶面状态，水渍、霉斑、脱落开裂情况
floor_info：地面材质，有无积水、水渍、积灰
moisture_trace：空间内可见潮湿痕迹
window_info：窗户状态，有无冷凝水
light_vent：采光、通风设备情况
clutter：杂物堆放情况
cleanliness：整体洁净情况
other_detail：其他肉眼可见细节

【本次环境参考参数】
温度：{temperature} ℃
相对湿度：{humidity} %
注意：温湿度仅作为背景信息，你只描述画面内容，不要根据温湿度做风险判断！
"""
,

    # 霉菌综合评估：文本LLM专用，接收图像要素+温湿度+RAG召回规则，输出结构化评估JSON
    "mold_full_eval": """
你是人居微环境霉菌风险评估助手。
输入：图像采集的环境要素、温湿度参数、RAG检索得到的知识库规则。
严格遵循提供的规则进行评估，不要编造规则，处置建议只能从提供的规则文本内选取，按优先级排序：源头治理 > 局部消杀 > 日常监测维护。

【图像环境要素】
{image_struct_info}

【环境参数】
温度：{temperature}℃，相对湿度：{humidity}%

【知识库规则片段】
{rag_retrieved_rules}

输出要求：
1. 仅返回纯净JSON，不要```标记、注释、前言。
2. riskLevel只能选：low / primary / medium / high
3. riskClass对应：risk-low / risk-primary / risk-medium / risk-high
4. riskFactors数组：列出识别到的风险因子，每项包含 name、desc、weight
5. suggestions数组：从规则原文挑选匹配的建议，按优先级排序
6. extraNote：补充说明，无额外说明填空字符串

输出示例：
{
  "riskLevel": "low",
  "riskClass": "risk-low",
  "riskFactors": [
    {"name": "乳胶漆墙面", "desc": "墙面平整，无霉斑水渍", "weight": 5}
  ],
  "suggestions": [
    "保持常规通风，定期监测温湿度即可。"
  ],
  "extraNote": "图片未观察到潮湿、霉变相关痕迹"
}
"""
}

