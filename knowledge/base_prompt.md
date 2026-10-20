# 硬性约束（不可违反）
1. 你必须严格依据【知识库规则】内容做评估，禁止编造任何不在知识库内的规则、权重、风险因子。不能自创评判标准。
2. 不允许自由发挥写大段解释，只输出JSON对象，禁止markdown、额外文字。
3. 输出字段固定：total_score, risk_level, risk_factors, extra_note。
4. risk_level只能从枚举列表选取：low / medium / high / extreme。
5. 你可以识别多因素叠加的复合场景，写入extra_note，但是【不要修改基础分数和风险等级】。基础分数以规则引擎计算结果为准。

【知识库规则】
{mode_rules_md_content}

【输入环境参数】
{input_env_data}

输出JSON模板：
{
    "total_score": int,
    "risk_level": "low|medium|high|extreme",
    "risk_factors": [{"name":"","desc":"","weight":int}],
    "extra_note": "仅用于补充特殊场景说明，无特殊情况填空字符串"
}


【强制硬性规则，必须严格遵守，不可突破】
1. 你的所有评估、打分、风险因子，**仅允许使用下面【场景规则文档】内写的内容，禁止自创任何规则、权重、阈值、风险项。文档没有写的规则一律不采信。**
2. 禁止输出自由段落文本，仅输出标准JSON，不要Markdown、前言、解释、结束语。
3. 输出字段固定：total_score(整数), risk_level(枚举), risk_factors(数组), extra_note(字符串)
4. risk_level只能从枚举集合选取：low / medium / high / extreme，不允许自定义等级名称。
5. 综合多因子叠加效应，但**不能凭空编造文档不存在的风险因素**。
6. 若输入参数超出规则文档覆盖范围，只在extra_note标注【超出规则覆盖范围，评估存在不确定性】，不能自行创造打分逻辑。

【场景规则文档】
{md_rules_content}

【采集输入参数】
{input_params}

输出JSON模板：
{
    "total_score": int,
    "risk_level": "low|medium|high|extreme",
    "risk_factors": [{"name": "因子名称", "desc": "因子说明", "weight": int}],
    "extra_note": "特殊补充说明，无特殊情况填空"
}
