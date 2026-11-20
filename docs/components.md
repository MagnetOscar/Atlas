# Atlas 可选回程组件

主题本身无需安装以下组件。自动回程需要 **Komari 原生插件 + 每个被测节点的附件**；主题只读取结果。组件不能上传到主题管理。

[独立组件下载页](https://github.com/MagnetOscar/Atlas/releases/tag/atlas-components)收纳现有发行文件，**不发布新组件版本**。文件名、版本、SHA256、源码和许可不变。

## 当前组件 0.4.0

适用于 Atlas 0.0.4–0.0.10、Komari Server 1.6.1。plugin ZIP 上传至插件管理，TcpQuality tar.gz 作为 Komari Agent 附件；按[适配说明](tcpquality-adaptation.md)及[附件 README](../companion/tcpquality/README.md)配置。

节点需 Linux、Python >=3.12 和工具权限。复用既有调度与鉴权，无新增常驻服务。rootfs 由准备阶段按固定摘要获取；仅安装主题不会安装组件，IPv6 不通时如实标记不可用。

- [atlas-komari-tcpquality-0.4.0.tar.gz](https://github.com/MagnetOscar/Atlas/releases/download/atlas-components/atlas-komari-tcpquality-0.4.0.tar.gz)
  SHA256：`2d1877758dff4833063ff85ce8f05c90becbd25d46d8b4f07f19ec493cee4817`
- [atlas-route-plugin-0.4.0.zip](https://github.com/MagnetOscar/Atlas/releases/download/atlas-components/atlas-route-plugin-0.4.0.zip)
  SHA256：`3cd2fceee4f7436c371fe0fbf221024c12cd1564de7764741a2a0fe15d908ef2`
- [atlas-tcpquality-installation-0.4.0.md](https://github.com/MagnetOscar/Atlas/releases/download/atlas-components/atlas-tcpquality-installation-0.4.0.md)
  SHA256：`f4507b7f22e9ec45fbe62a2960f6b4be565b610bf71e67ab3fe9c4813b33aec2`

## 历史组件 0.3.1

仅供 Atlas 0.0.3 历史安装／回滚，不与 0.4.0 的采集策略混装。

- [atlas-route-helper-0.3.1.zip](https://github.com/MagnetOscar/Atlas/releases/download/atlas-components/atlas-route-helper-0.3.1.zip)
  SHA256：`0160af6c914962e2e0dd05e19d727f7aafe5b6a1122e68a0d087c9041714f26b`
- [atlas-route-plugin-0.3.1.zip](https://github.com/MagnetOscar/Atlas/releases/download/atlas-components/atlas-route-plugin-0.3.1.zip)
  SHA256：`084c7f68b3bf5c6c18b2934ef609b1ab6ddf30c3a32f94970531119a4da64939`

## 许可与升级

MIT 主题／适配器和上游 TcpQuality GPL-3.0-only 源码分别保留许可，没有将第三方程序改称 Atlas 原创。[第三方声明](../THIRD_PARTY.md)

更新前保留匹配的配置与代码。回滚先停用对应调度及节点策略，不删除 Agent 凭据或历史；只使用主题时无需安装组件。
