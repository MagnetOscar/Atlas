# Atlas 发布约定

## 版本与来源

唯一维护仓库为 MagnetOscar/Atlas，分支 personal/main；上游只读，基线和贡献历史保留。komari-theme.json.version 是唯一软件版本来源，主题标题为 Atlas v<version>，标签为 atlas-v<version>。文档整理不增加版本，不移动旧软件标签或替换主题 ZIP。

## 开发与检查

- 未完成工作保持 Draft PR，按最终改动预检后转 Ready；后续改动先退回 Draft。
- 保留 lint-and-build、screenshots 和分支保护、真实失败通知，不弱化断言。
- 纯文档检查范围、链接、格式，不重复本地功能／浏览器／原生测试；既有强制 CI 仍运行。
- 功能／UI 变更执行完整受影响套件、类型和生产构建。Linux fixture 使用 Linux 验证；UI 遵守[契约流程](ui-contract-sop.md)。
- 工作流调整检查 YAML 与改动的 shell／附件契约，不为展示调整创建测试 Release。

## 原生主题 ZIP

安装包为 komari-theme-Atlas-build-<short-sha>.zip，来自已提交、干净的 production 构建，顶层仅为：

    komari-theme.json
    preview.png
    dist/

预览来源仍为 docs/preview.png；许可证保存在 dist/licenses/。不能加入插件、TQ、rootfs、安装脚本、凭据或私有配置。

## Release 页面

- **主题 Release 只手动上传一个主题 ZIP。** SHA256、源码、对比和兼容性写入说明，JSON 验证资料链接至仓库／CI。
- GitHub 自动 Source code ZIP／tar.gz 为平台链接，不能作为主题安装包，也不承诺隐藏。
- 插件、Helper、TcpQuality 在[独立组件页](components.md)提供，保留其版本、源码和字节。
- 2026-11-19 用户明确授权整理六个主题 Release：保留原主题 ZIP，校验信息移入说明，JSON／TXT 移出附件展示，组件在替代链接可用后迁移。此项不发布新软件版本。
- 历史下载／SHA256 见 [downloads.md](downloads.md)，代码和包记录见 [verification/releases.json](verification/releases.json)。

自动发布工作流直接只上传主题 ZIP，并把 SHA256、源码与构建验证链接写进 Release 说明；插件链接到独立组件页，不再需要发布后清理。JSON 和校验文件仅留在 CI 验证产物中，实际下载 ZIP 后继续核对 SHA256。`scripts/tidy-theme-release.mjs` 仅保留为历史附件整理工具，正常发版无需运行。既有检查、权限与手动触发方式不变。

## 正式发版与验收

正式发版仍需明确版本授权、源码范围验收、必要的原生安装／设置／升级／回滚验证和受控 CI 生产构建；本规范不授权发版或部署。记录实际检查与环境缺口，不把旧结果当作本次验证。

安装包来源、结构和实际下载校验保留；验证记录无需全部展示为附件。正式发布仅手动触发，文档提交不自动发版。生产操作另行授权，生产证据和凭据不公开。

来源见 [FORK](../FORK.md)、[LICENSE](../LICENSE)、[THIRD_PARTY](../THIRD_PARTY.md)；历史规则保留在[整理前源码](https://github.com/MagnetOscar/Atlas/blob/e0039b2f323114977fc1e94de054bd90f4f3e3b7/docs/releasing.md)。
