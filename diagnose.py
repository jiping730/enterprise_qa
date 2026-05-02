from app.evaluation import _is_exact_match, _is_partial_match

# 考勤
print("考勤完全匹配:", _is_exact_match(
    "公司实行标准工时制，每日工作时间不超过8小时，每周不超过40小时。同时推行弹性工作制。",
    "每日工作时间不超过8小时，每周不超过40小时，弹性工作制可选。"
))
# 信息安全
print("信息安全完全匹配:", _is_exact_match(
    "严禁泄露客户资料，定期更换密码，使用VPN访问内网资源",
    "不得泄露客户数据，定期更换密码，使用VPN访问内网资源"
))