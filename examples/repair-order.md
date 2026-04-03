# 修复令案例

## 背景

执行阶段发现依赖污染，导致执行池输出不稳定。

## 锦衣卫诊断

- 问题源：`executor_pool/api_builder`
- 影响范围：依赖安装链与后续生成流程
- 风险等级：高

## 修复建议

- 策略：`patch_then_rerun`
- 范围：`executor_pool/api_builder`

## 用户修复令

```json
{
  "strategy": "patch_then_rerun",
  "reason": "critical dependency issue",
  "scope": "executor_pool/api_builder"
}
```

## 状态流转

```text
executing
→ repair_pending
→ repair_authorized
→ rerunning
→ executing
```
