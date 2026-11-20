# Atlas v0.0.10

正式收录 [PR #28](https://github.com/MagnetOscar/Atlas/pull/28) 的流量统计修复，UI 布局保持不变。

- 修正整月查询可能选到空小时聚合层的问题：闭合历史使用已有的五分钟层，近期两小时及重置边缘使用分钟数据。
- 历史不完整时显示真实的“已记录（不完整）”流量小计，不使用机器累计量补算，不虚构完整周期百分比或剩余额度；可靠新周期自动恢复完整统计。
- 缓存已闭合历史，保留实时刷新、逐节点时区／重置时间、上传／下载／双向计费口径和其他功能。

## 安装与后端要求

Komari Server 1.6.1 后台主题管理仅上传本页的 **komari-theme-Atlas-build-*.zip**。包内仅有 komari-theme.json、preview.png、dist/；GitHub 自动 Source code 不是主题安装包。

主题 ZIP 不会修改后端指标保留策略。四个流量指标 traffic.up、traffic.down、net.total.up、net.total.down 应保留至少 **36 天**；分钟／五分钟／小时聚合层建议为 **48000 分钟／49000 分钟／840 小时**。仅设置小时层期限不能覆盖指标默认的 1 天限制，已删除的历史无法补回。操作说明见[独立流量周期](https://github.com/MagnetOscar/Atlas/blob/atlas-v0.0.10/docs/traffic-cycles.md)。

本版运行时代码与已验收的 PR28 修复构建一致，仅更新版本及发行材料；复用此前 444 项单元、266 项浏览器检查和原生验收结果，本次未追加功能测试或备份。已安装 PR28 修复构建的部署无需为同一修复重复安装。

[完整差异](https://github.com/MagnetOscar/Atlas/compare/atlas-v0.0.9...atlas-v0.0.10) · [验收来源](https://github.com/MagnetOscar/Atlas/blob/atlas-v0.0.10/docs/verification/review-0.0.10.json) · [可选回程组件（单独下载）](https://github.com/MagnetOscar/Atlas/releases/tag/atlas-components)
