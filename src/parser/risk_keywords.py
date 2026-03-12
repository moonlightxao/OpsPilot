# -*- coding: utf-8 -*-
"""
内置风险关键词库

定义不同风险级别的关键词，用于快速识别操作风险。
"""

BUILTIN_RISK_KEYWORDS = {
    "high": {
        "keywords": [
            "删除", "下线", "销毁", "清空", "回滚", "终止", "停止", "禁用",
            "truncate", "drop", "remove", "delete", "destroy"
        ],
        "score": 90,
        "category": "destructive"
    },
    "medium": {
        "keywords": [
            "修改", "变更", "重建", "重启", "替换", "覆盖", "批量", "迁移",
            "modify", "change", "rebuild", "restart", "replace", "override"
        ],
        "score": 60,
        "category": "impactful"
    },
    "low": {
        "keywords": [
            "新增", "配置", "部署", "安装", "启用",
            "add", "config", "deploy", "install", "enable"
        ],
        "score": 30,
        "category": "routine"
    }
}

# 安全关键词白名单
SAFE_KEYWORDS = [
    "备份", "检查", "查询", "查看", "监控", "巡检",
    "backup", "check", "query", "view", "monitor", "inspect"
]

# 组合风险模式（两个关键词同时出现升级风险）
COMPOUND_RISK_PATTERNS = [
    (["批量", "删除"], "high", 95),
    (["生产", "删除"], "high", 95),
    (["主库", "修改"], "high", 90),
    (["生产", "修改"], "high", 90),
    (["全量", "删除"], "high", 95),
    (["清空", "数据"], "high", 90),
    (["重启", "服务"], "medium", 70),
    (["批量", "修改"], "medium", 75),
]
